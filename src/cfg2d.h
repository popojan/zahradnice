#pragma once

#include <unordered_map>
#include <unordered_set>
#include <utility>
#include <string>

class ContextFreeGrammar2D {

public:  

  // non terminals
  std::unordered_set<char> V;

  // terminals
  // ... any ASCII char not in nonterminal

  // starting symbol
  char S;

  typedef std::vector<std::string> Rules;

  std::unordered_map<char, Rules> R;

  ContextFreeGrammar2D(char s, const std::string& nt):
  S(s) {
    for(const char* p = nt.c_str(); *p != '\0'; ++p) {
      V.insert(*p);
    }
  }

  void addRule(char lhs, const std::string& rhs) {
    if(R.find(lhs) == R.end())
      R[lhs] = Rules();
    R[lhs].push_back(rhs);
  }


  friend class Derivation;

};


class Derivation {
public:
  // LHS nonterminal uppercased
  // RHS nonterminal lowercased
  const char R2LD = 0x20;

  // active non terminal instance
  struct X {
    char s;
    int r;
    int c;
  };

  std::vector<X> x;

  Derivation(const ContextFreeGrammar2D& g)
   : g(g) { } 

  void start(int r, int c) {
    x.push_back({g.S, r, c});
  }

  void step() {
    //random nonterminal instance
    int i = random() % x.size();
    auto& n = x[i];
    auto res = g.R.find(n.s);
    if(res != g.R.end()) {
      //random rule
      auto r = res->second;
      if(r.size() > 0) {
        int j = random() % r.size();
        auto rule = r[j];
        auto o = origin(n.s, rule);
        bool applied = apply(n.s, n.r - o.first, n.c - o.second, rule);
        if(applied) {
          x.erase(x.begin() + i);
        }
      }
    }
  }

private:
  std::pair<int, int> origin(char s, const std::string& rhs) {
    int r = 0;
    int c = 0;
    for(const char * p = rhs.c_str() + 2; *p != '\0'; ++p, ++c) {
      if(*p == '\n') {
        ++r;
        c = -1;
      }
      else if(*p == s - R2LD) {
        return std::pair<int, int>(r, c);
      }
    }
    return std::pair<int, int>(-1,-1);
  } 

  bool apply(char lhs, int ro, int co, const std::string& rhs) {
    if(ro < 0 || co < 0)
      return false;
    int r = ro;
    int c = co;

    const char * p = rhs.c_str();

    int hack = *p; //char in place of LHS

    for(p += 2; *p != '\0'; ++p, ++c) {
      if(*p == '\n') {
        ++r;
        c = co - 1;
        continue;
      }
      char d = *p;
      if(lhs - R2LD == d) {
        d = hack;
      } 
      if(d != ' ') {
        mvaddch(r, c, d);
      }
      if (g.V.find(d) != g.V.end()) {
        x.push_back({d, r, c});
      }
    }
    return true;
  }

  ContextFreeGrammar2D g;
  
};
