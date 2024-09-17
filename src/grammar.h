#pragma once

#include <climits>
#include <unordered_map>
#include <unordered_set>
#include <string>
#include <fstream>
#include <sstream>

#include <functional>
#include <vector>
#include <algorithm>
#include <cstdint>

struct hash_pair final {
    template<class TFirst, class TSecond>
    size_t operator()(const std::pair<TFirst, TSecond>& p) const noexcept {
        uintmax_t hash = std::hash<TFirst>{}(p.first);
        hash <<= sizeof(uintmax_t) * 4;
        hash ^= std::hash<TSecond>{}(p.second);
        return std::hash<uintmax_t>{}(hash);
    }
};

class Grammar2D {

public:

  // non terminals
  std::unordered_set<char> V;
  struct Start {
    char ul; //vertical placement
    char lr; //horizontal placement
    char s; //symbol
  };

  std::string help;

  std::vector<Start> S;

  // terminals
  // ... any ASCII char not in nonterminal

  // starting symbol
  struct Rule {
    char lhs;
    std::string lhsa;
    std::string rhs;
    int ro;
    int co;
    int rm;
    int cm;
    int rq;
    int cq;
    char fore;
    char back;
    int reward;
    char key;
    char ctx;
    char rep;
    char ctxrep;
    int weight;
    char zord;
    char sound;
  };

  typedef std::vector<Rule> Rules;
  std::unordered_set<char> sounds;

  std::unordered_map<char, Rules> R;
  std::unordered_map<char, std::string> dict;

  Grammar2D()
  {
  }

  bool _process(const std::vector<std::string>& lhs, const std::string& rule);
  void loadFromFile(const std::string& fname);

  std::pair<int, int> origin(char s, const std::string& rhs, char spec, int ord = 0);

  void addRule(const std::string& lhs, const std::string& rhs);

  friend class Derivation;
private:
  char getColor(char val, char def);
};


class Derivation {
public:

  std::unordered_map< std::pair<int, int>, char, hash_pair> x;

  struct G {
    char c;
    char fore;
    char back;
    char zord;
  };

  G * memory;

  Derivation();

  void reset(const Grammar2D& g, int row, int col);
  void init();

  void initColors();

  ~Derivation();

  void start();

  bool step(char key, int &score, Grammar2D::Rule* dbgrule, int &errs);

  void restart();

private:

  bool dryapply(int ro, int co, const Grammar2D::Rule& rule);

  bool apply(int ro, int co, const Grammar2D::Rule& rule);

  int getColor(char fore, char back);

  Grammar2D g;
  int col, row;
  std::unordered_map< std::pair<char, char>, int, hash_pair> colors;
};
