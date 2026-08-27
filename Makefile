CXX = g++
STD = -std=c++20
ENGINE_SRCS = src/zahradnice.cpp src/sample.cpp src/display_curses.cpp
ENGINE_LIBS = -lz -lncursesw -lSDL2_mixer

SIZE_FLAGS = -Os -ffunction-sections -fdata-sections -fno-exceptions -fno-rtti -fmerge-all-constants -flto
SIZE_LDFLAGS = -Wl,--gc-sections

all: zahradnice-speed

# --- libgrammar.a: parser + rule engine, shared with future tools ---
# One archive per build mode so LTO can fold across the boundary in size builds.

build:
	@mkdir -p build

build/grammar-speed.o: src/grammar.cpp src/grammar.h src/display.h | build
	$(CXX) $(STD) -O3 -c $< -o $@
build/grammar-debug.o: src/grammar.cpp src/grammar.h src/display.h | build
	$(CXX) $(STD) -O2 -g -c $< -o $@
build/grammar-size.o: src/grammar.cpp src/grammar.h src/display.h | build
	$(CXX) $(STD) $(SIZE_FLAGS) -c $< -o $@

build/display_headless-speed.o: src/display_headless.cpp src/display_headless.h src/display.h | build
	$(CXX) $(STD) -O3 -c $< -o $@
build/display_headless-debug.o: src/display_headless.cpp src/display_headless.h src/display.h | build
	$(CXX) $(STD) -O2 -g -c $< -o $@
build/display_headless-size.o: src/display_headless.cpp src/display_headless.h src/display.h | build
	$(CXX) $(STD) $(SIZE_FLAGS) -c $< -o $@

build/status-speed.o: src/status.cpp src/status.h src/grammar.h | build
	$(CXX) $(STD) -O3 -c $< -o $@
build/status-debug.o: src/status.cpp src/status.h src/grammar.h | build
	$(CXX) $(STD) -O2 -g -c $< -o $@
build/status-size.o: src/status.cpp src/status.h src/grammar.h | build
	$(CXX) $(STD) $(SIZE_FLAGS) -c $< -o $@

build/headless_runner-speed.o: src/headless_runner.cpp src/headless_runner.h src/display_headless.h src/grammar.h src/status.h | build
	$(CXX) $(STD) -O3 -c $< -o $@
build/headless_runner-debug.o: src/headless_runner.cpp src/headless_runner.h src/display_headless.h src/grammar.h src/status.h | build
	$(CXX) $(STD) -O2 -g -c $< -o $@
build/headless_runner-size.o: src/headless_runner.cpp src/headless_runner.h src/display_headless.h src/grammar.h src/status.h | build
	$(CXX) $(STD) $(SIZE_FLAGS) -c $< -o $@

build/libgrammar-speed.a: build/grammar-speed.o build/display_headless-speed.o build/status-speed.o build/headless_runner-speed.o
	ar rcs $@ $^
build/libgrammar-debug.a: build/grammar-debug.o build/display_headless-debug.o build/status-debug.o build/headless_runner-debug.o
	ar rcs $@ $^
build/libgrammar-size.a: build/grammar-size.o build/display_headless-size.o build/status-size.o build/headless_runner-size.o
	ar rcs $@ $^

# --- libgenlib.a: authoring-time helpers for generators (no engine deps) ---

build/genlib.o: src/gen/genlib.cpp src/gen/genlib.h | build
	$(CXX) $(STD) -O2 -c $< -o $@

build/libgenlib.a: build/genlib.o
	ar rcs $@ $<

# --- Generator binaries (separate from engine targets) ---

build/animation_gen.o: src/gen/animation_gen.cpp src/gen/genlib.h | build
	$(CXX) $(STD) -O2 -c $< -o $@

build/animation_gen: build/animation_gen.o build/libgenlib.a
	$(CXX) $(STD) -O2 $^ -o $@

build/walker_gen.o: src/gen/walker_gen.cpp src/gen/genlib.h | build
	$(CXX) $(STD) -O2 -c $< -o $@

build/walker_gen: build/walker_gen.o build/libgenlib.a
	$(CXX) $(STD) -O2 $^ -o $@

# --- engine ---

zahradnice-speed: build/libgrammar-speed.a
	$(CXX) $(STD) -O3 -s $(ENGINE_SRCS) $< -o zahradnice $(ENGINE_LIBS)

zahradnice-debug: build/libgrammar-debug.a
	$(CXX) $(STD) -O2 -g $(ENGINE_SRCS) $< -o zahradnice $(ENGINE_LIBS)

zahradnice-size: build/libgrammar-size.a
	$(CXX) $(STD) $(SIZE_FLAGS) $(SIZE_LDFLAGS) -s $(ENGINE_SRCS) $< -o zahradnice $(ENGINE_LIBS)
	strip ./zahradnice -R .comment -R .gnu.version --strip-unneeded

