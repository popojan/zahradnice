#pragma once

#include <unordered_map>
#include <unordered_set>
#include <utility>
#include <string>
#include <fstream>
#include <streambuf>
#include <sstream>

#include <functional>
#include <utility>

struct hash_pair final {
    template<class TFirst, class TSecond>
    size_t operator()(const std::pair<TFirst, TSecond>& p) const noexcept {
        uintmax_t hash = std::hash<TFirst>{}(p.first);
        hash <<= sizeof(uintmax_t) * 4;
        hash ^= std::hash<TSecond>{}(p.second);
        return std::hash<uintmax_t>{}(hash);
    }
};

class ContextFreeGrammar2D {

public:  

  // non terminals
  std::unordered_set<char> V;
  struct Start {
    char ul; //vertical placement
    char lr; //horizontal placement
    char s; //symbol
  };

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
  };

  typedef std::vector<Rule> Rules;

  std::unordered_map<char, Rules> R;
  
  ContextFreeGrammar2D(char s, const std::string& nt)
  {
  }

  bool _process(const std::vector<std::string>& lhs, const std::string& rule) {
      std::for_each
      (
        lhs.begin(), lhs.end(),
        [this,&rule](auto& x)
        {
          addRule(x, rule); 
        }
      );
      return true;
  }
  void loadFromFile(const std::string& fname)
  {
    std::ifstream t(fname);
    std::string line;
    std::vector<std::string> lhs;
    std::ostringstream rule;

    while(std::getline(t, line))
    {
      
      if(line.size() > 0 && line.at(0) == '#') //comment
        continue;
      if(line.size() > 0 && line.at(0) == '^') //starting symbol
      {
        char s = line.size() > 1 ? line.at(1) : 's';
        char ul = line.size() > 2 ? line.at(2) : 'c';
        char lr = line.size() > 3 ? line.at(3) : 'c';
        S.push_back({ul, lr, s});
      }
      if(line.size() > 0 && line.at(0) == '=') //new rule LHSs
      {
        if(!rule.str().empty() && _process(lhs, rule.str())) {
          rule.str("");
          rule.clear();
          lhs.clear();
        }
        lhs.push_back(line);
      }
      else {
        rule << line << std::endl;
      }
    }
    if(!rule.str().empty())
      _process(lhs, rule.str());
    if(S.empty()) {
      S.push_back({'c', 'c', 's'});
    } 
  }
/*
  void addRuleFromFile(char lhs, const std::string& fname) {
    std::ifstream t(fname);
    std::string rhs((std::istreambuf_iterator<char>(t)),
      std::istreambuf_iterator<char>());
    addRule(lhs, rhs);
  }
*/
  std::pair<int, int> origin(char s, const std::string& rhs, char spec, int ord = 0) {
    int r = 0;
    int c = 0;

    for(const char * p = rhs.c_str(); *p != '\0'; ++p, ++c) {
      if(*p == '\n') {
        ++r;
        c = -1;
      }
      else if(*p == spec) {
        if(ord == 0) {
          return std::pair<int, int>(r, c);
        }
        --ord;
      }
    }
    return std::pair<int, int>(-1,-1);
  } 

  void addRule(const std::string& lhs, const std::string& rhs) {
    char s = lhs.at(1);
    if(R.find(s) == R.end()) {
      R[s] = Rules();
      V.insert(s);
    }
    Rule rule;
    auto o = origin(s, rhs, '@', 0);
    auto m = origin(s, rhs, '@', 1);
    auto q = origin(s, rhs, '@', 2);
    rule.lhsa = lhs;
    rule.lhs = s;
    rule.ro = o.first;
    rule.co = o.second;
    rule.rm = m.first;
    rule.cm = m.second;
    rule.rq = q.first;
    rule.cq = q.second;
    rule.rhs = rhs;
    char fore = 7; //default: white foreground
    char back = 8; //default: transparent background
    if(lhs.size() > 4) {
      fore = lhs.at(4) - '0';
    }
    if(lhs.size() > 5) {
      back = lhs.at(5) - '0';
    }
    rule.fore = fore;
    rule.back = back;
    int reward = -1; //default reward
    int weight = 1;
    rule.key = lhs.at(2);
    if(lhs.size() > 10) {
      std::istringstream iss(lhs.substr(10));
      iss >> reward;
      iss >> weight;
      if(weight < 1) weight = 1;
    }
    rule.reward = reward;
    rule.weight = weight;
    if(lhs.size() > 6)
      rule.ctx = lhs.at(6);
    else
      rule.ctx = -1;
    if(rule.ctx == '?')
      rule.ctx = -1;
      
    if(lhs.size() > 7)
      rule.ctxrep = lhs.at(7);
    else
      rule.ctxrep = ' ';

    if(lhs.size() > 8)
      rule.zord = lhs.at(8);
    else
      rule.zord = 'a';

    if(rule.ctxrep == '*') {
      rule.ctxrep = rule.lhs;
    }
    rule.rep = lhs.at(3);
    //std::replace(rule.rhs.begin(), rule.rhs.end(), '@', lhs.at(3));
    std::replace(rule.rhs.begin(), rule.rhs.end(), '*', rule.lhs);
    R[s].push_back(rule);
  }

  friend class Derivation;

};


