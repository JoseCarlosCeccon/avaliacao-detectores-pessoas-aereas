"""Regenera figuras documentais, sem executar detectores.

Requisitos: Python 3, matplotlib, numpy e Pillow.
Executar a partir de qualquer pasta: python gerar_figuras_controle.py
Entradas e fontes estão na mesma pasta e em figuras/controle_fontes.
"""
from pathlib import Path
import csv, json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
DOC = ROOT / 'documentacao'
FIG = ROOT / 'figuras'
IMG = FIG / 'controle_fontes'
MODELS = [('YOLO_original', 'YOLO11s COCO', '#315e57', 'o', '-'),
          ('FRCNN_pretreinado', 'Faster R-CNN COCO', '#9a573c', 's', '--')]
DIST = [10, 20, 40]
ANG = [0, 15, 30, 45, 60]
with (DOC / 'controle_originais_conferido.csv').open(encoding='utf-8-sig') as f:
    rows = list(csv.DictReader(f))
assert len(rows) == 30 and {r['model'] for r in rows} == {m[0] for m in MODELS}
for r in rows:
    for k in ['distance_m', 'angle', 'tp', 'fp', 'fn']: r[k] = int(r[k])
    for k in ['precision', 'recall', 'f1']: r[k] = float(r[k]) if r[k] else float('nan')
    assert r['tp'] + r['fn'] == 25
    assert abs(r['recall'] - r['tp']/25) < 1e-10
    assert abs(r['f1'] - 2*r['tp']/(2*r['tp']+r['fp']+r['fn'])) < 1e-10

plt.rcParams.update({'font.family':'DejaVu Sans', 'font.size':10,
    'axes.spines.top':False, 'axes.spines.right':False,
    'axes.labelcolor':'#252525', 'text.color':'#252525',
    'pdf.fonttype':42, 'savefig.facecolor':'white'})
def save(fig, name):
    fig.savefig(FIG / (name+'.pdf'), bbox_inches='tight', pad_inches=.06)
    fig.savefig(FIG / (name+'.png'), dpi=190, bbox_inches='tight', pad_inches=.06)
    plt.close(fig)
def values(model, field):
    return np.array([[next(r[field] for r in rows if r['model']==model
        and r['distance_m']==d and r['angle']==a) for a in ANG] for d in DIST])

# As mesmas cinco posições do ator, com recorte fixo em pixels.
fig, axes = plt.subplots(3, 5, figsize=(7.1, 4.25))
for i, d in enumerate(DIST):
    for j, a in enumerate(ANG):
        n=i*5+j+1; ax=axes[i,j]
        ax.imshow(Image.open(IMG / f'{n:06}_recorte.png'))
        ax.set_xticks([]); ax.set_yticks([])
        for s in ax.spines.values(): s.set_visible(False)
        ax.set_title(f'{a}° · {n:06}', fontsize=8, pad=3)
        if j == 0: ax.set_ylabel(f'{d} m', fontsize=10, labelpad=8)
fig.subplots_adjust(left=.055, right=.995, bottom=.01, top=.95, hspace=.16, wspace=.055)
save(fig, 'controle_serie_15_vistas')

fig, axes = plt.subplots(1, 2, figsize=(7.1, 2.25))
for ax,n,a in zip(axes,[1,5],[0,60]):
    ax.imshow(Image.open(IMG / f'{n:06}_contexto.png')); ax.axis('off')
    ax.set_title(f'10 m · {a}° · {n:06}.png', fontsize=9)
fig.subplots_adjust(left=0, right=1, bottom=0, top=.9, wspace=.035)
save(fig, 'controle_contexto_cena')

# Curvas por distância. O ponto é uma condição de 25 alvos, não uma trajetória.
fig, axes = plt.subplots(3,1,figsize=(6.6,6.8),sharex=True,sharey=True)
for i,(ax,d) in enumerate(zip(axes,DIST)):
    for m,label,c,mk,ls in MODELS:
        ax.plot(ANG,values(m,'recall')[i]*100,color=c,label=label,
                marker=mk,ls=ls,lw=1.7,ms=4.6)
    ax.set_title(f'Distância câmera–pelve: {d} m',loc='left',fontsize=10)
    ax.set_ylim(-4,105); ax.set_yticks([0,25,50,75,100]); ax.set_ylabel('Recall (%)')
    ax.grid(axis='y',color='#dddddd',lw=.6); ax.set_axisbelow(True)
axes[-1].set_xticks(ANG);axes[-1].set_xlabel('Ângulo off-nadir (graus)')
fig.legend(*axes[0].get_legend_handles_labels(),loc='upper center',ncol=2,frameon=False,fontsize=9)
fig.tight_layout(rect=[0,0,1,.95],h_pad=1.1)
save(fig,'controle_recall_curvas')

# Duas escalas diferentes, identificadas; iguais entre detectores para cada métrica.
f1map=LinearSegmentedColormap.from_list('f1',['#f4f4ef','#9bb7a7','#315e57'])
fpmap=LinearSegmentedColormap.from_list('fp',['#faf5ee','#d7a780','#874528'])
fig,axes=plt.subplots(2,2,figsize=(7.0,4.9),layout='constrained')
for col,(m,label,*_) in enumerate(MODELS):
    for row,(field,scale,cmap,vmax,title) in enumerate([
        ('f1',100,f1map,100,'F1 (%)'),('fp',1,fpmap,31,'Falsos positivos (contagem)')]):
        ax=axes[row,col]; z=values(m,field)*scale
        im=ax.imshow(z,cmap=cmap,vmin=0,vmax=vmax,aspect='auto')
        ax.set_xticks(range(5),[f'{a}°' for a in ANG]);ax.set_yticks(range(3),[f'{d} m' for d in DIST])
        ax.set_title(label,fontsize=10);ax.set_xlabel('Off-nadir');ax.set_ylabel('Distância')
        for i in range(3):
            for j in range(5):
                s=f'{z[i,j]:.1f}'.replace('.',',') if field=='f1' else str(int(z[i,j]))
                ax.text(j,i,s,ha='center',va='center',fontsize=9,
                        color='white' if z[i,j]>vmax*.6 else '#222222')
        cb=fig.colorbar(im,ax=ax,shrink=.9,pad=.025);cb.set_label(title,fontsize=9);cb.ax.tick_params(labelsize=8)
