"""Evaluate existing TCC captures. Source images, CSVs and Unreal maps are read-only."""
from __future__ import annotations
import argparse, csv, hashlib, json, math, platform, sys, time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent
DEFAULT_DATA = Path(r'C:\Users\pedro\Documents\Codex\2026-09-30\no-cen\outputs\Dataset')
SCENARIOS = ['Urban_Centered_1m', 'Urban_Spread', 'Forest_Centered_50', 'Forest_Spread', 'Forest_Low_Altitude']
ANGLES = [0, 15, 30, 45, 60]
BANDS = ['D01', 'D02', 'D03', 'D04', 'D05']
BAND_NAMES = ['[0,10) m', '[10,20) m', '[20,30) m', '[30,50] m', '>50 m']

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def csv_rows(path):
    with Path(path).open(encoding='utf-8-sig', newline='') as f: return list(csv.DictReader(f))
def truth(value):
    v = str(value).strip().lower()
    if v not in {'true', 'false', '1', '0'}: raise ValueError(f'Booleano inválido: {value!r}')
    return v in {'true', '1'}
def number(value):
    v = float(value)
    if not math.isfinite(v): raise ValueError(f'Número não finito: {value!r}')
    return v
def image_id(row): return str(row.get('image_id') or row['capture_id']).zfill(6)
def distance_band(d):
    if d < 0: raise ValueError('Distância negativa')
    return 'D01' if d < 10 else 'D02' if d < 20 else 'D03' if d < 30 else 'D04' if d <= 50 else 'D05'
def ground_box(row):
    x, y, w, h = [number(row[k]) for k in ['bbox_x', 'bbox_y', 'bbox_width_px', 'bbox_height_px']]
    if w <= 0 or h <= 0: raise ValueError('Pessoa anotável sem caixa válida')
    # Dataset widths include both endpoint pixels; continuous rectangle edges are x and x+w.
    return [x, y, x+w, y+h]
def iou(a, b):
    ix = max(0., min(a[2], b[2])-max(a[0], b[0]))
    iy = max(0., min(a[3], b[3])-max(a[1], b[1]))
    intersection = ix*iy
    aa = max(0., a[2]-a[0])*max(0., a[3]-a[1])
    bb = max(0., b[2]-b[0])*max(0., b[3]-b[1])
    union = aa+bb-intersection
    return intersection/union if union > 0 else 0.
def match_predictions(gt_boxes, predictions, conf=.25, threshold=.5):
    """Score-ordered greedy one-to-one matching, using best available IoU per detection."""
    eligible = [i for i,p in enumerate(predictions) if int(p['class_id']) == 0 and number(p['confidence']) >= conf]
    ordered = sorted(eligible, key=lambda i:(-number(predictions[i]['confidence']), i))
    available = set(range(len(gt_boxes))); matches = {}; used = set()
    for pi in ordered:
        if not available: break
        gi = max(sorted(available), key=lambda j:iou(gt_boxes[j], predictions[pi]['xyxy']))
        overlap = iou(gt_boxes[gi], predictions[pi]['xyxy'])
        if overlap >= threshold:
            matches[gi] = (pi, overlap); available.remove(gi); used.add(pi)
    return matches, [i for i in eligible if i not in used]
def ratio(n, d): return n/d if d else None
def metrics(tp, fp, fn):
    return {'tp':tp, 'fp':fp, 'fn':fn, 'precision':ratio(tp,tp+fp), 'recall':ratio(tp,tp+fn),
            'f1':ratio(2*tp,2*tp+fp+fn)}
def json_write(path, data):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix+'.tmp')
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')
    temp.replace(path)
def save_csv(path, fields, rows):
    with Path(path).open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields); writer.writeheader(); writer.writerows(rows)

