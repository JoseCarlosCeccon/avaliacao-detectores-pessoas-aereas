# Atualização de 2 de novembro de 2026

Aplicadas somente as orientações de título e discussão da aquisição sintética/real. O título passa a ser **Avaliação de ângulos de captura para detecção de pessoas em imagens aéreas sintéticas**, incluindo capa, folha de rosto e metadados do PDF. Retirada a explicação referente ao antigo título com classificação.

Incluídas a subseção sobre câmera virtual e aquisição favorável, uma delimitação operacional na metodologia e limitações na conclusão. A relação com câmeras de boa qualidade é conceitual: não se afirma equivalência com sensor ou lente calibrados, nem desempenho em fotografias reais.

Preservados tabelas, figuras, contagens, métricas, pesos e descrição das execuções. Não executados auditoria visual do dataset, inferência ou fine-tuning. O guia de auditoria e fine-tuning é planejamento separado, não resultado do TCC. Os registros históricos de treinamento devem ser conferidos antes de qualquer reutilização.

Backup anterior: .tcc_build/backup_antes_titulo_cameras_20261102. A entrega de 19/10 permanece preservada.


---

# Continuidade do TCC em 19 de outubro de 2026

Esta pasta contém o texto atualizado de **Avaliação de ângulos de captura para detecção de pessoas em imagens aéreas sintéticas**, de José Carlos Ceccon Neto, sob orientação do Prof. Dr. Ricardo Maroquio Bernardo.

Na entrega compactada estão os arquivos editáveis. O PDF compilado é entregue separadamente; na pasta de trabalho original, ele também está salvo como `main.pdf`.

## Arquivos principais

- `main.tex`: documento principal. Inclui os capítulos e as referências bibliográficas, sem apêndices nesta versão.
- `main.pdf`: versão compilada correspondente aos arquivos desta pasta.
- `textuais/`: introdução, fundamentação, metodologia, resultados e conclusão.
- `pre_textuais/`: resumo, abstract e listas.
- `bibliografia.bib`: referências utilizadas no texto.
- `documentacao/`: fontes de conferência, registro de continuidade e formulário da auditoria.
- `codigo_consultado/`: cópias dos scripts originais consultados no Drive. Não são uma instalação pronta do sistema.
- `figuras/controle_fontes/`: imagens usadas na série visual do controle e nos exemplos documentados de previsão.
- `documentacao/FIGURAS_CONTROLE.md`: origem das novas figuras, dados utilizados e instruções para regenerar os gráficos.

O PDF anterior e os arquivos alterados foram preservados em `.tcc_build/backup_antes_continuidade_20261019`, na pasta superior. As cópias antigas em `TCC/docs/tcc/source` e em `BACKUP_ANTES_REFORMULACAO_20261010` permanecem históricas; a fonte desta entrega é o `main.tex` desta pasta.

## Escopo consolidado

O estudo avalia exclusivamente imagens sintéticas do Unreal Engine 5.4.4. Utiliza YOLO11s e Faster R-CNN ResNet-50 FPN V2 com pesos originais COCO, sem fine-tuning. O controle de 375 imagens é o experimento principal. O acervo de 2.300 imagens e seu subconjunto comum de 380 imagens fornecem análises complementares. O subconjunto não deve ser somado ao acervo como nova coleta.

A tarefa operacional é detecção da classe pessoa e localização por caixas. O termo classificação foi preservado no título definido pelo autor e explicado na introdução.

## Situação da pesquisa

O texto reúne resultados existentes e sua conferência documental. Os detectores não foram reexecutados nesta continuidade. A pedido do autor, o PDF não contém apêndices, seção de delimitação, planejamento de próximos passos ou protocolo de auditoria. Os materiais dos antigos apêndices e o planejamento da auditoria permanecem somente na pasta de trabalho original, sem serem apresentados como atividades concluídas. O autor indicou que organizará a documentação no GitHub posteriormente; esta versão não inclui link ou seção reservada para isso.

O uso de imagens reais e a operação em voo estão fora do escopo. Não há um único vencedor em todas as métricas. Os tempos por imagem têm intervalos de cronometragem diferentes e não constituem benchmark padronizado.

## Formatação adotada

Foi preservada a classe `iftex.cls` e a estrutura do modelo fornecido pelo autor. A apresentação utiliza papel A4, margens superior/esquerda de 3 cm e inferior/direita de 2 cm, fonte Helvética e corpo de 12 pontos, com espaçamento de 1,5 no texto. As referências e os códigos possuem configuração própria. As legendas das figuras foram posicionadas acima das ilustrações, com fontes identificadas abaixo.

As recomendações foram confrontadas com o manual de 2024 disponibilizado pelo IFES: https://alegre.ifes.edu.br/images/conteudo/Biblioteca/Normas/Normas_para_Apresentao_de_Trabalhos_Acadmicos_e_Cientficos_2024.pdf . A adoção do modelo não dispensa a conferência institucional da versão destinada ao depósito, inclusive quanto a ficha catalográfica, folha de aprovação e eventuais atualizações das normas. Não foram inventados dados da banca ou aprovação.

## Compilação

Abra `main.tex` em um editor LaTeX com a distribuição instalada. O documento usa a classe e os arquivos locais desta pasta. Para evitar arquivos auxiliares de versões antigas, use um diretório de compilação vazio ou um nome de compilação novo.

Sequência usual: uma execução de pdfLaTeX, uma de BibTeX e pelo menos duas de pdfLaTeX. Se o editor ainda indicar referências pendentes após uma alteração de paginação, execute novamente pdfLaTeX. O arquivo de bibliografia precisa permanecer acessível ao BibTeX.

O pacote editável não inclui o dataset completo, os pesos ou o projeto Unreal. Os scripts em `codigo_consultado` mantêm os caminhos e dependências da origem e não devem ser executados sem configuração do ambiente.
