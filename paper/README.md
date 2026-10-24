# Manuscript

**Angelo Dalli (UMNAI). 2026. Separating Grounding, Execution and Attribution in
Foundation-Model-Assisted Banking Audits.** **UMNAI.**

The [PDF](Separating_Grounding_Execution_Attribution.pdf) contains four main-text
pages, one reference page and five pages of supplementary methods and records.

## LaTeX source

The final sources are in [`source/`](source/). They use the ACM `sigconf` layout
with `nonacm` for the named-author preprint. The bibliography is supplied as
`main.bbl`, with its BibTeX source and unmodified bibliography style.

With a TeX installation containing the ACM class dependencies, run from
`paper/source/`:

```sh
pdflatex -no-shell-escape -interaction=nonstopmode -halt-on-error main.tex
pdflatex -no-shell-escape -interaction=nonstopmode -halt-on-error main.tex
```

The source was also compiled successfully by arXiv with `pdflatex` and TeX Live
2025. Class dependencies include Libertine, Inconsolata and newtx fonts. The
bundled third-party class and bibliography style retain their upstream notices.
The corresponding class source is included in `source/third_party/acmart/`.

Appendix F describes arXiv's `anc/` packaging. In this repository the frozen
release ZIP is instead in `archive/`, with its working copy at the repository
root and the rendering/provenance additions in `supplements/`.

The manuscript retains the author's rights; the code MIT License does not grant
a separate manuscript license. See [`../NOTICE`](../NOTICE).
