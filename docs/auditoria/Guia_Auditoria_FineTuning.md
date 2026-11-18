# Guia de auditoria visual e fine-tuning

José Carlos Ceccon Neto | TCC | 2 de novembro de 2026

## Finalidade e estado das atividades

Este guia descreve procedimentos a executar. Sua produção não representa realização da auditoria, treinamento, nova inferência ou validação de resultados. O PDF atualizado do TCC mantém os resultados dos pesos originais COCO.

O objetivo central continua sendo avaliar ângulos de captura para detecção de pessoas em imagens aéreas sintéticas. O fine-tuning deve acrescentar uma comparação entre a configuração original e uma configuração ajustada do mesmo modelo, com resultados por condição.

## Sequência de trabalho

1. Inventariar os arquivos e preservar os originais.
2. Definir e registrar os critérios e a seleção da auditoria.
3. Executar a conferência, resolver dúvidas e documentar correções.
4. Conferir os registros históricos de treinamento e a separação dos conjuntos.
5. Definir o protocolo do fine-tuning e preparar o ambiente.
6. Executar o ajuste somente após conferir referências e partições.
7. Avaliar original e ajustado com protocolo comum.
8. Atualizar o TCC com o que foi efetivamente realizado.

## O que já existe e precisa ser conferido

O acervo observacional contém 2.300 imagens. O subconjunto de 380 pertence a esse acervo. O controle contém 375 capturas separadas. Não somar as 380 ao acervo como novas imagens.

O arquivo contexto_geral.md e os relatórios locais registram treinamento anterior dos modelos. No YOLO11s, o histórico descreve oito épocas, CPU, congelamento parcial e partições de 1.560/360/380 imagens. Esses registros não comprovam que todos os arquivos necessários estejam disponíveis neste computador.

Antes de repetir um treinamento, conferir checkpoint, manifesto das partições, protocolo, logs e previsões. A reutilização depende da compatibilidade e rastreabilidade desses materiais e deve ser acordada com o orientador. Resultados históricos ajustados não foram incorporados ao TCC nesta atualização.

<!-- PAGE -->

## 1. Preparar a auditoria e selecionar as imagens

**Passo 1 - Preservar a base.** Guardar uma cópia identificada dos arquivos originais, referências, previsões e métricas. Registrar hashes quando disponíveis. Correções devem gerar versões novas e um histórico de alterações.

**Passo 2 - Fazer o inventário.** Para cada captura, localizar imagem original, máscara, caixa de referência, metadados e previsões dos dois detectores. Registrar ausências. Os recortes ilustrativos do TCC não substituem a imagem completa nem as previsões armazenadas.

**Passo 3 - Registrar o protocolo.** Informar responsável, data, versão dos dados, conjuntos abrangidos, critérios, seleção e regra de ampliação. Identificar claramente o que será inspeção visual e o que será conferência automática.

**Passo 4 - Fixar a seleção.** A planilha existente propõe PERSON_001, PERSON_013 e PERSON_025 nas 15 condições: 45 imagens. Preservar essa lista e registrar mudanças. A lista cobre cinco ângulos e três distâncias, mas três personagens não representam necessariamente as quatro malhas.

**Passo 5 - Conferir a cobertura.** Relacionar personagens, malhas, poses e orientações. Se necessário, propor a inclusão de um representante da malha ausente. Quatro séries completas corresponderiam a 60 imagens; isso é uma alternativa de ampliação, não atividade concluída ou exigência universal.

**Passo 6 - Definir o alcance.** Uma revisão das 45 capturas do controle não verifica o acervo observacional nem as referências de treinamento. Para o fine-tuning, incluir revisão das anotações de treino/validação/teste segundo seleção documentada e checagens automáticas em todos os arquivos. Se viável, inspecionar integralmente as 375 capturas controladas.

**Entrega desta etapa:** inventário, lista fixa da amostra, cobertura das condições e protocolo datado. Uma amostra dirigida permite diagnóstico, mas não estima automaticamente uma taxa representativa de erro de todo o dataset.

<!-- PAGE -->

