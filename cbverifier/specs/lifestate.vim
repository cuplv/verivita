" rename spec.vim and put in ~/.vim/syntax/spec.vim

if exists("b:current_syntax")
  finish
endif
" Keywords
syntax keyword potionKeyword SPEC
highlight link potionKeyword Keyword

syntax match potionComment "|-"
highlight link potionComment Keyword