class Derivation {
public:

  // active non terminal instance
  struct X {
    char s;
    int r;
    int c;
  };

  std::vector<X> x;

  struct G {
    char c;
    int flag;
    char fore;
    char back;
    char zord;
  };

  G * memory;

  Derivation(const ContextFreeGrammar2D& g, int row, int col)
   : g(g), col(col), row(row) {
    memory = new G[row*col];
    initColors();
    restart();
  } 

  void initColors() {
    char cols[8] = {
      COLOR_BLACK,
      COLOR_RED,
      COLOR_GREEN,
      COLOR_YELLOW,
      COLOR_BLUE,
      COLOR_MAGENTA,
      COLOR_CYAN,
      COLOR_WHITE
    };

    int N = sizeof(cols)/sizeof(char);

    int colidx = 1;

    for(int i = 0; i < N; ++i) {
      for(int j = 0; j < N; ++j) {
        colors[std::pair<char, char>(cols[i], cols[j])] = colidx;
        init_pair(colidx, cols[i], cols[j]);
        ++colidx;
      }
    }
  }

  ~Derivation() {
    delete [] memory;
  }
  void start() {
    std::for_each(g.S.begin(), g.S.end(), [this](auto s){
      int c = col/2;
      int r = row/2;
      if(s.lr == 'l') {
        c = 0;
      } else if(s.lr == 'r') {
        c = col - 1;
      }
      else {
        c = rand() % col;
      }
      if(s.ul == 'u') {
        r = 0;
      } else if(s.ul == 'l') {
        r = row - 1;
      }
      else  {
        r = rand() % row;
      }
      x.push_back({s.s, r, c});
      mvaddch(r, c, s.s);
    });
  }

