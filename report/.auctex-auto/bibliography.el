(TeX-add-style-hook
 "bibliography"
 (lambda ()
   (LaTeX-add-bibitems
    "han"
    "bleu"
    "wd"
    "bigbench"
    "contamination"))
 '(or :bibtex :latex))

