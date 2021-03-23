all: zahr

zahr:
	g++ -std=c++14 -lncurses src/zahradnice.cpp -o zahradnice -O3

