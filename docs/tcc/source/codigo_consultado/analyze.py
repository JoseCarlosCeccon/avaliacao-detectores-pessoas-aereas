"""Paired, architecture-independent comparison on reserved test and controlled images."""
import collections,csv,functools,json,sys
from pathlib import Path
import faster_core as c
from common_ap import coco_ap
sys.path.insert(0,str(c.YOLO))
import executar_testes_tcc as b

MODELS=['YOLO_original','YOLO_ajustado','FRCNN_pretreinado','FRCNN_ajustado']

def cache_dir(model,cohort):
    if model.startswith('FRCNN'):
        return c.BASE/'Resultados'/('pretreinado' if model.endswith('pretreinado') else 'ajustado')/cohort
    if cohort=='controlled':return c.WORK/'Experimento_Controlado_TCC/Resultados'/('original' if model.endswith('original') else 'treinado')
    return c.YOLO/('resultados_yolo11s_1280' if model.endswith('original') else 'Treinamento_TCC_YOLO11s/resultados_1280')

def add_people(records):
    lookup={(r['scenario'],r['image_id']):r for r in records}
    for r in records:r['people']=[]
    for name in sorted({r['scenario'] for r in records}):
        folder=c.CONTROLLED if name=='Urban_Controlled_Angle_Distance' else c.SOURCE/name
        with (folder/'Metadata/person_geometry.csv').open(encoding='utf-8-sig',newline='') as f:
            for p in csv.DictReader(f):
                key=str(p.get('image_id') or p['capture_id']).zfill(6)
                if (name,key) in lookup:lookup[(name,key)]['people'].append(p)

@functools.lru_cache(maxsize=None)
def validated_config(model,cohort):
    folder=cache_dir(model,cohort);config=json.loads((folder/'protocolo.json').read_text(encoding='utf-8'))
    expected=c.YOLO/('pesos/yolo11s.pt' if model=='YOLO_original' else 'Treinamento_TCC_YOLO11s/runs/ajuste_inicial/weights/best.pt') if model.startswith('YOLO') else c.official_weight() if model=='FRCNN_pretreinado' else c.BASE/'pesos/best.pth'
    if config['weights_sha256']!=c.sha(expected):raise ValueError('Model weight hash changed')
    if model.startswith('YOLO'):
        for key,value in {'imgsz':1280,'batch':1,'max_det':300,'matching_iou':.5}.items():
            if config[key]!=value:raise ValueError('YOLO comparison config differs')
        conf=config.get('operating_confidence',config.get('conf_operating'))
        nms=config.get('nms_iou');floor=config.get('prediction_confidence',config.get('conf_stored'))
        if conf!=.25 or nms!=.7 or floor!=.001:raise ValueError('YOLO operating point differs')
    else:
        if not (folder/'concluido.json').exists():raise ValueError('FRCNN incomplete')
        for key,value in {'score_floor':.001,'operating_confidence':.25,'matching_iou':.5,'max_person_detections':300}.items():
            if config[key]!=value:raise ValueError('FRCNN operating point differs')
    if cohort=='controlled':
        metadata={'Urban_Controlled_Angle_Distance':c.CONTROLLED}
    else:metadata={name:c.SOURCE/name for name in b.SCENARIOS}
    for name,source in metadata.items():
        cap=c.sha(source/'Metadata/capture_metadata.csv');geom=c.sha(source/'Metadata/person_geometry.csv')
        if model.startswith('FRCNN'):
            if config['metadata'][name]!={'captures':cap,'geometry':geom}:raise ValueError('FRCNN metadata changed')
        elif cohort=='controlled':
            if config['capture_metadata_sha256']!=cap or config['person_geometry_sha256']!=geom:raise ValueError('Controlled metadata changed')
        else:
            if config['inputs'][name]['captures_sha256']!=cap or config['inputs'][name]['geometry_sha256']!=geom:raise ValueError('YOLO metadata changed')
    return folder,config

def load_cache(model,cohort,r):
    folder,config=validated_config(model,cohort)
    path=folder/'predicoes'/r['scenario']/(r['image_id']+'.json')
    cache=json.loads(path.read_text(encoding='utf-8'));source=Path(r['image']);stat=source.stat()
    stamp={'size':stat.st_size,'mtime_ns':stat.st_mtime_ns,'registered_sha256':r['image_sha256']}
    if cache['source_stamp']!=stamp or cache['image_id']!=r['image_id'] or cache['scenario']!=r['scenario']:
        raise ValueError('Source/cached identity changed')
    if any(p['class_id']!=0 for p in cache['predictions']):raise ValueError('Non-person exported')
    return cache

def write_csv(path,rows):
    if not rows:return
    path.parent.mkdir(parents=True,exist_ok=True)
    fields=list(dict.fromkeys(k for r in rows for k in r))
    with path.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)