## 2. Executar a inspeção visual

**Passo 7 - Abrir primeiro a imagem sem previsões.** Conferir personagem, enquadramento e visibilidade. No controle, verificar um alvo elegível, sem corte de borda ou oclusão externa inesperados. Não determinar valores exatos de ângulo ou distância apenas pela aparência: conferir metadados e geometria registrada.

**Passo 8 - Examinar máscara e referência.** Conferir correspondência ao ator, partes visíveis, ausência de sombra ou fundo incorporados indevidamente, limites da caixa e elegibilidade. A caixa representa a silhueta visível; uma caixa retangular pode conter fundo entre partes do corpo sem estar incorreta.

**Passo 9 - Respeitar as regras existentes.** Pessoas parcialmente ocluídas ou cortadas podem ser elegíveis. O método não aplica tamanho mínimo adicional de caixa. Não excluir um alvo porque é pequeno ou difícil. Mudanças nessas regras exigem nova versão do protocolo e recálculo.

**Passo 10 - Sobrepor as previsões.** Usar cores distintas para referência e cada detector. Conferir coordenadas na imagem original e efeito do redimensionamento do visualizador. Uma sobreposição desenhada incorretamente não prova falha da anotação.

**Passo 11 - Conferir o pareamento.** No ponto operacional atual: confiança maior ou igual a 0,25; IoU maior ou igual a 0,50; associação um a um, conforme a ordenação documentada. Conferir o IoU numericamente. A aparência de uma caixa não substitui o cálculo.

**Passo 12 - Registrar erros observáveis.** Para FP: fundo, sombra, duplicata, localização inadequada, pessoa excluída pelo protocolo ou indeterminado. Para FN: ausência de proposta operacional, proposta abaixo do limiar, localização inadequada, conflito de pareamento ou indeterminado. Registrar suspeita de problema de referência separadamente.

Uma pessoa pode gerar FP e FN simultaneamente se existir uma caixa sem pareamento. Ausência de proposta armazenada não significa ausência de toda resposta interna da rede. Quando a investigação exigir propostas abaixo de 0,25, utilizar somente as propostas efetivamente preservadas e registrar o piso disponível.

<!-- PAGE -->

## 3. Documentar, corrigir e encerrar a auditoria

**Passo 13 - Registrar duas unidades.** Manter uma tabela por imagem para captura/referência e outra por previsão ou referência não recuperada para os erros. Uma imagem pode conter vários FP de tipos diferentes.

Campos por imagem: conjunto, cenário, ID da imagem, personagem, malha, ângulo, distância, AGL, referência, situação, observação, evidência, responsável, data e versão do protocolo.

Campos por resultado: imagem, modelo, ID da previsão/referência, confiança, coordenadas, IoU, VP/FP/FN registrado pelo avaliador, categoria visual, concordância da conferência e providência. Não preencher valores que não puderem ser recuperados.

Situações recomendadas: PENDENTE, CONFORME, DIVERGÊNCIA, DUVIDOSO, CORRIGIDO E REAVALIADO. Um FP verdadeiro do detector pode ocorrer em imagem CONFORME: essa situação descreve a consistência dos dados e da avaliação, não a qualidade do modelo.

**Passo 14 - Guardar evidências.** Manter o original e uma cópia ilustrativa com sobreposições. Fotografias de tela e recortes devem apontar para o arquivo original. Identificar os casos, sem substituir silenciosamente arquivos anteriores.

**Passo 15 - Tratar divergências.** Corrigir erros confirmados de referência ou processamento. Conferir ambos os modelos com a mesma referência corrigida. Investigar outros arquivos potencialmente afetados pela mesma rotina. Não apagar falhas legítimas dos detectores para elevar métricas.

**Passo 16 - Ampliar quando necessário.** Associação errada de imagem e máscara, transformação incorreta de coordenadas ou um defeito sistemático de anotação justificam ampliar a revisão ao grupo afetado. Um único erro grave pode exigir ampliação. Não adotar uma porcentagem arbitrária como garantia de qualidade.

