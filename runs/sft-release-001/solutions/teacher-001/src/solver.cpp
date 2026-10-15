// CVRPTW regret-insertion and large-neighborhood search solver.
// Cached schedule bounds keep insertion checks constant time.
//
// Build:  make
// Run :   ./cvrptw_solver <input.txt> <output.txt> <time_budget_sec>
//
// Retains the best complete solution, prioritizing vehicle count then distance.

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


struct R {
    std::vector<int> v;
    std::vector<double> end, latest;
    int load=0;
    double cost=0;
};
struct Search {
    const Instance& in;
    int n;
    double d[205][205];
    std::mt19937 rng{712367};
    Clock::time_point deadline;
    Search(const Instance& a, Clock::time_point t):in(a),n(a.n_customers),deadline(t) {
        for(int i=0;i<=n;i++) for(int j=0;j<=n;j++) d[i][j]=dist_x10(in.nodes[i],in.nodes[j]);
    }
    double rnd(){return std::generate_canonical<double,32>(rng);}
    bool expired(){return Clock::now()>=deadline;}
    bool update(R& r) {
        int m=r.v.size(),prev=0; double t=in.nodes[0].e;
        r.end.resize(m); r.latest.resize(m); r.load=0;r.cost=0;
        for(int i=0;i<m;i++) {
            int c=r.v[i];r.load+=in.nodes[c].demand;r.cost+=d[prev][c];
            t=std::max(t+d[prev][c],in.nodes[c].e);
            if(t>in.nodes[c].l+1e-7)return false;
            t+=in.nodes[c].s;r.end[i]=t;prev=c;
        }
        r.cost+=d[prev][0];
        if(t+d[prev][0]>in.nodes[0].l+1e-7 || r.load>in.capacity)return false;
        double lim=in.nodes[0].l;int next=0;
        for(int i=m-1;i>=0;i--){int c=r.v[i];lim=std::min(in.nodes[c].l,lim-d[c][next]-in.nodes[c].s);r.latest[i]=lim;next=c;}
        return true;
    }
    bool insertable(const R& r,int c,int p) {
        if(r.load+in.nodes[c].demand>in.capacity)return false;
        int a=p?r.v[p-1]:0,b=p<(int)r.v.size()?r.v[p]:0;
        double t=std::max((p?r.end[p-1]:in.nodes[0].e)+d[a][c],in.nodes[c].e);
        if(t>in.nodes[c].l+1e-7)return false;
        t+=in.nodes[c].s+d[c][b];
        return t<=(b?r.latest[p]:in.nodes[0].l)+1e-7;
    }
    double delta(const R& r,int c,int p){int a=p?r.v[p-1]:0,b=p<(int)r.v.size()?r.v[p]:0;return d[a][c]+d[c][b]-d[a][b];}
    double cost(const std::vector<R>& rs){double c=0;for(auto& r:rs)c+=r.cost;return c;}
    void clean(std::vector<R>& rs){rs.erase(std::remove_if(rs.begin(),rs.end(),[](const R& r){return r.v.empty();}),rs.end());}

