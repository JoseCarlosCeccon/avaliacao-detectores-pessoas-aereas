# Resultados dos Pilotos Experimentais

Data de execucao: 2026-06-01

Este arquivo registra os pilotos reais executados com pesos pre-treinados para validar o pipeline experimental do TCC. Os artefatos completos foram salvos em `outputs/pilots/`, enquanto este resumo fica versionado no Git por ser leve e reprodutivel.

## Configuracao

| Item | Valor |
| --- | --- |
| Dataset | `datasets/visdrone_person_yolo_pilot` |
| Amostras de treino | 50 imagens |
| Amostras de validacao | 20 imagens |
| Epocas | 1 |
| Batch size | 1 |
| Dispositivo | CPU |
| Pesos iniciais | Pre-treinados em COCO |
| Limiar de confianca | 0.25 |
| Criterio simples de acerto | IoU >= 0.50 |

## Comandos Executados

```powershell
python .\scripts\train_faster_rcnn_pilot.py --dataset-root .\datasets\visdrone_person_yolo_pilot --epochs 1 --batch-size 1 --max-train-samples 50 --max-val-samples 20 --device cpu
```

```powershell
python .\scripts\train_ssd_pilot.py --dataset-root .\datasets\visdrone_person_yolo_pilot --epochs 1 --batch-size 1 --max-train-samples 50 --max-val-samples 20 --device cpu
```

## Metricas Obtidas

| Modelo | Precision | Recall | F1-score | TP | FP | FN | Tempo medio de inferencia (s/img) | FPS |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Faster R-CNN ResNet-50 FPN | 0.4495 | 0.2817 | 0.3463 | 129 | 158 | 329 | 2.4302 | 0.4115 |
| SSD300 VGG16 | 0.0003 | 0.0022 | 0.0004 | 1 | 3999 | 457 | 0.2931 | 3.4119 |

## Perdas de Treinamento

| Modelo | Loss total | Componentes |
| --- | ---: | --- |
| Faster R-CNN ResNet-50 FPN | 1.0664 | classifier: 0.2334; box_reg: 0.2323; objectness: 0.2788; rpn_box_reg: 0.3219 |
| SSD300 VGG16 | 9.3630 | bbox_regression: 6.4322; classification: 2.9308 |

## Artefatos Gerados

```text
outputs/pilots/faster_rcnn/
  losses.csv
  metrics.csv
  summary.json
  predictions/
  faster_rcnn_pilot_last.pt

outputs/pilots/ssd/
  losses.csv
  metrics.csv
  summary.json
  predictions/
  ssd_pilot_last.pt
```

## Interpretacao Preliminar

O Faster R-CNN apresentou desempenho inicial superior ao SSD em precisao, recall e F1-score no subconjunto piloto. Visualmente, as predicoes do Faster R-CNN indicam que o modelo consegue localizar parte das pessoas pequenas, mas ainda deixa muitas instancias sem deteccao.

O SSD apresentou comportamento inadequado neste piloto, com quantidade muito elevada de falsos positivos. A inspecao visual mostrou muitas caixas em regioes de borda e areas sem pessoas. Esse resultado sugere que o limiar de confianca, o ajuste fino e/ou a configuracao do modelo precisam ser revisados antes de qualquer conclusao cientifica.

## Limitacoes Metodologicas

Estes resultados nao devem ser tratados como comparacao final do TCC. O experimento usa apenas 50 imagens de treino, 20 imagens de validacao, 1 epoca e CPU. Alem disso, as metricas aqui registradas usam uma avaliacao simples por IoU >= 0.50, enquanto os resultados finais devem incluir mAP@0.5 e mAP@0.5:0.95 de forma padronizada entre todos os modelos.

Para a etapa final, recomenda-se executar os tres modelos no mesmo conjunto de validacao/teste, com GPU, hiperparametros documentados, multiplas epocas e protocolo unico de avaliacao.
