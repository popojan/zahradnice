all: zahradnice-speed

zahradnice-speed:
	g++ -std=c++20 -lz -lncursesw -lSDL2_mixer src/zahradnice.cpp src/grammar.cpp src/sample.cpp -o zahradnice -O3 -s

zahradnice-debug:
	g++ -std=c++20 -lz -lncursesw -lSDL2_mixer src/zahradnice.cpp src/grammar.cpp src/sample.cpp -o zahradnice -O2 -g

zahradnice-size:
	g++ -std=c++20 -lz -lncursesw -lSDL2_mixer src/zahradnice.cpp src/grammar.cpp src/sample.cpp -o zahradnice -Os -s \
   -ffunction-sections -fdata-sections -Wl,--gc-sections -fno-exceptions -fno-rtti -fmerge-all-constants -flto
	strip ./zahradnice -R .comment -R .gnu.version --strip-unneeded

RELEASE_DIR=release
release:
	mkdir -p ${RELEASE_DIR}/zahradnice/programs
	gzip -k programs/*.cfg
	gzip -k index.cfg
	mv index.cfg.gz ${RELEASE_DIR}/zahradnice
	mv programs/*.cfg.gz ${RELEASE_DIR}/zahradnice/programs
	#mkdir -p ${RELEASE_DIR}/zahradnice/sounds
	#cp sounds/*.wav ${RELEASE_DIR}/zahradnice/sounds
	cp zahradnice ${RELEASE_DIR}/zahradnice
	cd ${RELEASE_DIR}; \
	tar -czf zahradnice.tar.gz zahradnice/

SOKOWEB=http://www.sneezingtiger.com/sokoban/levels
SOKOFILES=picokosmosText.html #sasquatch5Text.html

soko:
	cp programs/partial/sokoban.cfg programs/sokoban.cfg
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
      | sed 's/  @:/~~@:/g' | sed 's/ @:/~@:/g' \
      | sed 's/^\s*\(Level.*\)$$/==\/TP/g' >> programs/sokoban.cfg; \
  done;\
  rm -f numbers.txt sokoban.txt

