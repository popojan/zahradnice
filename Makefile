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
      | sed 's/^/   /'\
      | tr '#' 'X'  | sed 's/X/##/g' \
      | tr ' ' 'S'  | sed 's/S/  /g' \
      | tr '$$' 'b' | sed 's/b/st/g' \
      | tr '*' 'B'  | sed 's/B/ST/g' \
      | tr '.' 'C'  | sed 's/C/../g' \
      | sed 's/^   \([^@]*\)@/@@ \1@P/' \
      | sed 's/^   \([^+]*\)+/@@ \1@:/' \
      | sed 's/^\s*\(Level.*\)$$/=2TP/g' >> programs/soko.cfg; \
  done;