  bool step(char key, int &score) {
    //random nonterminal instance

    //nonterminal alterable by rules from group key
    std::unordered_set<char> a;
    std::for_each(g.R.begin(), g.R.end(), [key,&a](auto rr){
      std::for_each(rr.second.begin(), rr.second.end(), [key,&a](auto rrr){
         if(rrr.key == key || rrr.key == '?') a.insert(rrr.lhs);
      });
    });

    std::vector<size_t> xx;
    for(auto nit = x.begin(); nit != x.end(); ++nit) {
      if(a.find(nit->s) != a.end())
          xx.push_back(nit - x.begin());
    }

    if(xx.size() <= 0)
      return 0;
    std::vector<std::pair<size_t, ContextFreeGrammar2D::Rule> > nr;
    for(auto nit = xx.begin(); nit != xx.end(); ++nit) {
      auto& n = x[*nit];
      auto res = g.R.find(n.s);
      if(res != g.R.end()) {
        //random rule
        auto rs = res->second;
        for(auto rit = rs.begin(); rit != rs.end(); ++rit) {
          if(rit->key == key || rit->key == '?') {
            if(dryapply(n.s, n.r - rit->ro, n.c - rit->co, *rit)) {
              for(int k = 0; k < rit->weight; ++k) {
                nr.push_back(std::pair<size_t, ContextFreeGrammar2D::Rule>(*nit, *rit));
              }
            }
          }
        }
      }
    }
    if(nr.size() > 0) {
      int j = random() % nr.size();
      auto rule = nr[j].second;
      auto n = x[nr[j].first];
      bool applied = apply(n.s, n.r - rule.rq, n.c - rule.cq, rule);
      if(applied) {
        mvprintw(0,0,rule.lhsa.c_str());
        x.erase(x.begin() + nr[j].first);
        score += rule.reward;
        return true;
      }
    }
    return false;
  }
  void restart() {
    x.clear();
    clear();
    for(int r = 0; r < row; ++r) {
      for(int c = 0; c < col; ++c) {
        memory[r*col + c] = {' ', 0, 7, 0, 'a'};
      }
    } 
  }

private:
  bool dryapply(char lhs, int ro, int co, const ContextFreeGrammar2D::Rule& rule) {
    int r = ro;
    int c = co;

    for(const char *p = rule.rhs.c_str(); *p != '\0'; ++p, ++c) {
      if(*p == '\n') {
        ++r;
        c = co - 1;
        continue;
      }
      if(rule.cq > rule.co && c - co >= rule.cm) // @ LHS @ >>RHS<<
        continue;

      if(rule.cq <= rule.co && r - ro >= rule.rm)
        break;

      char ctx = '#';
      if(r >= 0 && r < row && c >= 0 && c < col) {
        ctx = mvinch(r, c);
        if(ctx == ' ') ctx = '~';
      }
      if(*p != ' ') {
        char req = *p;
        if(req == '@')
          req = rule.lhs;
        if(req == ' ')
          req = '~';
        if((req != '!' && req != ctx) || (req == '!' && ctx == rule.ctx))
            return false;
      }
    }
    return true;
  }

  bool apply(char lhs, int ro, int co, const ContextFreeGrammar2D::Rule& rule) {
    int r = ro;
    int c = co;

    for(const char *p = rule.rhs.c_str(); *p != '\0'; ++p, ++c) {
      if(*p == '\n') {
        ++r;
        c = co - 1;
        continue;
      }
      if(rule.cq > rule.co && c - co <= rule.cm ) // @ LHS @ >>RHS<<
        continue;
      if(rule.cq <= rule.co && r - ro <= rule.rm)
        continue;
      G saved = {' ', 0, 7, 8, 'a'};
      char rep = *p;
      if(rep == '@')
        rep = rule.rep;
      bool isNonTerminal = g.V.find(rep) != g.V.end();
      if(rep != ' ' && r >= 0 && r < row && c >= 0 && c < col) {
        if(rep == '~')
          rep = ' ';
  
        int flag = 0;
 
        char back = rule.back;

        // transparent background; take background from memory
        if(rule.back > 7) {
          back = memory[col * r + c].back;
        } 
        // to be saved in memory

        G d = {rep, flag, rule.fore, back, rule.zord};

        // special char: restore from memory
        if(rep == '$') d = memory[col * r + c];

        // memory empty
        if(d.c == -1) d = {' ', flag, rule.fore, back, 'a'};

        int cidx = getColor(d.fore, d.back);

        if(rule.zord >= memory[col*r + c].zord) {
          if(cidx > 0) {
            attron(COLOR_PAIR(cidx));
          }
        
            mvaddch(r, c, d.c | d.flag);
          if(!isNonTerminal) {
            //terminal symbol: save all
            saved = d;
          } else {
            //nonterminal symbol: replace bg color if any 
            saved = memory[col * r + c];
          }
          if(cidx > 0)
            attroff(COLOR_PAIR(cidx));
            memory[col * r + c] = saved;
        } 
        if (isNonTerminal) {
          x.push_back({rep, r, c});
        }
      }
    }
    return true;
  }

  int getColor(char fore, char back) {
    auto cit = colors.find(std::pair<char, char>(fore, back));
    if(cit != colors.end())
      return cit->second;
    return -1;
  }
  const ContextFreeGrammar2D& g;
  int col, row;
  std::unordered_map< std::pair<char, char>, int, hash_pair> colors;
};