# --- zahradnice-headless: curses-free build, validates the seam ---
# Links libgrammar + headless main only; no ncurses, no SDL2_mixer, no
# zahradnice.cpp. Not in `make install` — architectural validation only.

zahradnice-headless: build/libgrammar-size.a src/headless_main.cpp
	$(CXX) $(STD) $(SIZE_FLAGS) $(SIZE_LDFLAGS) -s src/headless_main.cpp build/libgrammar-size.a -o zahradnice-headless -lz
	strip ./zahradnice-headless -R .comment -R .gnu.version --strip-unneeded

# --- zahradnice-check: validation/inspection tool, links libgrammar.a ---

build/check.o: src/check/check.cpp src/grammar.h | build
	$(CXX) $(STD) -O2 -c $< -o $@

zahradnice-check: build/check.o build/libgrammar-speed.a
	$(CXX) $(STD) -O2 $^ -o $@ -lncursesw -lz

clean:
	rm -rf build zahradnice

# --- regression tests ---
# `make test` runs all three suites: the headless screen dumps below, then
# the two that need the curses binary and a pty — idle CPU, and menus
# remembering which entry you left through.
#
# Screen dumps: tests/<prog>/<case>.input + tests/<prog>/<case>.expected.
# <prog> resolves to programs/<prog>/index.cfg if it's a directory,
# otherwise programs/<prog>.cfg. Optional sidecar tests/<prog>/<case>.seed
# overrides the default --seed 1. Compares plain-text screen dumps with
# `diff -u`; non-zero exit on any mismatch. `make update-tests` rewrites
# the .expected files in place — review the diff before committing.

TESTS := $(shell find tests -name '*.input' 2>/dev/null | sort)

.PHONY: test test-dumps test-idle test-menu update-tests

test: test-dumps test-idle test-menu

# The engine must sleep when the screen cannot change, and only then:
# see tests/idle_cpu.py. Takes ~15s of wall clock, most of it waiting.
test-idle: zahradnice
	@python3 tests/idle_cpu.py ./zahradnice

# A menu must come back with the entry you left through: see
# tests/menu_memory.py. Drives the real binary; ~25s, mostly waiting.
test-menu: zahradnice
	@python3 tests/menu_memory.py ./zahradnice

test-dumps: zahradnice-headless
	@pass=0; fail=0; tmp=$$(mktemp); trap 'rm -f $$tmp' EXIT; \
	for t in $(TESTS); do \
	  base=$${t%.input}; \
	  prog=$$(echo "$$t" | cut -d/ -f2); \
	  name=$$(basename "$$base"); \
	  if [ -f "programs/$$prog/$$name.cfg" ]; then cfg="programs/$$prog/$$name.cfg"; \
	  elif [ -f "$$prog/$$name.cfg" ]; then cfg="$$prog/$$name.cfg"; \
	  elif [ -d "programs/$$prog" ]; then cfg="programs/$$prog/index.cfg"; \
	  else cfg="programs/$$prog.cfg"; fi; \
	  seed=1; [ -f "$$base.seed" ] && seed=$$(cat "$$base.seed"); \
	  ./zahradnice-headless "$$cfg" --seed "$$seed" --threads 4 \
	    --input "@$$t" --dump-screen -.txt 2>/dev/null > $$tmp; \
	  if diff -u "$$base.expected" $$tmp >/dev/null; then \
	    echo "PASS $$base"; pass=$$((pass+1)); \
	  else \
	    echo "FAIL $$base"; fail=$$((fail+1)); \
	    diff -u "$$base.expected" $$tmp || true; \
	  fi; \
	done; \
	echo "----"; echo "$$pass passed, $$fail failed"; \
	[ $$fail -eq 0 ]

update-tests: zahradnice-headless
	@for t in $(TESTS); do \
	  base=$${t%.input}; \
	  prog=$$(echo "$$t" | cut -d/ -f2); \
	  name=$$(basename "$$base"); \
	  if [ -f "programs/$$prog/$$name.cfg" ]; then cfg="programs/$$prog/$$name.cfg"; \
	  elif [ -f "$$prog/$$name.cfg" ]; then cfg="$$prog/$$name.cfg"; \
	  elif [ -d "programs/$$prog" ]; then cfg="programs/$$prog/index.cfg"; \
	  else cfg="programs/$$prog.cfg"; fi; \
	  seed=1; [ -f "$$base.seed" ] && seed=$$(cat "$$base.seed"); \
	  ./zahradnice-headless "$$cfg" --seed "$$seed" --threads 4 \
	    --input "@$$t" --dump-screen -.txt 2>/dev/null > "$$base.expected"; \
	  echo "wrote $$base.expected"; \
	done

# --- release packaging (unchanged) ---

RELEASE_DIR=release
release:
	mkdir -p ${RELEASE_DIR}/zahradnice/programs
	cp index.cfg ${RELEASE_DIR}/zahradnice
	cp -R programs/*.cfg programs/sokoban programs/primes ${RELEASE_DIR}/zahradnice/programs
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
