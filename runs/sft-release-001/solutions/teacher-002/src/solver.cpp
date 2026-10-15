// CVRPTW baseline solver: Nearest-Neighbor construction with Push-Forward
// time-window feasibility check. Approx. 240 lines, no third-party deps.
//
// Build:  make
// Run :   ./cvrptw_solver <input.txt> <output.txt> <time_budget_sec>
//
// This is a deliberately simple baseline. Agents are expected to replace
// or extend it with stronger metaheuristics (ALNS, SISR, Tabu, etc.).

#include "../include/types.h"

#include <algorithm>
#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <iostream>
#include <limits>
#include <sstream>
#include <string>
#include <tuple>
#include <vector>
#include <random>
#include <cmath>
#include <numeric>

using namespace cvrptw;
using Clock = std::chrono::steady_clock;

// ---------- IO ----------

static bool starts_with(const std::string& s, const char* p) {
    return s.compare(0, std::strlen(p), p) == 0;
}

static Instance parse_input(const std::string& path) {
    std::ifstream in(path);
    if (!in) {
        std::fprintf(stderr, "ERROR: cannot open input file: %s\n", path.c_str());
        std::exit(2);
    }
    Instance inst;
    int dim = 0;
    std::string line;
    enum Section { NONE, COORD, DEMAND, TW, SVC, DEPOT } sec = NONE;
    std::vector<std::tuple<int, double, double>> coords;
    std::vector<std::pair<int, int>> demands;
    std::vector<std::tuple<int, double, double>> tws;
    std::vector<std::pair<int, double>> svcs;
    while (std::getline(in, line)) {
        // strip trailing \r
        while (!line.empty() && (line.back() == '\r' || line.back() == ' ' || line.back() == '\t'))
            line.pop_back();
        if (line.empty() || starts_with(line, "EOF")) continue;
        if (starts_with(line, "NAME")) {
            auto pos = line.find(':');
            if (pos != std::string::npos) {
                inst.name = line.substr(pos + 1);
                while (!inst.name.empty() && inst.name.front() == ' ') inst.name.erase(inst.name.begin());
            }
            continue;
        }
        if (starts_with(line, "DIMENSION")) {
            auto pos = line.find(':');
            dim = std::atoi(line.c_str() + pos + 1);
            continue;
        }
        if (starts_with(line, "CAPACITY")) {
            auto pos = line.find(':');
            inst.capacity = std::atoi(line.c_str() + pos + 1);
            continue;
        }
        if (starts_with(line, "MAX_VEHICLES")) {
            auto pos = line.find(':');
            inst.max_vehicles = std::atoi(line.c_str() + pos + 1);
            continue;
        }
        if (starts_with(line, "EDGE_WEIGHT_TYPE")) continue;
        if (starts_with(line, "NODE_COORD_SECTION"))  { sec = COORD;  continue; }
        if (starts_with(line, "DEMAND_SECTION"))      { sec = DEMAND; continue; }
        if (starts_with(line, "TIME_WINDOW_SECTION")) { sec = TW;     continue; }
        if (starts_with(line, "SERVICE_TIME_SECTION")){ sec = SVC;    continue; }
        if (starts_with(line, "DEPOT_SECTION"))       { sec = DEPOT;  continue; }
        std::istringstream iss(line);
        if (sec == COORD) {
            int id; double x, y;
            if (iss >> id >> x >> y) coords.emplace_back(id, x, y);
        } else if (sec == DEMAND) {
            int id, q;
            if (iss >> id >> q) demands.emplace_back(id, q);
        } else if (sec == TW) {
            int id; double e, l;
            if (iss >> id >> e >> l) tws.emplace_back(id, e, l);
        } else if (sec == SVC) {
            int id; double s;
            if (iss >> id >> s) svcs.emplace_back(id, s);
        }
        // DEPOT section: ignored, we always assume depot id == 0
    }
    if (dim <= 0) { std::fprintf(stderr, "ERROR: missing DIMENSION\n"); std::exit(2); }
    inst.nodes.assign(dim, Node{});
    inst.n_customers = dim - 1;
    for (auto& [id, x, y] : coords) {
        if (id < 0 || id >= dim) continue;
        inst.nodes[id].id = id;
        inst.nodes[id].x  = x;
        inst.nodes[id].y  = y;
    }
    for (auto& [id, q]    : demands) if (id >= 0 && id < dim) inst.nodes[id].demand = q;
    for (auto& [id, e, l] : tws)     if (id >= 0 && id < dim) { inst.nodes[id].e = e; inst.nodes[id].l = l; }
    for (auto& [id, s]    : svcs)    if (id >= 0 && id < dim) inst.nodes[id].s = s;
    return inst;
}

