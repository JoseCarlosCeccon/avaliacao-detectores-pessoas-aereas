# Documento do TCC

Esta pasta registra a versao atual do texto academico do projeto.

- `main.pdf`: versao compilada do TCC.
- `source/`: arquivos LaTeX usados para gerar o documento.

Para recompilar o PDF a partir da fonte:

```powershell
cd .\docs\tcc\source
pdflatex -interaction=nonstopmode -halt-on-error main.tex
bibtex main
pdflatex -interaction=nonstopmode -halt-on-error main.tex
pdflatex -interaction=nonstopmode -halt-on-error main.tex
```

O documento inclui a metodologia, o referencial teorico e os resultados preliminares da avaliacao padronizada dos modelos YOLO11s, Faster R-CNN e SSD no subconjunto piloto do VisDrone.