**Passo 17 - Conferir consistência.** Reexaminar uma parte da amostra em outro momento; quando possível, solicitar segunda leitura dos casos duvidosos. Declarar se a revisão foi exclusivamente do autor. Registrar divergências e como foram resolvidas.

**Passo 18 - Produzir a síntese.** Informar imagens, referências e combinações imagem-modelo examinadas, cobertura, problemas, correções, impacto nas métricas e pendências. Examinar 45 imagens nos dois modelos corresponde a 90 combinações imagem-modelo, não a 90 imagens. Relatar somente o alcance efetivo da inspeção.

<!-- PAGE -->

## 4. Definir o experimento de fine-tuning

**Passo 19 - Escolher um modelo.** O YOLO11s é uma opção prática para manter continuidade com os arquivos históricos. A escolha final deve considerar os materiais recuperados e os recursos computacionais disponíveis. Ajustar um modelo atende à orientação recebida; não é necessário ampliar automaticamente para várias arquiteturas.

**Passo 20 - Verificar o treinamento anterior.** Procurar o relatório TCC_Treinamento_YOLO11s_Comparacao_Completa e os arquivos particoes.csv, dataset.yaml, protocolo_treinamento.json, treinamento_concluido.json, logs e best.pt. Os caminhos citados no histórico pertencem à máquina de origem e precisam ser localizados, não presumidos neste computador.

Se os materiais forem íntegros, conferir se é possível reutilizar o experimento. Caso faltem dados, pesos ou protocolo, registrar as ausências e definir uma nova execução identificada. Um PDF de resultados não substitui checkpoint e registros da execução.

**Passo 21 - Definir a pergunta complementar.** Comparar a resposta por ângulo e distância do YOLO11s original com a do YOLO11s ajustado, incluindo precisão e FP junto ao recall. Ganho de recall com aumento acentuado de FP não significa melhora em todos os critérios.

**Passo 22 - Separar os dados antes de treinar.** O histórico registra 1.560 imagens de treino, 360 de validação e 380 de teste, com agrupamento por spatial_repeat_id e semente 20261003. Conferir o manifesto efetivo antes de reutilizá-lo. As 375 capturas controladas devem permanecer fora do ajuste e da escolha de hiperparâmetros se forem usadas na avaliação complementar.

**Passo 23 - Prevenir contaminação.** Manter juntos quadros relacionados de uma estação/família de captura, incluindo ângulos e alturas. Verificar IDs e hashes entre partições. Ausência de arquivos idênticos não elimina semelhança visual ou compartilhamento de malhas, poses e mapas. Documentar essas limitações.

Os conjuntos de 380 e 375 imagens já foram examinados na pesquisa. Mesmo preservados do novo treinamento e da seleção de pesos, não devem ser apresentados como testes nunca observados. Não ajustar decisões após consultar seus resultados e chamá-los de validação independente.

<!-- PAGE -->

## 5. Preparar ambiente, anotações e protocolo

**Passo 24 - Conferir a infraestrutura.** Registrar sistema operacional, CPU, RAM, eventual GPU e versões das bibliotecas. Não presumir CUDA disponível. O treinamento histórico foi em CPU; sua duração não estima a duração de uma nova execução em outra máquina.

**Passo 25 - Conferir o dataset.** Relacionar imagem e anotação por ID único. Se converter para o formato YOLO, cada linha deve conter classe 0 e caixa normalizada: x_centro, y_centro, largura, altura. Conferir a conversão sobrepondo caixas às imagens e usando a convenção de coordenadas da origem. Não incluir sombras nas referências. Imagens sem pessoas elegíveis continuam úteis e devem ter anotação vazia conforme o formato utilizado.

Exemplo estrutural de dataset.yaml; substituir os caminhos antes de executar:

```yaml
path: C:/CAMINHO_REAL/dataset_auditado
train: images/train
val: images/val
test: images/test
names:
  0: person
```

Manter anotações correspondentes em labels/train, labels/val e labels/test. Não usar o YAML histórico do APDataset para treinar: o contexto registra que ele aponta treino, validação e teste ao mesmo conjunto para uma rotina de avaliação.