static void write_output(const std::string& path, const Solution& sol) {
    std::ofstream out(path);
    if (!out) {
        std::fprintf(stderr, "ERROR: cannot open output file: %s\n", path.c_str());
        std::exit(3);
    }
    out << "Routes: " << sol.routes.size() << "\n";
    for (size_t r = 0; r < sol.routes.size(); ++r) {
        out << "Route " << (r + 1) << ": 0";
        for (int c : sol.routes[r].seq) out << " " << c;
        out << " 0\n";
    }
    char buf[64];
    std::snprintf(buf, sizeof(buf), "%.2f", sol.total_cost);
    out << "Cost: " << buf << "\n";
}


struct WorkRoute {
    std::vector<int> q;
    std::vector<double> early, late;
    int load=0;
    double cost=0;
};
struct Search {
    const Instance& in;
    double d[105][105]{};
    std::mt19937 rng{17431};
    using State=std::vector<WorkRoute>;
    Search(const Instance& i):in(i) {
        for(int a=0;a<=in.n_customers;a++) for(int b=0;b<=in.n_customers;b++) d[a][b]=dist_x10(in.nodes[a],in.nodes[b]);
    }
    double rand01(){return std::generate_canonical<double,32>(rng);}
    void update(WorkRoute& r) {
        int n=r.q.size(); r.early.resize(n);r.late.resize(n);r.load=0;r.cost=0;
        double t=in.nodes[0].e;int prev=0;
        for(int k=0;k<n;k++){
            int c=r.q[k];t=std::max(in.nodes[c].e,t+d[prev][c]);r.early[k]=t;t+=in.nodes[c].s;
            r.load+=in.nodes[c].demand;r.cost+=d[prev][c];prev=c;
        }
        r.cost+=d[prev][0]; double latest=in.nodes[0].l;int next=0;
        for(int k=n-1;k>=0;k--){int c=r.q[k];latest=std::min(in.nodes[c].l,latest-d[c][next]-in.nodes[c].s);r.late[k]=latest;next=c;}
    }
    double insertion(const WorkRoute& r,int c,int p) {
        if(r.load+in.nodes[c].demand>in.capacity)return 1e30;
        int n=r.q.size(),a=p?r.q[p-1]:0,b=p<n?r.q[p]:0;
        double t=p?r.early[p-1]+in.nodes[a].s:in.nodes[0].e;
        t=std::max(in.nodes[c].e,t+d[a][c]);
        if(t>in.nodes[c].l+1e-7)return 1e30;
        double lim=p<n?r.late[p]:in.nodes[0].l;
        if(t+in.nodes[c].s+d[c][b]>lim+1e-7)return 1e30;
        return d[a][c]+d[c][b]-d[a][b];
    }
    double cost(const State& s){double z=0;for(auto& r:s)z+=r.cost;return z;}
    bool better(const State&a,const State&b){return a.size()<b.size()||(a.size()==b.size()&&cost(a)<cost(b)-1e-7);}
    void prune(State& s){s.erase(std::remove_if(s.begin(),s.end(),[](auto&r){return r.q.empty();}),s.end());}
    bool repair(State& s,std::vector<int> todo,double noise,int regret,bool allowNew=true) {
        while(!todo.empty()) {
            int chosen=-1,br=-1,bp=-1;double priority=-1e30;
            for(int k=0;k<(int)todo.size();k++) {
                int c=todo[k];double first=1e30,second=1e30,third=1e30;int rr=-1,pp=-1;
                for(int r=0;r<(int)s.size();r++) {
                    double local=1e30;int pos=-1;
                    for(int p=0;p<=(int)s[r].q.size();p++) {
                        double v=insertion(s[r],c,p);
                        if(v<1e29) v+=noise*(rand01()-.5)*d[0][c];
                        if(v<local){local=v;pos=p;}
                    }
                    if(local<first){third=second;second=first;first=local;rr=r;pp=pos;}
                    else if(local<second){third=second;second=local;}
                    else if(local<third)third=local;
                }
                WorkRoute empty;
                double fresh=insertion(empty,c,0);
                if(allowNew&&fresh<1e29){fresh+=1500; if(fresh<first){third=second;second=first;first=fresh;rr=s.size();pp=0;}else if(fresh<second){third=second;second=fresh;}else if(fresh<third)third=fresh;}
                if(first>1e29)continue;
                double pri=regret==1?-first:std::min(second-first,20000.0)+(regret==3?std::min(third-first,20000.0):0)-first*.05;
                if(pri>priority){priority=pri;chosen=k;br=rr;bp=pp;}
            }
            if(chosen<0)return false;
            if(br==(int)s.size())s.emplace_back();
            s[br].q.insert(s[br].q.begin()+bp,todo[chosen]);update(s[br]);todo.erase(todo.begin()+chosen);
        }
        return true;
    }
    void improve(State& s) {
        for(auto& r:s){
            bool changed=true;int passes=0;
            while(changed&&passes++<3){changed=false;
                for(int a=0;a<(int)r.q.size();a++)for(int b=a+1;b<(int)r.q.size();b++){
                    int prev=a?r.q[a-1]:0,next=b+1<(int)r.q.size()?r.q[b+1]:0;
                    double delta=d[prev][r.q[b]]+d[r.q[a]][next]-d[prev][r.q[a]]-d[r.q[b]][next];
                    if(delta>=-1e-7)continue;
                    WorkRoute t=r;std::reverse(t.q.begin()+a,t.q.begin()+b+1);update(t);
                    bool ok=true;for(int k=0;k<(int)t.q.size();k++)if(t.early[k]>t.late[k]+1e-7){ok=false;break;}
                    if(ok){r=std::move(t);changed=true;}
                }
            }
        }
    }
    State run(Clock::time_point deadline) {
        std::vector<int> all(in.n_customers);std::iota(all.begin(),all.end(),1);
        State cur;repair(cur,all,0,2);improve(cur);State best=cur;
        double value=cost(cur)+1500*cur.size();int iter=0,stale=0;
        while(Clock::now()<deadline){
            State trial=cur; std::vector<int> removed;int op=rng()%5;
            int count=8+rng()%25;
            std::vector<int> flat;for(auto&r:trial)for(int c:r.q)flat.push_back(c);
            std::vector<bool> kill(in.n_customers+1,false);
            if(op==0){
                int r=rng()%trial.size(); if(rand01()<.7){r=0;for(int j=1;j<(int)trial.size();j++)if(trial[j].q.size()<trial[r].q.size())r=j;}
                for(int c:trial[r].q)kill[c]=true;
            }else if(op==1||op==2){
                int seed=flat[rng()%flat.size()];
                std::sort(flat.begin(),flat.end(),[&](int a,int b){return d[seed][a]+.15*std::abs(in.nodes[seed].e-in.nodes[a].e)<d[seed][b]+.15*std::abs(in.nodes[seed].e-in.nodes[b].e);});
                for(int j=0;j<std::min(count,(int)flat.size());j++)kill[flat[j]]=true;
            }else if(op==3){
                std::vector<std::pair<double,int>> ranked;
                for(auto&r:trial)for(int p=0;p<(int)r.q.size();p++){int a=p?r.q[p-1]:0,b=p+1<(int)r.q.size()?r.q[p+1]:0,c=r.q[p];ranked.push_back({(d[a][c]+d[c][b]-d[a][b])*(.7+rand01()*.6),c});}
                std::sort(ranked.rbegin(),ranked.rend());for(int j=0;j<std::min(count,(int)ranked.size());j++)kill[ranked[j].second]=true;
            }else{std::shuffle(flat.begin(),flat.end(),rng);for(int j=0;j<std::min(count,(int)flat.size());j++)kill[flat[j]]=true;}
            for(auto&r:trial){for(int c:r.q)if(kill[c])removed.push_back(c);r.q.erase(std::remove_if(r.q.begin(),r.q.end(),[&](int c){return kill[c];}),r.q.end());update(r);}prune(trial);
            std::shuffle(removed.begin(),removed.end(),rng);
            if(!repair(trial,removed,iter%4==0?.5:0,2+rng()%2)){iter++;continue;}
            if(iter%20==0)improve(trial);
            double nv=cost(trial)+1500*trial.size();
            double temp=std::max(2.0,35.0*(1.0-(iter%1800)/1800.0));
            if(nv<value||rand01()<std::exp((value-nv)/temp)){cur=std::move(trial);value=nv;}
            if((cur.size()<= (size_t)in.max_vehicles ||best.size()>(size_t)in.max_vehicles)&&better(cur,best)){best=cur;stale=0;}else stale++;
            if(stale>700){cur=best;value=cost(cur)+1500*cur.size();stale=0;}
            iter++;
        }
        return best;
    }
};
int main(int argc,char**argv){
    if(argc<4)return 1;
    auto start=Clock::now();double budget=std::atof(argv[3]);if(budget<=0)budget=1;
    auto deadline=start+std::chrono::milliseconds((long long)(std::max(.01,budget-.035)*1000));
    Instance in=parse_input(argv[1]);Search search(in);auto best=search.run(deadline);
    Solution sol;for(auto&r:best){Route out;out.seq=r.q;out.load=r.load;out.cost=r.cost;sol.total_cost+=r.cost;sol.routes.push_back(std::move(out));}
    write_output(argv[2],sol);
    std::fprintf(stderr,"NV=%zu TD=%.2f\n",sol.routes.size(),sol.total_cost);
}