def load_data(root, names):
    datasets = {}; audit = []
    for name in names:
        folder = root/name
        captures_path = folder/'Metadata/capture_metadata.csv'
        geometry_path = folder/'Metadata/person_geometry.csv'
        captures = csv_rows(captures_path); geometry = csv_rows(geometry_path)
        cameras = {}; by_image = defaultdict(list); seen_people = set(); annotation_count = 0
        for r in captures:
            key = image_id(r)
            if key in cameras: raise ValueError(f'{name}: imagem duplicada {key}')
            img = (folder/r['image_file']).resolve()
            if not img.is_relative_to(folder.resolve()) or not img.is_file():
                raise ValueError(f'{name}: caminho de imagem inválido: {img}')
            if img.stem != key: raise ValueError(f'{name}: ID não corresponde ao PNG {key}')
            for k in ['off_nadir_angle_deg','camera_height_agl_m','width_px','height_px']: number(r[k])
            if round(number(r['off_nadir_angle_deg'])) not in ANGLES: raise ValueError('Ângulo inesperado')
            cameras[key] = r
        for r in geometry:
            key = image_id(r); unique = (key,r['person_id'])
            if key not in cameras or unique in seen_people: raise ValueError(f'{name}: relação inválida {unique}')
            seen_people.add(unique)
            if r['scenario_id'] != cameras[key]['scenario_id']: raise ValueError('Cenário divergente')
            d = number(r['distance_camera_person_m'])
            if distance_band(d) != r['distance_class']: raise ValueError('Faixa de distância divergente')
            if abs(number(r['off_nadir_angle_deg'])-number(cameras[key]['off_nadir_angle_deg'])) > .0001:
                raise ValueError('Ângulo de pessoa divergente da câmera')
            if truth(r['annotatable']):
                box = ground_box(r); annotation_count += 1
                if not (0 <= box[0] < box[2] <= number(cameras[key]['width_px']) and
                        0 <= box[1] < box[3] <= number(cameras[key]['height_px'])):
                    raise ValueError(f'{name}: caixa fora do quadro {unique}')
                if number(r['visible_pixel_count']) <= 0: raise ValueError('Anotável sem pixels visíveis')
            by_image[key].append(r)
        if set(by_image) != set(cameras): raise ValueError(f'{name}: imagem sem registros de geometria')
        if len(list((folder/'Images').glob('*.png'))) != len(cameras): raise ValueError(f'{name}: contagem de PNG divergente')
        for key,r in cameras.items():
            if 'annotatable_person_count' in r and int(r['annotatable_person_count']) != sum(truth(x['annotatable']) for x in by_image[key]):
                raise ValueError(f'{name}: contagem anotável divergente {key}')
        datasets[name] = {'folder':folder, 'cameras':cameras, 'people':by_image,
                          'captures_sha256':sha(captures_path), 'geometry_sha256':sha(geometry_path)}
        audit.append({'scenario':name, 'images':len(cameras), 'person_relations':len(geometry),
                      'annotatable':annotation_count, 'excluded':len(geometry)-annotation_count})
    return datasets, audit

def cache_path(out, name, key): return out/'predicoes'/name/(key+'.json')
def source_stamp(data, key):
    r = data['cameras'][key]; path = data['folder']/r['image_file']; s = path.stat()
    return {'size':s.st_size, 'mtime_ns':s.st_mtime_ns, 'registered_sha256':r['image_sha256']}
def cached_result(out, name, key, data):
    p = cache_path(out,name,key)
    if not p.exists(): return None
    result = json.loads(p.read_text(encoding='utf-8'))
    if result.get('source_stamp') != source_stamp(data,key): raise ValueError(f'Imagem alterada após captura: {p}')
    if result.get('image_id') != key or result.get('scenario') != name: raise ValueError('Cache com identificação inválida')
    return result
