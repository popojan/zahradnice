#pragma once

#include <unordered_map>
#include <unordered_set>
#include <utility>
#include <string>
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
  };

  char S;

  typedef std::vector<Rule> Rules;

  std::unordered_map<char, Rules> R;

  ContextFreeGrammar2D(char s, const std::string& nt):
  S(s) {
  }

  bool _process(const std::vector<std::pair<char,char> >& lhs, const std::string& rule) {
      if(!rule.empty() && lhs.size() > 0)
      {
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
      return false;
  }
  void loadFromFile(const std::string& fname)
  {
    std::ifstream t(fname);
    std::string line;
    std::vector<std::pair<char,char> > lhs;
    std::ostringstream rule;

    while(std::getline(t, line))
    {
      
      if(line.size() > 0 && line.at(0) == '#') //comment
        continue;
      if(line.size() > 0 && line.at(0) == '=') //new rule LHSs
      {
       if(_process(lhs, rule.str())) {
          rule.str("");
          rule.clear();
          lhs.clear();
        }
        lhs.push_back(std::make_pair(line.at(1), line.at(3)));
      }
      else {
        rule << line << std::endl;
      }
    }
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
  std::pair<int, int> origin(char s, const std::string& rhs) {
    int r = 0;
    int c = 0;
    for(const char * p = rhs.c_str(); *p != '\0'; ++p, ++c) {
      if(*p == '\n') {
        ++r;
        c = -1;
      }
      else if(*p == '@') {
        return std::pair<int, int>(r, c);
      }
    }
    return std::pair<int, int>(-1,-1);
  } 

  void addRule(std::pair<char, char> lhs, const std::string& rhs) {
    if(R.find(lhs.first) == R.end()) {
      R[lhs.first] = Rules();
      V.insert(lhs.first);
    }
    Rule rule;
    rule.lhs = lhs.first;
    auto o = origin(lhs.first, rhs);
    rule.ro = o.first;
    rule.co = o.second;
    rule.rhs = rhs;
    std::replace(rule.rhs.begin(), rule.rhs.end(), '@', lhs.second);
    R[lhs.first].push_back(rule);
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
        bool applied = apply(n.s, n.r - rule.ro, n.c - rule.co, rule);
        if(applied) {
          x.erase(x.begin() + i);
        }
      }
    }
  }

private:

  bool apply(char lhs, int ro, int co, const ContextFreeGrammar2D::Rule& rule) {
    if(ro < 0 || co < 0)
      return false;
    int r = ro;
    int c = co;

    for(const char *p = rule.rhs.c_str(); *p != '\0'; ++p, ++c) {
      if(*p == '\n') {
        ++r;
        c = co - 1;
        continue;
      }
      if(*p != ' ') {
        mvaddch(r, c, *p);
      }
      if (g.V.find(*p) != g.V.end()) {
        x.push_back({*p, r, c});
      }
    }
    return true;
  }

  const ContextFreeGrammar2D& g;
  
};
