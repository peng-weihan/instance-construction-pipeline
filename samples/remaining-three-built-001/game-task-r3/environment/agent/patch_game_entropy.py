"""Small reproducibility patch to a private copy of the pinned engine source."""
from pathlib import Path
root=Path('/opt/runtime/wesnoth-source')
p=root/'src/random.cpp';s=p.read_text();s='#include <cstdlib>\n'+s
s=s.replace('gen_.seed(entropy_source());', '''if(const char* fixed = std::getenv("EDGE_GAME_RNG_SEED")) {
                gen_.seed(static_cast<unsigned>(std::strtoul(fixed, nullptr, 10)));
            } else { gen_.seed(entropy_source()); }''')
p.write_text(s)
p=root/'src/seed_rng.cpp';s=p.read_text();s='#include <cstdlib>\n#include <random>\n'+s
s=s.replace('static boost::random_device rnd_;\n\t\treturn rnd_();', '''if(const char* fixed = std::getenv("EDGE_GAME_RNG_SEED")) {
            static std::mt19937 deterministic(static_cast<unsigned>(std::strtoul(fixed, nullptr, 10)));
            return deterministic();
        }
        static boost::random_device rnd_;
        return rnd_();''')
p.write_text(s)
print('Patched private engine copy: default RNG and Lua/network seed source')
