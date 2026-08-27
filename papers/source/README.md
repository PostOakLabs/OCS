# Paper sources, build note

This directory mirrors the LaTeX sources of the omegacentauri.me paper set. Every `.tex` file
here is byte-identical to the file in the private working repository, and the `.bib` files it
draws on are all in this one directory.

Two of the mirrored files, `axi-note.tex` and `census-paper.tex`, live one directory deeper in
the working repository (`paper/axi/` and `paper/g/`), so their `\bibliography` lines point at
`../references`, `../masstension-extra` and `../engineered-extra`. Those parent-relative paths
do not resolve here, where the `.bib` files sit alongside the `.tex`.

To build either of those two files from this directory, either run BibTeX with the search path
set to this directory:

    BIBINPUTS=.:..: pdflatex axi-note.tex && BIBINPUTS=.:..: bibtex axi-note

or drop the `../` prefixes for a local build:

    \bibliography{references,masstension-extra,axi-extra}     % axi-note.tex
    \bibliography{references,engineered-extra,census-extra}   % census-paper.tex

The mirrored `.tex` is deliberately left unedited so it stays a faithful copy of the source
that produced the published PDF. The seven other papers build here without any adjustment.
