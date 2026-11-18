# Imagens e gráficos do experimento controlado

Esta ampliação apresenta a mesma base de resultados, sem novas inferências, sem ajuste de pesos e sem imagens reais. A auditoria formal das referências permanece pendente após a pré-banca.

## Capturas originais

Foi selecionada a primeira série completa na ordem de captura: PERSON_001, imagens 000001.png a 000015.png. A ordem é distância de 10, 20 e 40 m; dentro de cada distância, ângulos de 0, 15, 30, 45 e 60 graus. Não houve seleção por acerto do detector.

- Pasta das 375 capturas: https://drive.google.com/drive/folders/1VIKLqqMjMEWN9hvEzJjHzp78UuRaqcqL
- Pasta dos metadados: https://drive.google.com/drive/folders/1QVIGi2b4dqgvxxBeFLC1BRMYiBtv1yfs
- O arquivo `controle_figuras_manifesto.json` registra os links individuais e SHA256 dos 15 arquivos originais consultados. Todos corresponderam ao campo `image_sha256` do metadata.
- O arquivo `controle_metadata_15_ilustracoes.csv` conserva as 15 linhas de origem e seus campos, incluindo AGL e distância efetiva.
- Os originais completos consultados estão preservados na pasta de trabalho `.tcc_build/control_originais`, fora do ZIP. O ZIP contém os recortes utilizados e duas vistas completas recomprimidas sem alteração dos pixels, suficientes para regenerar as figuras.

Todos os 15 recortes usam os limites em pixels x=810..1109 e y=415..664, com 300 × 250 pixels. Não há ampliação variável por personagem, mudança de contraste ou inclusão artificial de pessoas. Os dois contextos completos correspondem a 000001 e 000005, a 10 m e 0/60 graus. Os PNG de contexto foram recomprimidos; o hash do arquivo recomprimido não deve ser comparado ao SHA256 do arquivo original, embora seus pixels sejam os mesmos.

## Previsões ilustrativas

Os seis recortes de previsões provêm dos painéis do YOLO11s original no relatório `TCC_Experimento_Controlado_Angulo_Distancia.pdf`, páginas 15–17. As cópias já utilizadas na apresentação foram convertidas para PNG para compor a figura. Verde é a referência; azul é uma proposta com confiança pelo menos 0,25. VP/FN se refere ao pareamento da pessoa, exigindo IoU pelo menos 0,50. Um FN pode coexistir com FP no mesmo quadro.

Esses painéis mostram o primeiro ator, em 0 e 60 graus e nas três distâncias. Não representam uma contagem nova de mecanismos de erro e não substituem a auditoria planejada.

## Gráficos e entradas

`gerar_figuras_controle.py` usa `controle_originais_conferido.csv` (30 linhas, 15 por detector) e `resumo_modelos_origem.csv`, selecionando exclusivamente YOLO_original e FRCNN_pretreinado. As linhas históricas de modelos ajustados não são plotadas.

Figuras geradas:

1. `controle_contexto_cena`: dois quadros completos.
2. `controle_serie_15_vistas`: quinze recortes com ângulos, distâncias e identificadores.
3. `controle_recall_curvas`: recall em função do ângulo, com um painel por distância.
4. `controle_exemplos_predicoes`: seis exemplos já documentados de previsões do YOLO11s COCO.
5. `controle_f1_fp_celulas`: matrizes de F1 e FP com escalas comuns entre detectores para cada medida.
6. `controle_contagens_distancia`: VP/FN em 125 referências por distância e FP apresentados separadamente. As contagens derivadas ficam em `controle_agregado_distancia.csv`.
7. `controle_metricas_globais`: precisão, recall e F1 no ponto operacional e AP50/AP50:95 do avaliador COCO comum.

Todas as escalas percentuais quantitativas vão de 0 a 100. Linhas entre pontos são guias de leitura entre condições discretas; não são medições contínuas de ângulo. Não há intervalos de confiança, curvas precisão–recall inventadas a partir de médias ou estimativa de FPS.

Para regerar, instalar Python 3 com matplotlib, numpy e Pillow e executar `python documentacao/gerar_figuras_controle.py` a partir da pasta principal das fontes. Os arquivos em `figuras/controle_fontes` e os CSV devem permanecer no pacote. Isso regenera as figuras documentais, não o dataset ou as previsões.
