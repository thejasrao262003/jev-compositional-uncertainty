# Paper sources

Three builds share one source of content, so the versions can't drift apart.

| File | Format | Build |
|---|---|---|
| `main.tex` | Article, one column (natbib, `plainnat`) | `tectonic main.tex` |
| `ieee.tex` | IEEE conference, two column (`IEEEtran`, `IEEEtran.bst`) | `tectonic ieee.tex` |
| `springer.tex` | Springer LNCS (`llncs`, `splncs04.bst`) | `tectonic springer.tex` |

**Shared content** (edit these, not the wrappers):
- `abstract.tex`, `body.tex`, `appendix.tex`: the text;
- `macros.tex`: packages and macros;
- `references.bib`: the bibliography.

**Wrappers** set the class, author block, bibliography style and float
handling. `widefigure`/`widetable` span both columns in the IEEE version;
`\para{}` gives each format its own run-in heading style.

**Reproducibility:**
- `python3 make_figure_data.py` regenerates the figure data from committed results.
- `python3 paper_statistics.py` recomputes intervals and contrasts.
- `python3 check_paper_numbers.py` confirms that 36 headline numbers in the text match the artifacts.
- `CITATION_VERIFICATION.md` records how each citation was checked.

**Double-blind submission:** replace the author blocks in the wrapper with
anonymous ones. Each wrapper marks the spot.

**Tooling:** Tectonic (`brew install tectonic`) fetches the IEEEtran and
llncs classes automatically on first build. With TeX Live, use
`latexmk -pdf <file>`.
