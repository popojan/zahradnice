CXX = g++
STD = -std=c++20
ENGINE_SRCS = src/zahradnice.cpp src/sample.cpp
ENGINE_LIBS = -lz -lncursesw -lSDL2_mixer

SIZE_FLAGS = -Os -ffunction-sections -fdata-sections -fno-exceptions -fno-rtti -fmerge-all-constants -flto
SIZE_LDFLAGS = -Wl,--gc-sections

all: zahradnice-speed

# --- libgrammar.a: parser + rule engine, shared with future tools ---
# One archive per build mode so LTO can fold across the boundary in size builds.

build:
	@mkdir -p build

build/grammar-speed.o: src/grammar.cpp src/grammar.h | build
	$(CXX) $(STD) -O3 -c $< -o $@
build/grammar-debug.o: src/grammar.cpp src/grammar.h | build
	$(CXX) $(STD) -O2 -g -c $< -o $@
build/grammar-size.o: src/grammar.cpp src/grammar.h | build
	$(CXX) $(STD) $(SIZE_FLAGS) -c $< -o $@

build/libgrammar-speed.a: build/grammar-speed.o
	ar rcs $@ $<
build/libgrammar-debug.a: build/grammar-debug.o
	ar rcs $@ $<
build/libgrammar-size.a: build/grammar-size.o
	ar rcs $@ $<

# --- libgenlib.a: authoring-time helpers for generators (no engine deps) ---

build/genlib.o: src/gen/genlib.cpp src/gen/genlib.h | build
	$(CXX) $(STD) -O2 -c $< -o $@

build/libgenlib.a: build/genlib.o
	ar rcs $@ $<

# --- Generator binaries (separate from engine targets) ---

build/tetris_gen.o: src/gen/tetris_gen.cpp src/gen/genlib.h | build
	$(CXX) $(STD) -O2 -c $< -o $@

build/tetris_gen: build/tetris_gen.o build/libgenlib.a
	$(CXX) $(STD) -O2 $^ -o $@

# Regenerate tetris2 from source.
gen-tetris: build/tetris_gen
	./build/tetris_gen > programs/tetris2/tetris.cfg

build/animation_gen.o: src/gen/animation_gen.cpp src/gen/genlib.h | build
	$(CXX) $(STD) -O2 -c $< -o $@

build/animation_gen: build/animation_gen.o build/libgenlib.a
	$(CXX) $(STD) -O2 $^ -o $@

# --- engine ---

zahradnice-speed: build/libgrammar-speed.a
	$(CXX) $(STD) -O3 -s $(ENGINE_SRCS) $< -o zahradnice $(ENGINE_LIBS)

zahradnice-debug: build/libgrammar-debug.a
	$(CXX) $(STD) -O2 -g $(ENGINE_SRCS) $< -o zahradnice $(ENGINE_LIBS)

zahradnice-size: build/libgrammar-size.a
	$(CXX) $(STD) $(SIZE_FLAGS) $(SIZE_LDFLAGS) -s $(ENGINE_SRCS) $< -o zahradnice $(ENGINE_LIBS)
	strip ./zahradnice -R .comment -R .gnu.version --strip-unneeded

clean:
	rm -rf build zahradnice

# --- release packaging (unchanged) ---

RELEASE_DIR=release
release:
	mkdir -p ${RELEASE_DIR}/zahradnice/programs
	cp index.cfg ${RELEASE_DIR}/zahradnice
	cp -R programs/*.cfg programs/sokoban ${RELEASE_DIR}/zahradnice/programs
	cp zahradnice ${RELEASE_DIR}/zahradnice
	cd ${RELEASE_DIR}; \
	tar -czf zahradnice.tar.gz zahradnice/; \
	cd ..
	mkdir -p ${RELEASE_DIR}/zahradnice/sounds
	cp sounds/*.wav ${RELEASE_DIR}/zahradnice/sounds
	cd ${RELEASE_DIR}; \
	tar -czf zahradnice-sounds.tar.gz zahradnice/sounds; \
	rm -rf zahradnice

# --- sokoban level scrape (unchanged) ---

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