save(fig,'controle_f1_fp_celulas')

# Contagens por distância: denominador fixo 125. FP fora desse denominador.
fig,axes=plt.subplots(2,1,figsize=(6.8,5.3),layout='constrained')
x=np.arange(3);w=.33
distance_rows=[]
for k,(m,label,c,*_) in enumerate(MODELS):
    sums=[]
    for d in DIST:
        sums.append({key:sum(r[key] for r in rows if r['model']==m and r['distance_m']==d) for key in ['tp','fp','fn']})
        distance_rows.append({'model':m,'distance_m':d,**sums[-1]})
    pos=x+(k-.5)*w; tp=np.array([s['tp'] for s in sums]); fn=125-tp; fp=[s['fp'] for s in sums]
    axes[0].bar(pos,tp,w,color=c,label=label)
    axes[0].bar(pos,fn,w,bottom=tp,color=c,alpha=.18,hatch='///',edgecolor=c,lw=.5)
    axes[1].bar(pos,fp,w,color=c,label=label)
    for p,t,f in zip(pos,tp,fn):
        axes[0].text(p,max(t/2,4),str(t),ha='center',va='center',fontsize=9,color='white' if t>10 else '#222222')
        axes[0].text(p,t+f/2,str(f),ha='center',va='center',fontsize=9,color='#222222')
    for p,v in zip(pos,fp):axes[1].text(p,v+1,str(v),ha='center',fontsize=9)
for ax in axes:
    ax.set_xticks(x,[f'{d} m' for d in DIST]);ax.grid(axis='y',color='#e0e0e0',lw=.5);ax.set_axisbelow(True)
axes[0].set_title('(a) VP: parte sólida; FN: parte hachurada (125 alvos por barra)',loc='left',fontsize=9)
axes[0].set_ylabel('Pessoas de referência');axes[0].set_ylim(0,137);axes[0].set_yticks([0,25,50,75,100,125])
axes[0].legend(loc='upper center',bbox_to_anchor=(.5,1.31),ncol=2,frameon=False,fontsize=9)
axes[1].set_title('(b) FP: previsões sem correspondência elegível',loc='left',fontsize=9)
axes[1].set_ylabel('Previsões');axes[1].set_ylim(0,85);axes[1].set_xlabel('Distância câmera–pelve')
save(fig,'controle_contagens_distancia')
with (DOC/'controle_agregado_distancia.csv').open('w',encoding='utf-8-sig',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=list(distance_rows[0]));writer.writeheader();writer.writerows(distance_rows)

with (DOC/'resumo_modelos_origem.csv').open(encoding='utf-8-sig') as f:
    summary={r['model']:r for r in csv.DictReader(f) if r['model'] in [m[0] for m in MODELS]}
assert len(summary)==2
fig,axes=plt.subplots(2,1,figsize=(6.6,4.9),layout='constrained')
for ax,metrics,title in zip(axes,[['precision','recall','f1'],['map50','map50_95']],
        ['(a) Ponto operacional: confiança 0,25 e IoU 0,50','(b) AP: avaliador COCO comum, maxDets=100']):
    x=np.arange(len(metrics));w=.32
    for k,(m,label,c,*_) in enumerate(MODELS):
        v=[100*float(summary[m][key]) for key in metrics];pos=x+(k-.5)*w
        ax.bar(pos,v,w,color=c,label=label)
        for p,y in zip(pos,v):ax.text(p,y+1.5,f'{y:.2f}'.replace('.',','),ha='center',fontsize=9)
    ax.set_xticks(x,[{'precision':'Precisão','recall':'Recall','f1':'F1','map50':r'$AP_{50}$','map50_95':r'$AP_{50:95}$'}[key] for key in metrics])
    ax.set_ylim(0,100);ax.set_ylabel('(%)');ax.set_title(title,fontsize=9,loc='left')
    ax.grid(axis='y',color='#dddddd',lw=.5);ax.set_axisbelow(True)
axes[0].legend(loc='upper center',bbox_to_anchor=(.5,1.34),ncol=2,frameon=False,fontsize=9)
save(fig,'controle_metricas_globais')

# Ilustração de previsões já presentes no relatório; nenhuma inferência nova.
fig,axes=plt.subplots(2,3,figsize=(7.0,3.8))
for i,a in enumerate([0,60]):
    for j,d in enumerate(DIST):
        ax=axes[i,j];ax.imshow(Image.open(IMG/f'pred_yolo_{d}_{a}.png'));ax.axis('off')
        state='VP' if a==60 and d in [10,20] else 'FN'
        ax.set_title(f'{d} m · {a}° · {state}',fontsize=9,pad=3)
fig.subplots_adjust(left=0,right=1,bottom=0,top=.94,wspace=.03,hspace=.23)
save(fig,'controle_exemplos_predicoes')
print(json.dumps({'figuras_pdf':7,'series_originais':15,'modelos':list(summary),'novas_inferencias':False},ensure_ascii=False))
