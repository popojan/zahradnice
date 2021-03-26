all: zahr

zahr:
	g++ -std=c++14 -lncurses src/zahradnice.cpp -o zahradnice -O3


SOKOWEB=http://www.sneezingtiger.com/sokoban/levels
SOKOFILES=picokosmosText.htm sasquatch5Text.htm

soko:
	cp programs/sokoban.cfg programs/soko.cfg
	for sokofile in ${SOKOFILES}; do \
    wget -N "${SOKOWEB}/$$sokofile"; \
	  grep "^Level\|#" "$$sokofile" > sokoban.txt; \
	  cat sokoban.txt \
      | sed 's/Level \([0-9]\+\)/\1/g' \
      | sed 's/^[^0-9].*//g' \
      | awk '{if($$1 != "") { a=$$1}; print a; }' > numbers.txt; \
	  paste numbers.txt sokoban.txt \
      | sed 's/^\([0-9]*\)\t\([^+@]*\)$$/~\1 \2/'\
      | sed 's/~[0-9] /~~~~/'\
      | sed 's/~[0-9][0-9] /~~~~~/'\
      | tr '#' 'X'  | sed 's/X/##/g' \
      | tr ' ' 'S'  | sed 's/S/  /g' \
      | tr '$$' 'b' | sed 's/b/st/g' \
      | tr '*' 'B'  | sed 's/B/ST/g' \
      | tr '.' 'C'  | sed 's/C/../g' \
      | tr '~' ' ' \
      | sed 's/^\([0-9]\+\)\t\([^@]*\)@/~\1@@\2@P/' \
      | sed 's/^\([0-9]\+\)\t\([^+]*\)+/~\1@@\2@:/' \
      | sed 's/  @P/~~@P/g' | sed 's/ @P/~@P/g' \
      | sed 's/^\s*\(Level.*\)$$/=\/TP/g' >> programs/soko.cfg; \
  done;\
  rm -f numbers.txt sokoban.txt 
  
