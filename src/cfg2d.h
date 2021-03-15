#pragma once

#include <unordered_map>
#include <unordered_set>
#include <utility>
#include <string>
#include <fstream>
#include <streambuf>
#include <sstream>

class ContextFreeGrammar2D {

public:  

  // non terminals
  std::unordered_set<char> V;

  // terminals
  // ... any ASCII char not in nonterminal

  // starting symbol
  struct Rule {
    char lhs;
    std::string rhs;
    int ro;
    int co;
    int rq;
    int cq;
    int extra;
    int reward;
    char key;
    char ctx;
    char ctxrep;
    int weight;
  };

  char S;

  typedef std::vector<Rule> Rules;

  std::unordered_map<char, Rules> R;

  ContextFreeGrammar2D(char s, const std::string& nt):
  S(s), numColors(1) {
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
  }
/*
  void addRuleFromFile(char lhs, const std::string& fname) {
    std::ifstream t(fname);
    std::string rhs((std::istreambuf_iterator<char>(t)),
      std::istreambuf_iterator<char>());
    addRule(lhs, rhs);
  }
*/
  std::pair<int, int> origin(char s, const std::string& rhs, char spec = '@') {
    int r = 0;
    int c = 0;
    for(const char * p = rhs.c_str(); *p != '\0'; ++p, ++c) {
      if(*p == '\n') {
        ++r;
        c = -1;
      }
      else if(*p == spec) {
        return std::pair<int, int>(r, c);
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
    auto o = origin(s, rhs, '@');
    auto q = origin(s, rhs, '&');
    rule.lhs = s;
    rule.ro = o.first;
    rule.co = o.second;
    rule.rq = q.first;
    rule.cq = q.second;
    rule.rhs = rhs;
    char fore = 0;
    char back = 0;
    char colidx = 0;
    if(lhs.size() > 4) {
      fore = lhs.at(4) - '0';
    }
    if(lhs.size() > 5) {
      back = lhs.at(5) - '0';
    }
    if(fore > 0 || back > 0) {
      colidx = numColors;
      init_pair(colidx, fore, back);
      ++numColors;
    }
    int reward = 0;
    int weight = 1;
    rule.key = lhs.at(2);
    if(lhs.size() > 9) {
      std::istringstream iss(lhs.substr(9));
      iss >> reward;
      iss >> weight;
      if(weight < 1) weight = 1;
    }
    rule.reward = reward;
    rule.weight = weight;
    rule.extra = colidx;
    if(lhs.size() > 6)
     rule.ctx = lhs.at(6);
    else
     rule.ctx = -1;
    if(lhs.size() > 7)
     rule.ctxrep = lhs.at(7);
    else
     rule.ctxrep = ' ';

    std::replace(rule.rhs.begin(), rule.rhs.end(), '@', lhs.at(3));
    std::replace(rule.rhs.begin(), rule.rhs.end(), '&', rule.ctxrep);
    R[s].push_back(rule);
  }

  friend class Derivation;
  int numColors;  

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

  Derivation(const ContextFreeGrammar2D& g, int row, int col)
   : g(g), col(col), row(row) { } 

  void start(int r, int c) {
    x.push_back({g.S, r, c});
    mvaddch(r, c, g.S);
  }

  int step(char key) {
    //random nonterminal instance

    //nonterminal alterable by rules from group key
    std::unordered_set<char> a;
    std::for_each(g.R.begin(), g.R.end(), [key,&a](auto rr){
      std::for_each(rr.second.begin(), rr.second.end(), [key,&a](auto rrr){
         if(rrr.key == key) a.insert(rrr.lhs);
      });
    });

    std::vector<size_t> xx;
    for(auto nit = x.begin(); nit != x.end(); ++nit) {
      if(a.find(nit->s) != a.end())
          xx.push_back(nit - x.begin());
    }

    if(xx.size() <= 0)
      return 0;
    int i = random() % xx.size();
    auto& n = x[xx[i]];
    auto res = g.R.find(n.s);
    if(res != g.R.end()) {
      //random rule
      auto rs = res->second;
      std::vector<ContextFreeGrammar2D::Rule> r;
      for(auto rit = rs.begin(); rit != rs.end(); ++rit) {
        if(rit->key == key) {
            char ctx = mvinch(n.r - rit->ro + rit->rq, n.c - rit->co + rit->cq);
            if(rit->ctx == -1 
               || ctx == rit->ctx) {
            for(int k = 0; k < rit->weight; ++k) {
                r.push_back(*rit);
            }
          }
        }
      }
      if(r.size() > 0) {
        int j = random() % r.size();
        auto rule = r[j];
        bool applied = apply(n.s, n.r - rule.ro, n.c - rule.co, rule);
        if(applied) {
          x.erase(x.begin() + xx[i]);
          return rule.reward;
        }
      }
    }
    return 0;
  }
  void restart() {
    x.clear();
    clear();
  }

private:

  bool apply(char lhs, int ro, int co, const ContextFreeGrammar2D::Rule& rule) {
    int r = ro;
    int c = co;

    for(const char *p = rule.rhs.c_str(); *p != '\0'; ++p, ++c) {
      if(*p == '\n') {
        ++r;
        c = co - 1;
        continue;
      }
      if((*p != ' ' || (r - ro == rule.ro && c- co == rule.co) ) 
        && r >= 0 && r < row && c >= 0 && c < col) {

        int flag = 0;
 
        if(rule.extra > 0) {
          attron(COLOR_PAIR(rule.extra));
        }
       
        mvaddch(r, c, *p | flag);
        if(rule.extra > 0)
          attroff(COLOR_PAIR(rule.extra));
   
      }
      if(r >= 0 && r < row && c >= 0 && c < col) {
        if (g.V.find(*p) != g.V.end()) {
          x.push_back({*p, r, c});
        }
      }
    }
    return true;
  }

  const ContextFreeGrammar2D& g;
  int col, row;
};
