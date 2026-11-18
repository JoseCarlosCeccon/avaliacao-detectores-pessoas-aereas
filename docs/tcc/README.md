# Documento do TCC

Esta pasta contém a entrega de 2 de novembro de 2026 de **Avaliação de ângulos de captura para detecção de pessoas em imagens aéreas sintéticas**.

- [PDF compilado](main.pdf)
- [Fontes LaTeX e figuras](source/)
- [Registro das alterações](source/documentacao/REGISTRO_CONTINUIDADE.md)

Para recompilar o PDF a partir da fonte:

```powershell
cd .\docs\tcc\source
pdflatex -interaction=nonstopmode -halt-on-error main.tex
bibtex main
pdflatex -interaction=nonstopmode -halt-on-error main.tex
pdflatex -interaction=nonstopmode -halt-on-error main.tex
```

O documento descreve o experimento sintético com YOLO11s e Faster R-CNN, a análise de ângulo e distância e as limitações da transferência para capturas reais. O [guia de auditoria e fine-tuning](../auditoria/README.md) documenta a preparação das etapas posteriores à entrega.