def pilot_keys(data, count):
    groups = defaultdict(list)
    for key,r in data['cameras'].items(): groups[round(number(r['off_nadir_angle_deg']))].append(key)
    picked = []
    per_angle = max(1,count//5)
    for a in ANGLES:
        keys = sorted(groups[a],key=lambda k:(number(data['cameras'][k]['camera_height_agl_m']),k))
        if not keys: continue
        n = min(per_angle,len(keys))
        indices = [round(i*(len(keys)-1)/(n-1)) for i in range(n)] if n > 1 else [0]
        picked.extend(keys[i] for i in indices)
    return sorted(set(picked))
def protocol(args, datasets, torch, ultralytics, weight):
    return {'format_version':1, 'model':args.modelo, 'weights_sha256':sha(weight), 'imgsz':args.imgsz,
            'device':'cpu', 'batch':1, 'rect':True, 'class_id':0, 'class_name':'person',
            'prediction_confidence':.001, 'operating_confidence':.25, 'nms_iou':.7,
            'matching_iou':.5, 'max_det':300, 'augment':False, 'torch_threads':8,
            'python':platform.python_version(), 'platform':platform.platform(),
            'torch_version':str(torch.__version__), 'ultralytics_version':ultralytics.__version__,
            'script_sha256':sha(__file__), 'data_root':str(args.dados.resolve()),
            'inputs':{n:{'captures_sha256':d['captures_sha256'], 'geometry_sha256':d['geometry_sha256'],
                         'image_count':len(d['cameras'])} for n,d in datasets.items()}}

def run_inference(args, datasets, audit):
    import torch, ultralytics
    from ultralytics import YOLO
    out = args.saida.resolve(); out.mkdir(parents=True,exist_ok=True)
    torch.set_num_threads(8)
    weights_dir = BASE/'pesos'; weights_dir.mkdir(exist_ok=True)
    model_path = weights_dir/args.modelo
    model = YOLO(str(model_path))  # Official named weights; library downloads if absent.
    if model.names.get(0) != 'person' or model.task != 'detect': raise ValueError('Modelo não é detector COCO/person')
    settings = protocol(args,datasets,torch,ultralytics,model_path)
    config_path = out/'protocolo.json'
    if config_path.exists():
        if json.loads(config_path.read_text(encoding='utf-8')) != settings:
            raise ValueError('Protocolo diferente. Use uma nova pasta --saida para outra resolução/modelo/configuração.')
    else: json_write(config_path,settings)
    json_write(out/'auditoria_entrada.json',audit)
    first = next(iter(datasets.values())); first_key = sorted(first['cameras'])[0]
    model.predict(str(first['folder']/first['cameras'][first_key]['image_file']),imgsz=args.imgsz,
                  device='cpu',batch=1,rect=True,classes=[0],conf=.001,iou=.7,max_det=300,
                  augment=False,verbose=False,save=False)  # warmup, excluded from timing
    timings = []; fresh = 0; reused = 0
    total_selected = sum(len(pilot_keys(d,args.piloto_por_cenario)) if args.modo=='piloto' else len(d['cameras']) for d in datasets.values())
    for name,data in datasets.items():
        keys = pilot_keys(data,args.piloto_por_cenario) if args.modo=='piloto' else sorted(data['cameras'])
        for key in keys:
            if cached_result(out,name,key,data) is not None:
                reused += 1; continue
            row = data['cameras'][key]; path = data['folder']/row['image_file']
            if sha(path) != row['image_sha256']: raise ValueError(f'Checksum divergente: {path}')
            stamp = source_stamp(data,key); start = time.perf_counter()
            result = model.predict(str(path),imgsz=args.imgsz,device='cpu',batch=1,rect=True,
                                   classes=[0],conf=.001,iou=.7,max_det=300,augment=False,
                                   verbose=False,save=False)[0]
            elapsed = time.perf_counter()-start
            if list(result.orig_shape) != [int(row['height_px']),int(row['width_px'])]: raise ValueError('Resolução divergente')
            predictions = [{'xyxy':[float(v) for v in box], 'confidence':float(score), 'class_id':int(cls)}
                           for box,score,cls in zip(result.boxes.xyxy.cpu().tolist(),result.boxes.conf.cpu().tolist(),result.boxes.cls.cpu().tolist())]
            record = {'scenario':name, 'image_id':key, 'source_stamp':stamp,
                      'image_sha256_verified':True, 'prediction_seconds':elapsed,
                      'speed_ms':result.speed, 'predictions':predictions,
                      'timestamp_utc':datetime.now(timezone.utc).isoformat()}
            json_write(cache_path(out,name,key),record); timings.append(elapsed); fresh += 1
            if args.modo=='piloto':
                preview = result.new()
                preview.update(boxes=result.boxes.data[result.boxes.conf >= .25])
                preview_dir = out/'previews_piloto'/name; preview_dir.mkdir(parents=True,exist_ok=True)
                preview.save(str(preview_dir/(key+'.jpg')))
            if (fresh+reused)%10 == 0: print(f'{fresh+reused}/{total_selected}: {name}/{key}',flush=True)
    if args.modo=='piloto':
        records = [cached_result(out,n,k,d) for n,d in datasets.items() for k in pilot_keys(d,args.piloto_por_cenario)]
        mean = sum(r['prediction_seconds'] for r in records)/len(records)
        estimate = {'pilot_images':len(records), 'mean_prediction_seconds':mean,
                    'dataset_images':sum(len(d['cameras']) for d in datasets.values()),
                    'estimated_inference_hours':mean*sum(len(d['cameras']) for d in datasets.values())/3600,
                    'meaning':'Estimativa de inferência, sem instalação/download, análise e revisão. Não é garantia de prazo.'}
        json_write(out/'estimativa_piloto.json',estimate)
        print(json.dumps(estimate,ensure_ascii=False,indent=2))
    else: analyze(out,datasets)

def analyze(out, datasets):
    config = json.loads((out/'protocolo.json').read_text(encoding='utf-8'))
    for name,data in datasets.items():
        baseline = config['inputs'][name]
        if data['captures_sha256'] != baseline['captures_sha256'] or data['geometry_sha256'] != baseline['geometry_sha256']:
            raise ValueError('Metadados alterados depois de fixar o protocolo')
    records = {}; missing = []
    for name,data in datasets.items():
        for key in sorted(data['cameras']):
            record = cached_result(out,name,key,data)
            if record is None: missing.append(f'{name}/{key}')
            else: records[(name,key)] = record
    if missing: raise ValueError(f'Análise final bloqueada: faltam {len(missing)} imagens. Rode --modo completo. Primeira: {missing[0]}')
    tables = out/'tabelas'; tables.mkdir(parents=True,exist_ok=True)
    cells = defaultdict(lambda:[0,0]); angle_totals = defaultdict(lambda:[0,0,0]); scenario_totals = defaultdict(lambda:[0,0,0])
    image_rows = []; prediction_rows = []; excluded = 0; expected_annotatable = 0
    person_fields = ['scenario','image_id','person_id','annotatable','visibility_status','off_nadir_angle_deg',
                     'distance_camera_person_m','distance_class','bbox_width_px','bbox_height_px',
                     'occlusion_fraction_in_frame','frame_truncated','evaluation_status','prediction_confidence','matching_iou']
    with (tables/'resultados_por_pessoa.csv').open('w',encoding='utf-8-sig',newline='') as f:
        writer = csv.DictWriter(f,fieldnames=person_fields); writer.writeheader()
        for (name,key),record in records.items():
            data = datasets[name]; camera = data['cameras'][key]; persons = data['people'][key]
            eligible_people = [r for r in persons if truth(r['annotatable'])]
            preds = record['predictions']; boxes = [ground_box(r) for r in eligible_people]
            matches, fp_indices = match_predictions(boxes,preds,config['operating_confidence'],config['matching_iou'])
            by_id = {r['person_id']:i for i,r in enumerate(eligible_people)}
            angle = round(number(camera['off_nadir_angle_deg']))
            tp = len(matches); fp = len(fp_indices); fn = len(eligible_people)-tp; expected_annotatable += len(eligible_people)
            for target in [scenario_totals[name],angle_totals[(name,angle)]]:
                target[0] += tp; target[1] += fp; target[2] += fn
            image_rows.append({'scenario':name,'image_id':key,'off_nadir_angle_deg':angle,
                               'camera_height_agl_m':camera['camera_height_agl_m'],'annotatable_people':len(eligible_people),
                               **metrics(tp,fp,fn),'prediction_seconds':record['prediction_seconds']})
            matched_pred = {v[0]:eligible_people[gi]['person_id'] for gi,v in matches.items()}
            for pi,pred in enumerate(preds):
                above = pred['confidence'] >= config['operating_confidence']
                prediction_rows.append({'scenario':name,'image_id':key,'prediction_index':pi,'confidence':pred['confidence'],
                    'x1':pred['xyxy'][0],'y1':pred['xyxy'][1],'x2':pred['xyxy'][2],'y2':pred['xyxy'][3],
                    'status':'TP' if pi in matched_pred else 'FP' if above else 'BELOW_OPERATING_THRESHOLD',
                    'matched_person_id':matched_pred.get(pi,'')})
            for person in persons:
                annotated = truth(person['annotatable']); gi = by_id.get(person['person_id'])
                matched = matches.get(gi) if annotated else None
                row = {k:person.get(k,'') for k in person_fields}
                row.update(scenario=name,image_id=key,annotatable=annotated,
                           evaluation_status='TP' if matched else 'FN' if annotated else 'EXCLUDED',
                           prediction_confidence=preds[matched[0]]['confidence'] if matched else '',
                           matching_iou=matched[1] if matched else '')
                writer.writerow(row)
                if annotated:
                    cell = cells[(name,angle,person['distance_class'])]; cell[0] += 1; cell[1] += bool(matched)
                else: excluded += 1
    image_fields = ['scenario','image_id','off_nadir_angle_deg','camera_height_agl_m','annotatable_people',
                    'tp','fp','fn','precision','recall','f1','prediction_seconds']
    save_csv(tables/'resultados_por_imagem.csv',image_fields,image_rows)
    save_csv(tables/'predicoes.csv',['scenario','image_id','prediction_index','confidence','x1','y1','x2','y2','status','matched_person_id'],prediction_rows)
    summary = [{'scenario':n,**metrics(*scenario_totals[n])} for n in datasets]
    save_csv(tables/'resumo_por_cenario.csv',['scenario','tp','fp','fn','precision','recall','f1'],summary)
    save_csv(tables/'resumo_por_angulo.csv',['scenario','off_nadir_angle_deg','tp','fp','fn','precision','recall','f1'],
             [{'scenario':n,'off_nadir_angle_deg':a,**metrics(*angle_totals[(n,a)])} for n in datasets for a in ANGLES])
    joint_rows = [{'scenario':n,'off_nadir_angle_deg':a,'distance_class':b,'annotatable_people':cells[(n,a,b)][0],
                   'tp':cells[(n,a,b)][1],'fn':cells[(n,a,b)][0]-cells[(n,a,b)][1],
                   'recall':ratio(cells[(n,a,b)][1],cells[(n,a,b)][0])} for n in datasets for a in ANGLES for b in BANDS]
    save_csv(tables/'recall_angulo_distancia.csv',['scenario','off_nadir_angle_deg','distance_class','annotatable_people','tp','fn','recall'],joint_rows)
    all_tp = sum(r['tp'] for r in summary); all_fp = sum(r['fp'] for r in summary); all_fn = sum(r['fn'] for r in summary)
    assert all_tp+all_fn == expected_annotatable
    for n in datasets:
        assert sum(cells[(n,a,b)][0] for a in ANGLES for b in BANDS) == scenario_totals[n][0]+scenario_totals[n][2]
    validation = {'status':'COMPLETE','images_processed':len(records),'person_relations':expected_annotatable+excluded,
                  'annotatable_people':expected_annotatable,'excluded_person_relations':excluded,
                  'all_tp_plus_fn_equals_annotatable':True,'summary_micro':metrics(all_tp,all_fp,all_fn),
                  'warning':'Observações repetidas; não são pessoas independentes. FP não têm distância corporal conhecida. AP/mAP não calculados neste executor.'}
    json_write(out/'validacao_resultados.json',validation)
    make_plots(out,joint_rows,list(datasets))
    (out/'LEIA_RESULTADOS.txt').write_text(
        'Análise descritiva, modelo fixo. Recall principal: TP/(TP+FN), conf >= 0.25 e matching IoU >= 0.50.\n'
        'FP e precisão são calculados por imagem/cenário/ângulo. Não atribuir distância de pessoa a FP.\n'
        'Células sem pessoas anotáveis têm recall vazio (sem dados), não zero. CSV: UTF-8 BOM, separador vírgula, decimal ponto.\n'
        'Resultados reutilizam as mesmas pessoas. Ângulo e distância não são plenamente balanceados; separar cenários e analisar cobertura.\n'
        'Anotações: silhueta visível, caixa com arestas x,y,x+width,y+height. Pessoas não anotáveis são excluídas do denominador.\n'
        'Imagens sem pessoas anotáveis permanecem na avaliação de FP. AP/mAP não são calculados aqui.\n',encoding='utf-8')
    print(json.dumps(validation,ensure_ascii=False,indent=2))

def make_plots(out, rows, names):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    plots = out/'graficos'; plots.mkdir(exist_ok=True)
    for name in names:
        lookup = {(r['off_nadir_angle_deg'],r['distance_class']):r for r in rows if r['scenario']==name}
        values = np.array([[lookup[(a,b)]['recall'] if lookup[(a,b)]['recall'] is not None else np.nan for b in BANDS] for a in ANGLES])
        fig,ax = plt.subplots(figsize=(9,5.6),layout='constrained')
        cmap = plt.get_cmap('YlGnBu').copy(); cmap.set_bad('#e7e7e7')
        im = ax.imshow(values,vmin=0,vmax=1,cmap=cmap,aspect='auto')
        ax.set_xticks(range(5),BAND_NAMES); ax.set_yticks(range(5),[f'{a}°' for a in ANGLES])
        ax.set_xlabel('Distância 3D câmera-pelve'); ax.set_ylabel('Off-nadir da câmera')
        ax.set_title(name+' | Recall a conf >= 0,25; IoU >= 0,50')
        for i,a in enumerate(ANGLES):
            for j,b in enumerate(BANDS):
                r = lookup[(a,b)]; text = 'Sem dados\nn=0' if r['recall'] is None else f"{100*r['recall']:.1f}%\nn={r['annotatable_people']}"
                ax.text(j,i,text,ha='center',va='center',fontsize=9,color='white' if r['recall'] is not None and r['recall']>.6 else '#182d3b')
        fig.colorbar(im,ax=ax,label='Recall'); fig.savefig(plots/(name+'_matriz_recall.png'),dpi=170); plt.close(fig)
        fig,ax = plt.subplots(figsize=(8,4.8),layout='constrained')
        for i,a in enumerate(ANGLES): ax.plot(range(5),values[i],marker='o',label=f'{a}°')
        ax.set_xticks(range(5),BAND_NAMES); ax.set_ylim(-.03,1.03); ax.set_ylabel('Recall'); ax.set_xlabel('Distância 3D câmera-pelve')
        ax.set_title(name+' | Recall por distância e ângulo'); ax.grid(alpha=.25); ax.legend(title='Off-nadir')
        fig.savefig(plots/(name+'_curvas_recall.png'),dpi=170); plt.close(fig)

def main():
    parser = argparse.ArgumentParser(description='Testes de detecção em capturas existentes do TCC')
    parser.add_argument('--modo',choices=['conferir','piloto','completo','analisar'],required=True)
    parser.add_argument('--dados',type=Path,default=DEFAULT_DATA)
    parser.add_argument('--saida',type=Path,default=BASE/'resultados_yolo11s_1280')
    parser.add_argument('--modelo',choices=['yolo11n.pt','yolo11s.pt','yolo11m.pt'],default='yolo11s.pt')
    parser.add_argument('--imgsz',type=int,default=1280)
    parser.add_argument('--piloto-por-cenario',type=int,default=10)
    parser.add_argument('--cenarios',nargs='+',choices=SCENARIOS,default=SCENARIOS)
    args = parser.parse_args()
    if args.imgsz < 32 or args.imgsz%32: parser.error('--imgsz deve ser múltiplo positivo de 32')
    if args.piloto_por_cenario < 5 or args.piloto_por_cenario%5: parser.error('Piloto por cenário deve ser múltiplo de 5')
    datasets,audit = load_data(args.dados.resolve(),args.cenarios)
    print(json.dumps(audit,ensure_ascii=False,indent=2),flush=True)
    if args.modo=='conferir': return
    if args.modo=='analisar': analyze(args.saida.resolve(),datasets)
    else: run_inference(args,datasets,audit)

if __name__=='__main__':
    try: main()
    except Exception as error:
        print(f'ERRO: {error}',file=sys.stderr,flush=True)
        raise
