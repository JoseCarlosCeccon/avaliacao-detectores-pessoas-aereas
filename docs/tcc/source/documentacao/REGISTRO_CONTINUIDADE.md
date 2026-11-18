# Atualização de 2 de novembro de 2026

Aplicadas somente as orientações de título e discussão da aquisição sintética/real. O título passa a ser **Avaliação de ângulos de captura para detecção de pessoas em imagens aéreas sintéticas**, incluindo capa, folha de rosto e metadados do PDF. Retirada a explicação referente ao antigo título com classificação.

Incluídas a subseção sobre câmera virtual e aquisição favorável, uma delimitação operacional na metodologia e limitações na conclusão. A relação com câmeras de boa qualidade é conceitual: não se afirma equivalência com sensor ou lente calibrados, nem desempenho em fotografias reais.

Preservados tabelas, figuras, contagens, métricas, pesos e descrição das execuções. Não executados auditoria visual do dataset, inferência ou fine-tuning. O guia de auditoria e fine-tuning é planejamento separado, não resultado do TCC. Os registros históricos de treinamento devem ser conferidos antes de qualquer reutilização.

Backup anterior: .tcc_build/backup_antes_titulo_cameras_20261102. A entrega de 19/10 permanece preservada.

# Registro de continuidade

## Correções editoriais de 20 de outubro de 2026

Foram aplicadas as correções de voz autoral indicadas nas seções 3.1, 3.9, 4.1, 4.2.2 e 4.8 e nas fontes das Figuras 3 e 5. A seção 1.5 passou a mencionar explicitamente as seções 2.3, 2.4 e 2.7 por referências automáticas. A descrição do Faster em 4.1 especifica que o recorte de 380 imagens se refere ao acervo observacional, preservando sua avaliação nas 375 capturas controladas.

O hash SHA256 foi transferido integralmente para uma nota de rodapé. A Tabela 4 passou a usar alinhamento à esquerda nas colunas dos detectores e quebras explícitas nos parâmetros de entrada. A redação do ambiente apresenta as versões das execuções de origem, sem representar nova execução dos modelos nesta edição. Não houve alteração de resultados, configurações ou pesos. A versão anterior foi preservada em `.tcc_build/backup_antes_revisao_editorial_20261020`.

## Síntese da seção 2.7

A seção sobre objetos pequenos foi condensada a pedido do autor. Foram mantidos os três subtópicos, as referências, a explicação de escala e redimensionamento, o exemplo de IoU e a relação com o controle e as florestas. Foram reduzidos exemplos e trechos repetidos, sem alterar resultados. A versão anterior está em `.tcc_build/backup_antes_resumo_secao_27`.

## Revisão das lacunas da fundamentação

Foram incluídas seções sobre dados sintéticos e diferença de domínio, Unreal Engine como instrumento de pesquisa e detecção de objetos pequenos. A descrição do YOLO11s foi ampliada com backbone, combinação de escalas, C3k2, SPPF, C2PSA, P3/P4/P5 e cabeça desacoplada anchor-free. Uma tabela sintetiza as funções desses componentes.

Foram consultados o preprint de Khanam e Hussain (2024), os arquivos oficiais da arquitetura na versão v8.3.0 e fontes primárias sobre dados sintéticos, domain randomization, UnrealCV e escala de objetos. A versão v8.3.0 serve como referência estrutural consultada; não substitui a versão 8.4.171 transcrita dos registros de execução nem representa nova inspeção do checkpoint utilizado.

O texto distingue treinamento sintético para transferência sim-to-real da avaliação atual, que aplica pesos COCO a imagens renderizadas. A seção de objetos pequenos apresenta exemplos didáticos de redimensionamento e IoU, sem introduzir novas medidas do acervo ou atribuir automaticamente as falhas de 40 m e florestas à escala. Não houve mudança de pesos, inferência, contagens ou gráficos. A versão anterior de 47 páginas foi preservada em `.tcc_build/backup_antes_revisao_fundamentacao`.

## Retirada temporária dos apêndices

A pedido do autor, o PDF passou a encerrar nas referências bibliográficas, sem apêndices ou páginas reservadas. Foram retiradas também as chamadas aos apêndices na introdução, na metodologia e nos resultados. O sumário e as listas são gerados novamente sem esses elementos.

Os arquivos dos antigos apêndices permanecem na pasta de trabalho original para recuperação posterior, mas não integram o PDF nem o pacote de fontes desta versão. O autor informou que organizará a documentação no GitHub depois; nenhum repositório foi criado ou linkado nesta alteração. A versão anterior está em `.tcc_build/backup_antes_retirar_apendices`.

## Ajuste editorial para o documento em construção

A pedido do autor, foram retiradas do texto compilado as seções Delimitação, Alcance e continuidade, Auditoria visual planejada e Limites da discussão. O apêndice com o protocolo de auditoria deixou de integrar o PDF. Também foram removidas menções a próximos passos e ao cronograma após a pré-banca no resumo, na introdução, na metodologia, nos resultados e nos apêndices compilados.

As informações efetivas do método, os resultados, as figuras e as ressalvas necessárias para interpretar as métricas foram preservados. O texto continua identificando os resultados como preliminares. O planejamento da auditoria não foi executado nem apagado: permanece nos arquivos de trabalho, separado do TCC compilado. A versão anterior está em `.tcc_build/backup_antes_remover_delimitacao_proximos_passos`.

## Ilustração conceitual do ângulo off-nadir

