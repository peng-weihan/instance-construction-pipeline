FROM ubuntu@sha256:534baea6a22c03a63003dbc8dbe78fe34bc0d7e595d9a9dc9834884ff530eb55
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends python3 python3-venv python3-pip bubblewrap git curl ca-certificates build-essential cmake ninja-build pkg-config && rm -rf /var/lib/apt/lists/*
RUN python3 -m venv /opt/runtime/venv
ENV PATH="/opt/runtime/venv/bin:/opt/runtime/elan/bin:${PATH}"
RUN python -m pip install --no-cache-dir numpy==2.2.6 scipy==1.15.3 shapely==2.1.1 applicationinsights==0.11.10 requests==2.32.4 pytest==8.4.1 cmake==3.31.6
COPY public /opt/public
COPY capture_build.py /opt/capture_build.py
RUN apt-get update && apt-get install -y --no-install-recommends libboost-all-dev libssl-dev libicu-dev libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libcurl4-openssl-dev libvorbis-dev libfontconfig-dev libcairo2-dev libpango1.0-dev libreadline-dev gettext libdbus-1-dev && rm -rf /var/lib/apt/lists/*
RUN git init /opt/runtime/wesnoth-source && git -C /opt/runtime/wesnoth-source remote add origin https://github.com/wesnoth/wesnoth.git && git -C /opt/runtime/wesnoth-source fetch --depth 1 origin 8ba2b3ebd33f6850c2dc4fe7c6478c7e4f9fc3fd && git -C /opt/runtime/wesnoth-source checkout --detach FETCH_HEAD && git -C /opt/runtime/wesnoth-source submodule update --init --recursive --depth 1
COPY patch_game_entropy.py /opt/patch_game_entropy.py
RUN python3 /opt/patch_game_entropy.py
RUN cmake -S /opt/runtime/wesnoth-source -B /opt/runtime/wesnoth-build -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=/opt/runtime/wesnoth -DENABLE_SERVER=OFF -DENABLE_CAMPAIGN_SERVER=OFF -DENABLE_TESTS=OFF -DENABLE_NLS=OFF -DENABLE_NOTIFICATIONS=OFF
RUN cmake --build /opt/runtime/wesnoth-build -j 2 && cmake --install /opt/runtime/wesnoth-build
RUN python /opt/capture_build.py
COPY public /judge/public
COPY private /judge/private
COPY verifier /judge/verifier
WORKDIR /judge/verifier
ENTRYPOINT ["/opt/runtime/venv/bin/python", "/judge/verifier/entry.py"]