    bool repair(std::vector<R>& rs,std::vector<int> todo,int regret,double noise) {
        // Only the modified route's insertion scores need to be refreshed.
        std::vector<std::vector<double>> value(n+1,std::vector<double>(n+1,1e90));
        std::vector<std::vector<int>> position(n+1,std::vector<int>(n+1,-1));
        auto refresh=[&](int j) {
            for(int c:todo) {
                double val=1e90;int pos=-1;
                for(int p=0;p<=(int)rs[j].v.size();p++)if(insertable(rs[j],c,p)) {
                    double x=delta(rs[j],c,p);
                    if(noise)x+=noise*(rnd()-.5)*d[0][c];
                    if(x<val){val=x;pos=p;}
                }
                value[c][j]=val;position[c][j]=pos;
            }
        };
        for(int j=0;j<(int)rs.size();j++)refresh(j);
        while(!todo.empty()) {
            int chosen=-1,br=-1,bp=-1;double priority=-1e100;
            for(int k=0;k<(int)todo.size();k++) {
                int c=todo[k],rr=-1,pp=-1;
                double vals[3]={1e90,1e90,1e90};
                for(int j=0;j<=(int)rs.size();j++) {
                    double val;int pos;
                    if(j==(int)rs.size()) {
                        R empty;val=1e90;pos=-1;
                        if(insertable(empty,c,0)){val=1000+2*d[0][c];pos=0;}
                    } else {val=value[c][j];pos=position[c][j];}
                    if(val<vals[0]){vals[2]=vals[1];vals[1]=vals[0];vals[0]=val;rr=j;pp=pos;}
                    else if(val<vals[1]){vals[2]=vals[1];vals[1]=val;}
                    else if(val<vals[2])vals[2]=val;
                }
                if(rr<0)return false;
                double pr=0;
                for(int h=1;h<regret;h++)pr+=std::min(2000.0,vals[h]-vals[0]);
                pr-=.001*vals[0];
                if(regret==1)pr=-vals[0];
                if(pr>priority){priority=pr;chosen=k;br=rr;bp=pp;}
            }
            if(br==(int)rs.size())rs.push_back(R{});
            rs[br].v.insert(rs[br].v.begin()+bp,todo[chosen]);
            if(!update(rs[br]))return false;
            todo.erase(todo.begin()+chosen);
            refresh(br);
        }
        return true;
    }
    void improve(std::vector<R>& rs) {
        // Best feasible single-customer relocations, including within a route.
        for(int pass=0;pass<3 && !expired();pass++) {
            bool changed=false;
            for(int a=0;a<(int)rs.size();a++)for(int i=0;i<(int)rs[a].v.size();i++) {
                int c=rs[a].v[i];R rem=rs[a];rem.v.erase(rem.v.begin()+i);if(!update(rem))continue;
                double saving=rs[a].cost-rem.cost,best=-1e-6;int bb=-1,pp=-1;
                for(int b=0;b<(int)rs.size();b++) {
                    const R& dest=b==a?rem:rs[b];
                    for(int p=0;p<=(int)dest.v.size();p++) {
                        double gain=delta(dest,c,p)-saving;
                        if(gain<best && insertable(dest,c,p)){best=gain;bb=b;pp=p;}
                    }
                }
                if(bb>=0){rs[a]=std::move(rem);rs[bb].v.insert(rs[bb].v.begin()+pp,c);update(rs[bb]);changed=true;break;}
            }
            clean(rs);if(!changed)break;
        }
        for(auto& r:rs) {
            bool changed=true;
            for(int pass=0;pass<2 && changed;pass++){
                changed=false;
                for(int i=0;i<(int)r.v.size();i++)for(int j=i+1;j<(int)r.v.size();j++){
                    int a=i?r.v[i-1]:0,b=r.v[i],c=r.v[j],e=j+1<(int)r.v.size()?r.v[j+1]:0;
                    if(d[a][c]+d[b][e]>=d[a][b]+d[c][e]-1e-6)continue;
                    R x=r;std::reverse(x.v.begin()+i,x.v.begin()+j+1);
                    if(update(x)){r=std::move(x);changed=true;}
                }
            }
        }
    }
    Solution run() {
        std::vector<int> all(n);std::iota(all.begin(),all.end(),1);
        std::vector<R> cur,best;
        repair(cur,all,2,0);improve(cur);best=cur;
        double bestc=cost(best),curc=cost(cur);
        int iteration=0,stale=0;
        auto begin=Clock::now();
        double duration=std::chrono::duration<double>(deadline-begin).count();
        while(!expired()) {
            iteration++;stale++;
            std::vector<R> cand=cur;
            std::vector<int> removed;std::vector<bool> mark(n+1,false);
            int q=8+rng()%28,mode=rng()%6;
            if(mode==0) {
                int r=rng()%cand.size();for(int c:cand[r].v){mark[c]=true;removed.push_back(c);}
            } else {
                int seed=1+rng()%n;
                std::vector<std::pair<double,int>> rank;
                for(auto& r:cand)for(int p=0;p<(int)r.v.size();p++) {
                    int c=r.v[p],a=p?r.v[p-1]:0,b=p+1<(int)r.v.size()?r.v[p+1]:0;
                    double v=rnd();
                    if(mode==1 || mode==2)v=d[seed][c]+.15*std::abs(in.nodes[seed].e-in.nodes[c].e)+rnd()*20;
                    if(mode==3)v=-(d[a][c]+d[c][b]-d[a][b])*(.7+.6*rnd());
                    rank.emplace_back(v,c);
                }
                std::sort(rank.begin(),rank.end());
                q=std::min(q,n);
                for(int i=0;i<q;i++){mark[rank[i].second]=true;removed.push_back(rank[i].second);}
            }
            bool valid=true;
            for(auto& r:cand){r.v.erase(std::remove_if(r.v.begin(),r.v.end(),[&](int c){return mark[c];}),r.v.end());if(!update(r)){valid=false;break;}}
            if(!valid)continue;
            clean(cand);
            double noise=(rng()%4==0)?.3:0;
            if(!repair(cand,removed,2+rng()%2,noise))continue;
            if(iteration%15==0 || cand.size()<best.size())improve(cand);
            double cc=cost(cand);
            if(cand.size()<best.size() || (cand.size()==best.size() && cc<bestc-1e-6)) {
                best=cand;bestc=cc;stale=0;
            }
            double frac=std::chrono::duration<double>(Clock::now()-begin).count()/std::max(.001,duration);
            double temperature=std::max(1.0,30.0*(1-frac));
            double diff=cc-curc+2000*((int)cand.size()-(int)cur.size());
            if(diff<0 || rnd()<std::exp(-diff/temperature)){cur=std::move(cand);curc=cc;}
            if(stale>250){cur=best;curc=bestc;stale=0;}
        }
        Solution sol;
        for(auto& r:best){Route v;v.seq=r.v;v.cost=r.cost;v.load=r.load;sol.routes.push_back(v);sol.total_cost+=r.cost;}
        std::fprintf(stderr,"iterations=%d vehicles=%zu distance=%.2f\n",iteration,best.size(),bestc);
        return sol;
    }
};
int main(int argc,char** argv) {
    if(argc<4)return 1;
    auto start=Clock::now();double budget=std::atof(argv[3]);if(budget<=0)budget=60;
    auto deadline=start+std::chrono::milliseconds((long long)(std::max(.01,budget-.035)*1000));
    Instance in=parse_input(argv[1]);Search search(in,deadline);Solution sol=search.run();write_output(argv[2],sol);return 0;
}
