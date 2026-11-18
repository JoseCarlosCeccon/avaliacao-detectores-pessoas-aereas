"""Shared TorchVision adapter. Source captures and existing YOLO artifacts are read-only."""
import csv, hashlib, json, math, types
from pathlib import Path
import torch
from torchvision.ops import boxes as box_ops
from torchvision.models.detection import fasterrcnn_resnet50_fpn_v2
from torchvision.models.detection.faster_rcnn import FastRCNNPredictor

BASE=Path(__file__).resolve().parent
WORK=BASE.parent
YOLO=WORK/'Testes_TCC_YOLO'
SOURCE=Path('C:/Users/pedro/Documents/Codex/2026-09-30/no-cen/outputs/Dataset')
CONTROLLED=WORK/'Experimento_Controlado_TCC/Dataset/Urban_Controlled_Angle_Distance'
PARTITIONS=YOLO/'Treinamento_TCC_YOLO11s/particoes.csv'
URL='https://download.pytorch.org/models/fasterrcnn_resnet50_fpn_v2_coco-dd69338a.pth'
EXPECTED_PARTITIONS='d41487dc12dfe32445740e1fc228df3bcf712863ee5dd927405bb3ea84c2ac1c'

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()

def write_json(path,data):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_suffix(path.suffix+'.tmp')
    temp.write_text(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
    temp.replace(path)

def read_csv(path):
    with Path(path).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

def make_target(boxes,image_id):
    tensor=torch.as_tensor(boxes,dtype=torch.float32).reshape(-1,4)
    if not torch.isfinite(tensor).all() or (tensor[:,2:]<=tensor[:,:2]).any():
        raise ValueError('Invalid visible-silhouette bounding box')
    return {'boxes':tensor,'labels':torch.ones(len(tensor),dtype=torch.int64),
            'image_id':torch.tensor(image_id,dtype=torch.int64),
            'area':(tensor[:,2]-tensor[:,0])*(tensor[:,3]-tensor[:,1]),
            'iscrowd':torch.zeros(len(tensor),dtype=torch.int64)}

def validate_manifest(rows):
    seen=set();groups={};hashes={}
    for r in rows:
        key=(r['scenario'],r['image_id']);split=r['split']
        if key in seen or split not in {'train','val','test'}:raise ValueError('Invalid/duplicate partition key')
        seen.add(key)
        for store,field in [(groups,'group'),(hashes,'image_sha256')]:
            value=r[field]
            if value in store and store[value]!=split:raise ValueError('Partition leakage: '+field)
            store[value]=split

def select_person_detections(logits,decoded_boxes,image_size,score_thresh,nms_thresh,max_det):
    # Keep the full COCO softmax: dropping other logits before softmax inflates confidence.
    scores=torch.softmax(logits,dim=-1)[:,1]
    boxes=box_ops.clip_boxes_to_image(decoded_boxes[:,1,:],image_size)
    keep=torch.where(scores>score_thresh)[0];boxes,scores=boxes[keep],scores[keep]
    keep=box_ops.remove_small_boxes(boxes,min_size=1e-2);boxes,scores=boxes[keep],scores[keep]
    keep=box_ops.nms(boxes,scores,nms_thresh)[:max_det]
    return {'boxes':boxes[keep],'scores':scores[keep],
            'labels':torch.ones(len(keep),device=logits.device,dtype=torch.int64)}

def person_postprocess(self,class_logits,box_regression,proposals,image_shapes):
    counts=[len(p) for p in proposals]
    decoded=self.box_coder.decode(box_regression,proposals)
    all_boxes=[];all_scores=[];all_labels=[]
    for logits,boxes,size in zip(class_logits.split(counts),decoded.split(counts),image_shapes):
        out=select_person_detections(logits,boxes,size,self.score_thresh,self.nms_thresh,self.detections_per_img)
        all_boxes.append(out['boxes']);all_scores.append(out['scores']);all_labels.append(out['labels'])
    return all_boxes,all_scores,all_labels

def person_predictor(old):
    new=FastRCNNPredictor(old.cls_score.in_features,2)
    with torch.no_grad():
        new.cls_score.weight.copy_(old.cls_score.weight[:2]);new.cls_score.bias.copy_(old.cls_score.bias[:2])
        new.bbox_pred.weight.copy_(old.bbox_pred.weight[:8]);new.bbox_pred.bias.copy_(old.bbox_pred.bias[:8])
    return new

def official_weight():
    folder=BASE/'pesos';folder.mkdir(exist_ok=True)
    path=folder/URL.rsplit('/',1)[1]
    if not path.exists():torch.hub.download_url_to_file(URL,str(path),hash_prefix='dd69338a',progress=True)
    if not sha(path).startswith('dd69338a'):raise ValueError('Official checkpoint hash mismatch')
    return path

def build_model(weight=None,adapt=False,min_size=720,max_size=1280):
    classes=2 if weight and Path(weight).name!='fasterrcnn_resnet50_fpn_v2_coco-dd69338a.pth' else 91
    model=fasterrcnn_resnet50_fpn_v2(weights=None,weights_backbone=None,num_classes=classes,
           min_size=min_size,max_size=max_size,box_score_thresh=.001,box_nms_thresh=.7,
           box_detections_per_img=300,box_batch_size_per_image=256)
    path=Path(weight) if weight else official_weight()
    state=torch.load(path,map_location='cpu',weights_only=True)
    model.load_state_dict(state.get('model',state));del state
    if adapt:model.roi_heads.box_predictor=person_predictor(model.roi_heads.box_predictor)
    model.roi_heads.postprocess_detections=types.MethodType(person_postprocess,model.roi_heads)
    return model

def freeze_feature_extractor(model):
    for p in model.backbone.parameters():p.requires_grad_(False)
    model.backbone.eval()

def prediction_record(out):
    if len(out['labels']) and not torch.all(out['labels']==1):raise ValueError('Non-person returned')
    return [{'xyxy':[float(v) for v in box],'confidence':float(score),'class_id':0}
            for box,score in zip(out['boxes'].tolist(),out['scores'].tolist())]

def image_tensor(path):
    from PIL import Image
    from torchvision.transforms.functional import pil_to_tensor
    with Image.open(path) as im:return pil_to_tensor(im.convert('RGB')).float().div_(255)

def load_records(controlled=False,with_people=False):
    if controlled:
        folders={'Urban_Controlled_Angle_Distance':CONTROLLED};manifest=None
    else:
        if sha(PARTITIONS)!=EXPECTED_PARTITIONS:raise ValueError('Existing partitions altered')
        rows=read_csv(PARTITIONS);validate_manifest(rows)
        manifest={(r['scenario'],r['image_id']):r for r in rows}
        folders={name:SOURCE/name for name in sorted({r['scenario'] for r in rows})}
    records=[];hashes={}
    for name,folder in folders.items():
        cap=folder/'Metadata/capture_metadata.csv';geom=folder/'Metadata/person_geometry.csv'
        hashes[name]={'captures':sha(cap),'geometry':sha(geom)}
        entries={}
        for r in read_csv(cap):
            key=str(r.get('image_id') or r['capture_id']).zfill(6)
            m=manifest[(name,key)] if manifest else None
            path=(folder/r['image_file']).resolve()
            if not path.is_relative_to(folder.resolve()) or not path.is_file():raise ValueError('Missing/outside image')
            if m and r['image_sha256']!=m['image_sha256']:raise ValueError('Capture hash != partition hash')
            entries[key]={'scenario':name,'image_id':key,'split':m['split'] if m else 'controlled',
                'group':m['group'] if m else r['person_id'],'image':str(path),'image_sha256':r['image_sha256'],
                'angle':int(round(float(r['off_nadir_angle_deg']))),'height_agl_m':float(r['camera_height_agl_m']),
                'boxes':[],'width':int(r['width_px']),'height':int(r['height_px']),
                'distance_nominal_m':float(r['nominal_distance_m']) if controlled else None}
            if with_people:entries[key]['people']=[]
        with geom.open(encoding='utf-8-sig',newline='') as f:
            for p in csv.DictReader(f):
                key=str(p.get('image_id') or p['capture_id']).zfill(6);entry=entries[key]
                eligible=p['annotatable'].lower() in ('true','1')
                if eligible:
                    x,y,w,h=[float(p[k]) for k in ('bbox_x','bbox_y','bbox_width_px','bbox_height_px')]
                    box=[x,y,x+w,y+h]
                    if not (0<=x<x+w<=entry['width'] and 0<=y<y+h<=entry['height']):raise ValueError('GT outside image')
                    entry['boxes'].append(box)
                if with_people:entry['people'].append(p)
        if manifest:
            for key,e in entries.items():
                if len(e['boxes'])!=int(manifest[(name,key)]['annotatable_people']):raise ValueError('GT count mismatch')
        records.extend(entries.values())
    return sorted(records,key=lambda r:(r['scenario'],r['image_id'])),hashes