def analyze(cohort):
    records,hashes=c.load_records(controlled=cohort=='controlled')
    if cohort=='test':records=[r for r in records if r['split']=='test']
    add_people(records);expected=6310 if cohort=='test' else 375
    if sum(len(r['boxes']) for r in records)!=expected:raise ValueError('Eligibility count changed')
    totals=collections.defaultdict(lambda:[0,0,0]);groups=collections.defaultdict(lambda:[0,0,0]);personrows=[];imagerows=[];predrows=[]
    caches={};cohort_summary={};ap={};paired=collections.Counter()
    for model in MODELS:
        predictions=[]
        for r in records:
            record=load_cache(model,cohort,r);pred=record['predictions'];predictions.append(pred);caches[(model,r['scenario'],r['image_id'])]=record
            people=[p for p in r['people'] if b.truth(p['annotatable'])]
            gt=[b.ground_box(p) for p in people];matches,fp=b.match_predictions(gt,pred,.25,.5)
            counts=[len(matches),len(fp),len(gt)-len(matches)]
            totals[model]=[x+y for x,y in zip(totals[model],counts)]
            for key in [(model,r['scenario'],'ALL'),(model,r['scenario'],r['angle'])]:
                groups[key]=[x+y for x,y in zip(groups[key],counts)]
            imagerows.append({'cohort':cohort,'model':model,'scenario':r['scenario'],'image_id':r['image_id'],
                'angle':r['angle'],'height_agl_m':r['height_agl_m'],'nominal_distance_m':r['distance_nominal_m'],
                'eligible_people':len(gt),**b.metrics(*counts),'inference_seconds':record['prediction_seconds'],
                'proposals':len(pred),'reached_cap':len(pred)==300})
            for gi,p in enumerate(people):
                hit=gi in matches;pi=matches[gi][0] if hit else None
                personrows.append({'cohort':cohort,'model':model,'scenario':r['scenario'],'image_id':r['image_id'],
                    'person_id':p['person_id'],'status':'TP' if hit else 'FN','angle':r['angle'],
                    'distance_camera_person_m':p['distance_camera_person_m'],'distance_class':p['distance_class'],
                    'nominal_distance_m':r['distance_nominal_m'],'occlusion_fraction_in_frame':p['occlusion_fraction_in_frame'],
                    'bbox_height_px':p['bbox_height_px'],'confidence':pred[pi]['confidence'] if hit else None,
                    'matching_iou':matches[gi][1] if hit else None})
            matched={pi:people[gi]['person_id'] for gi,(pi,ov) in matches.items()}
            for pi,p in enumerate(pred):
                if p['confidence']<.25:continue
                predrows.append({'cohort':cohort,'model':model,'scenario':r['scenario'],'image_id':r['image_id'],
                    'prediction_index':pi,'confidence':p['confidence'],'x1':p['xyxy'][0],'y1':p['xyxy'][1],
                    'x2':p['xyxy'][2],'y2':p['xyxy'][3],'status':'TP' if pi in matched else 'FP',
                    'matched_person_id':matched.get(pi)})
        cohort_summary[model]=b.metrics(*totals[model]);ap[model]=coco_ap([r['boxes'] for r in records],predictions)
        if totals[model][0]+totals[model][2]!=expected:raise ValueError('TP+FN mismatch')
    if cohort=='test':
        old=json.loads((c.YOLO/'Treinamento_TCC_YOLO11s/comparacao/resumo_comparacao.json').read_text(encoding='utf-8'))
        for name,alias in [('YOLO_original','original'),('YOLO_ajustado','treinado')]:
            if cohort_summary[name]!=old['primary_test'][alias]:raise ValueError('YOLO test result not reproduced')
    else:
        old=json.loads((c.WORK/'Experimento_Controlado_TCC/Analise/resumo.json').read_text(encoding='utf-8'))
        for name,alias in [('YOLO_original','original'),('YOLO_ajustado','treinado')]:
            if any(cohort_summary[name][k]!=old['model_summary'][alias][k] for k in cohort_summary[name]):raise ValueError('Controlled YOLO not reproduced')
    out=c.BASE/'Analise'/cohort;out.mkdir(parents=True,exist_ok=True)
    summaryrows=[{'model':m,'images':len(records),'eligible_people':expected,**cohort_summary[m],**{k:ap[m][k] for k in ['map50','map50_95']}} for m in MODELS]
    group_rows=[{'model':m,'scenario':s,'angle':a,**b.metrics(*n)} for (m,s,a),n in groups.items()]
    distance=collections.defaultdict(lambda:[0,0]);controlled=collections.defaultdict(lambda:[0,0,0])
    for p in personrows:
        key=(p['model'],p['scenario'],p['angle'],p['distance_class']);distance[key][0]+=1;distance[key][1]+=p['status']=='TP'
    for im in imagerows:
        if cohort=='controlled':
            key=(im['model'],int(im['nominal_distance_m']),im['angle']);controlled[key]=[x+im[k] for x,k in zip(controlled[key],['tp','fp','fn'])]
    write_csv(out/'resumo_modelos.csv',summaryrows);write_csv(out/'cenario_angulo.csv',group_rows)
    write_csv(out/'pessoas_comparacao.csv',personrows);write_csv(out/'imagens_comparacao.csv',imagerows);write_csv(out/'predicoes_operacionais.csv',predrows)
    write_csv(out/'angulo_distancia.csv',[{'model':m,'scenario':s,'angle':a,'distance_class':d,'n':n,'tp':tp,'fn':n-tp,'recall':tp/n} for (m,s,a,d),(n,tp) in distance.items()])
    write_csv(out/'controlado_celulas.csv',[{'model':m,'distance_m':d,'angle':a,**b.metrics(*n)} for (m,d,a),n in controlled.items()])
    summary={'status':'COMPLETE','cohort':cohort,'images':len(records),'eligible_observations':expected,
       'operating_point':{'confidence':.25,'matching_iou':.5,'max_dets':300},'models':cohort_summary,'common_coco_ap':ap,
       'metadata':hashes,'previous_yolo_reproduced':True,'validation_or_training_is_not_primary':True}
    c.write_json(out/'resumo.json',summary);make_plots(out,group_rows,controlled,personrows,records,caches);return summary