Foi incorporada à subseção de off-nadir da fundamentação a imagem fornecida pelo autor do TCC, reproduzida integralmente, sem edição de seu conteúdo. A fonte é European Space Imaging, no artigo de Zuzana Hajkova publicado em 31 de janeiro de 2024: https://www.euspaceimaging.com/blog/2024/01/31/what-is-ona-off-nadir-angle-in-satellite-imagery/ . A página de origem foi consultada, e a referência foi acrescentada à bibliografia.

O texto explica a referência vertical e distingue os ângulos ilustrativos de 5, 15 e 30 graus das cinco condições do experimento. Também diferencia o esquema de satélite do delineamento de distância câmera–pelve constante, sem atribuir à ilustração resultados do TCC. A imagem acompanha o pacote editável como `figuras/off_nadir_eusi.png`.

## Ampliação do experimento controlado e dos gráficos

A metodologia passou a distinguir fatores manipulados, condições preservadas e mudanças que acompanham a geometria. Foram detalhados o movimento da câmera entre capturas, a diferença entre AGL e distância até a pelve, a unidade repetida e o encadeamento da captura até as métricas.

Foram acrescentadas duas vistas completas e uma série de quinze recortes originais do primeiro ator, cobrindo todas as combinações. Os 15 hashes foram conferidos com os metadados do Drive. A seleção documental das imagens não representa conclusão da auditoria formal de referências.

Os resultados passaram a mostrar seis exemplos de previsões já documentadas do YOLO11s original. O gráfico de recall foi refeito em formato vetorial. Três novos gráficos quantitativos apresentam F1/FP por condição, VP/FN/FP por distância e métricas globais dos dois detectores COCO. A discussão explica a coexistência de FP e FN, a precisão elevada com muitas omissões e a mudança de vantagem entre modelos conforme a distância.

Os scripts e dados de geração das figuras acompanham as fontes. As contagens e os pesos foram preservados; não houve nova inferência. A versão anterior foi guardada em `.tcc_build/backup_antes_ampliacao_controle`. Detalhes de origem e recortes constam em `FIGURAS_CONTROLE.md` e `controle_figuras_manifesto.json`.

## Alterações desta versão

O título foi atualizado para a formulação definida pelo autor. A folha de rosto identifica **Prof. Dr. Ricardo Maroquio Bernardo**, confirmado também no portal institucional: https://integra.ifes.edu.br/portfolio/pessoas/ricardo-maroquio-bernardo . A ficha catalográfica e a folha de aprovação não são impressas nesta versão para pré-banca.

A introdução foi reescrita para apresentar a motivação, a pergunta, os objetivos e o recorte sem narrar mudanças antigas de planejamento. O uso da palavra classificação no título foi relacionado à detecção da classe pessoa com localização.

A fundamentação agora explica pesos pré-treinados, as duas implementações, AGL, distância câmera–pelve, NMS, pareamento e métricas. Foram incorporados estudos anexados sobre validação sintética, perspectiva, escala e detecção aérea. As referências de exemplo que não sustentavam o texto atual foram retiradas da bibliografia principal.

A metodologia descreve o carregamento e a inferência em Python, o piso de armazenamento de 0,001, o limiar operacional de 0,25 e o IoU de pareamento de 0,50. A versão da TorchVision foi conferida no registro do Drive. As observações sobre a origem dos tempos foram preservadas.

A discussão mantém as 15 células do controle e acrescenta a leitura das diferenças por distância, a importância dos mapas florestais e a comparação angular observacional com faixas de distância comuns. Os valores agregados anteriores foram mantidos e conferidos; não houve geração de novas medições.

Foram acrescentados apêndices com o protocolo da auditoria, o dicionário resumido de campos e trechos dos scripts originais. As conclusões e os resumos identificam os resultados como preliminares, sem propor imagens reais como requisito de continuidade.

## Fontes e materiais utilizados

Os relatórios da pasta `Documentos de todas execucoes` fornecem os resultados experimentais. A lista de fontes e páginas está no Apêndice A. As cópias dos relatórios em `Atualizações TCC/Atualizacoes 10-07/Documentos` pertencem ao material de apoio; cópias repetidas não foram contadas como novas execuções.

Da pasta `PROJETOS SIMILARES`, foram consultados especialmente `2201.06629v1.pdf`, `sensors-25-00772-v2.pdf`, `s41598-025-27441-8.pdf`, `Ricardo_Roberto_Storck_Pinto.pdf` e a tese de Ricardo Maroquio Bernardo. Foram utilizados para contextualização e discussão, sem copiar sua redação nem atribuir seus resultados a este TCC.

Foram consultados no Drive os scripts `executar_testes_tcc.py`, `faster_core.py` e `analyze.py`, o arquivo de versões e as tabelas do experimento controlado. As fontes históricas também incluem modelos ajustados; somente as linhas `YOLO_original` e `FRCNN_pretreinado` integram os resultados selecionados.

## Pendências reais antes da versão final

- Realizar a auditoria visual após a pré-banca e registrar a extensão efetivamente examinada.
- Documentar e incorporar qualquer correção que altere referências, contagens ou métricas.
- Confirmar o sistema operacional efetivo das execuções nos registros da máquina de origem.
- Submeter o texto ao orientador para revisão científica e editorial.
- Acrescentar a ficha catalográfica e os dados reais de aprovação na etapa de depósito, conforme o procedimento institucional.

Não há previsão de coleta com pessoas reais nesta versão. O formulário de auditoria é apenas um instrumento de trabalho pendente. Os comprovantes de integridade e os testes históricos de código não foram apresentados como auditoria manual de todas as imagens.