**Passo 26 - Escrever o protocolo antes da execução.** Registrar checkpoint inicial e hash, partições, número máximo de épocas, tamanho da entrada, batch, otimizador, taxa de aprendizado, congelamento, aumentos de dados, semente, hardware, critério de seleção e versões. Guardar também os parâmetros efetivamente resolvidos pela biblioteca.

**Passo 27 - Fixar como selecionar o modelo.** Usar a validação para selecionar o checkpoint e justificar o critério. Para continuidade com o histórico YOLO, pode-se adotar AP50:95 de validação. Não selecionar pesos ou limiares pelo teste nem pelo controle. Diferentes sementes ou condições de execução podem produzir diferenças; uma única execução não quantifica sua variabilidade.

O uso de freeze=10 no histórico significa congelamento parcial dos módulos iniciais. Não descrevê-lo como congelamento integral do backbone sem conferir os parâmetros treináveis da versão utilizada.

<!-- PAGE -->

## 6. Executar e registrar o treinamento

**Passo 28 - Fazer um ensaio de funcionamento.** Usar somente dados de treino/validação, em saída separada. Conferir leitura, classes, caixas, memória e salvamento. Se for necessário alterar batch ou entrada por falta de memória, fixar e registrar a configuração antes da execução principal.

**Passo 29 - Executar a configuração aprovada.** O exemplo abaixo é um ponto de partida inspirado no histórico, não um protocolo já executado nem garantia de melhoria. Exige ambiente configurado, dataset.yaml válido e checkpoint local. Confirmar a compatibilidade com a versão instalada; não atualizar bibliotecas automaticamente durante a experiência.

```python
from ultralytics import YOLO

model = YOLO(r"C:\CAMINHO_REAL\yolo11s.pt")
model.train(
    data=r"C:\CAMINHO_REAL\dataset.yaml",
    epochs=8,
    imgsz=640,
    batch=4,
    device="cpu",
    workers=0,
    freeze=10,
    optimizer="AdamW",
    lr0=0.001,
    seed=20261003,
    project=r"C:\CAMINHO_REAL\experimentos",
    name="yolo11s_ajuste_v1",
    exist_ok=False,
)
```

Os oito ciclos são uma proposta limitada de partida, não evidência de convergência. A taxa de aprendizado do exemplo é uma escolha proposta, não transcrição confirmada do histórico. Verificar demais parâmetros, parada antecipada e aumentos efetivos. Se outro protocolo for adotado, manter sua identificação e justificativa.

**Passo 30 - Acompanhar pela validação.** Registrar curvas de perdas e métricas. Se o ajuste apresentar problemas, investigar com treino/validação, sem consultar o teste para escolher a solução. Manter também resultados desfavoráveis.

**Passo 31 - Preservar a execução.** Guardar configuração resolvida, logs, curvas, checkpoints, hash do peso selecionado e critério de seleção. Confirmar como a versão utilizada gerou best.pt e last.pt. A seleção automática da biblioteca deve ser compatível com o critério declarado.

A documentação de treinamento e configuração da Ultralytics serve para conferir a API e os argumentos. As versões atuais podem diferir da versão histórica; registrar a versão efetiva da execução e conferir seu comportamento.

<!-- PAGE -->

## 7. Comparar original e ajustado

**Passo 32 - Congelar a avaliação.** Usar as mesmas imagens e referências para os dois pesos, filtrando pessoa em ambos. Preservar o protocolo operacional: confiança 0,25, IoU de pareamento 0,50 e associação um a um. Registrar redimensionamento, NMS, limite de caixas e demais parâmetros de inferência.

O modelo ajustado pode ter saída especializada em pessoa, enquanto o original mantém as classes COCO. Documentar essa diferença e a possível diferença de calibração dos escores. Não atribuir todo contraste exclusivamente à arquitetura.

**Passo 33 - Exportar previsões identificadas.** Guardar caixas, escores, classes e IDs das imagens de cada modelo. Configurar os scripts de avaliação em cópia separada e adaptar os caminhos da máquina de origem. Conferir se o adaptador suporta o checkpoint ajustado. Não presumir que as cópias codigo_consultado constituem uma instalação pronta.