def make_plots(out,groups,controlled,people,records,caches):
    import matplotlib;matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    from PIL import Image,ImageDraw,ImageFont
    figures=out/'Figuras';figures.mkdir(exist_ok=True)
    colors=['#607d8b','#e89520','#2f6db2','#009b85']
    for scenario in sorted({r['scenario'] for r in records}):
        fig,ax=plt.subplots(figsize=(8.5,4.8),layout='constrained')
        for model,color in zip(MODELS,colors):
            rows=sorted([r for r in groups if r['model']==model and r['scenario']==scenario and r['angle']!='ALL'],key=lambda r:r['angle'])
            ax.plot([r['angle'] for r in rows],[100*r['recall'] if r['recall'] is not None else np.nan for r in rows],'o-',label=model,color=color)
        ax.set(title=scenario,xlabel='Off-nadir (graus)',ylabel='Recall (%)',xticks=[0,15,30,45,60],ylim=(-3,103));ax.legend(fontsize=8);ax.grid(alpha=.2)
        fig.savefig(figures/(scenario+'_angulo.png'),dpi=170);plt.close(fig)
    if controlled:
        for distance in [10,20,40]:
            fig,ax=plt.subplots(figsize=(8.5,4.8),layout='constrained')
            for model,color in zip(MODELS,colors):
                n=[controlled[(model,distance,a)] for a in [0,15,30,45,60]]
                ax.plot([0,15,30,45,60],[100*x[0]/(x[0]+x[2]) for x in n],'o-',label=model,color=color)
            ax.set(title=f'Distância 3D à pelve: {distance} m',xlabel='Off-nadir (graus)',ylabel='Recall (%)',xticks=[0,15,30,45,60],ylim=(-3,103));ax.legend(fontsize=8);ax.grid(alpha=.2)
            fig.savefig(figures/f'controlado_{distance}m.png',dpi=170);plt.close(fig)
    examples=out/'Exemplos';examples.mkdir(exist_ok=True)
    try:font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',20)
    except OSError:font=ImageFont.load_default()
    for scenario in sorted({r['scenario'] for r in records}):
        for angle in [0,60]:
            candidates=[r for r in records if r['scenario']==scenario and r['angle']==angle and r['boxes']]
            if not candidates:continue
            r=candidates[0];canvas=Image.new('RGB',(1400,860),'white')
            for index,model in enumerate(MODELS):
                with Image.open(r['image']) as original:im=original.convert('RGB')
                draw=ImageDraw.Draw(im)
                for box in r['boxes']:draw.rectangle(box,outline='#00ee55',width=3)
                for p in caches[(model,scenario,r['image_id'])]['predictions']:
                    if p['confidence']>=.25:draw.rectangle(p['xyxy'],outline='#248bff',width=3)
                im.thumbnail((700,394));x=(index%2)*700;y=(index//2)*430
                canvas.paste(im,(x,y+36));ImageDraw.Draw(canvas).text((x+10,y+5),model+' | '+str(angle)+' graus',fill='black',font=font)
            canvas.save(examples/(scenario+'_'+str(angle)+'.jpg'),quality=92)

if __name__=='__main__':
    summaries=[analyze(x) for x in ['test','controlled']]
    c.write_json(c.BASE/'Analise/resumo_final.json',{'status':'COMPLETE','cohorts':summaries})