**Passo 34 - Calcular métricas comparáveis.** Separar VP, FP, FN, precisão, recall e F1 no ponto operacional do cálculo de AP. Para AP comparável ao TCC, usar propostas preservadas desde 0,001 e COCOeval comum, IoUs 0,50:0,95 e maxDets=100. Um gráfico do validador nativo do treino não substitui essa avaliação comum.

**Passo 35 - Apresentar os dois universos.** No teste observacional, informar o número de imagens e referências efetivamente avaliadas. No controle, mostrar as 15 condições de ângulo e distância e o agregado das 375 imagens. Não somar as 380 imagens novamente ao acervo. No controle, cada acerto equivale a quatro pontos percentuais por célula de 25 referências.

**Passo 36 - Examinar a distribuição dos ganhos.** Comparar erros por ângulo, distância e cenário. Investigar regressões específicas mesmo quando a média melhorar. No histórico existe registro de desempenho desfavorável do YOLO ajustado em 10 m/60 graus; conferir as entradas antes de reutilizar esse achado, sem ocultá-lo por contrariar uma expectativa.

**Passo 37 - Relatar incerteza e alcance.** Não tratar imagens repetidas dos mesmos atores como pessoas independentes. Se forem incluídos intervalos ou testes, justificar a unidade e a dependência. A avaliação sintética não comprova desempenho em câmeras reais, mesmo após fine-tuning.

<!-- PAGE -->

## 8. Incorporar os resultados e fechar as entregas

**Passo 38 - Atualizar a metodologia.** Acrescentar dados de treinamento, partições, configuração, seleção e avaliação efetivas. Distinguir os modelos originais da etapa ajustada. Revisar frases como "sem treinamento adicional" somente quando o fine-tuning tiver sido efetivamente incorporado.

**Passo 39 - Atualizar os resultados.** Apresentar original versus ajustado, contagens, métricas comuns e gráficos por condição. Identificar o conjunto e o denominador de cada tabela. Não misturar dados de validação, teste observacional e controle.

**Passo 40 - Atualizar discussão, resumo e conclusão.** Explicar ganhos, perdas, FP e limitações. Manter o eixo da análise angular. A relação com imagens reais deve permanecer como alcance a verificar, sem afirmar equivalência com uma câmera física.

## Entregas que demonstram a execução

- Auditoria: protocolo datado, lista de imagens, registros preenchidos, evidências, dúvidas resolvidas ou declaradas e histórico de correções.
- Dados: manifestos das partições, verificações de IDs/hashes e versão das referências após correções.
- Fine-tuning: configuração efetiva, ambiente, logs, curvas, checkpoint selecionado e hash.
- Avaliação: previsões, regras de pareamento, tabelas e gráficos dos dois pesos nas mesmas entradas.
- Texto: descrição compatível com as atividades realizadas, sem converter planejamento em resultado.

## Pontos de conclusão

A auditoria pode ser relatada quando sua extensão, achados, correções e pendências estiverem documentados. O fine-tuning pode ser incorporado quando houver execução rastreável e comparação reproduzível com o original. Uma melhoria numérica não é condição para relatar um experimento válido; um resultado desfavorável deve ser preservado e discutido.

## Fontes para consulta

- Entrega de 19/10: TCC e fontes editáveis; parâmetros de avaliação e dados de origem.
- contexto_geral.md e relatórios de treinamento: registros históricos, não comprovação de nova execução.
- Ultralytics, treinamento: https://docs.ultralytics.com/modes/train/
- Ultralytics, configuração: https://docs.ultralytics.com/usage/cfg/
- Avaliador COCO: https://github.com/cocodataset/cocoapi/blob/master/PythonAPI/pycocotools/cocoeval.py

Consulta das páginas de treinamento/configuração: 2 de novembro de 2026. O guia propõe escolhas para a próxima etapa; confirmar sua adequação com o orientador antes da execução principal.
