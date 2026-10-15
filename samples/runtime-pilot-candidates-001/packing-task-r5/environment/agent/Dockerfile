FROM ubuntu@sha256:534baea6a22c03a63003dbc8dbe78fe34bc0d7e595d9a9dc9834884ff530eb55
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends python3 python3-venv python3-pip bubblewrap git curl ca-certificates build-essential cmake ninja-build pkg-config && rm -rf /var/lib/apt/lists/*
RUN python3 -m venv /opt/runtime/venv
ENV PATH="/opt/runtime/venv/bin:/opt/runtime/elan/bin:${PATH}"
RUN python -m pip install --no-cache-dir numpy==2.2.6 scipy==1.15.3 shapely==2.1.1 applicationinsights==0.11.10 requests==2.32.4 pytest==8.4.1 cmake==3.31.6
COPY public /opt/public
COPY capture_build.py /opt/capture_build.py
RUN cp -a /opt/public/repo /opt/runtime/packing
RUN cmake -S /opt/runtime/packing -B /opt/runtime/packing-build -DCMAKE_BUILD_TYPE=Release -DPACKINGSOLVER_BUILD_TEST=OFF -DPACKINGSOLVER_USE_CLP=OFF -DPACKINGSOLVER_USE_HIGHS=ON
RUN cmake --build /opt/runtime/packing-build --target PackingSolver_irregular_main -j 2
COPY lock_packing_dependencies.py /opt/lock_packing_dependencies.py
RUN python /opt/lock_packing_dependencies.py
RUN python /opt/capture_build.py
RUN mkdir /workspace && cp -a /opt/public/. /workspace/
WORKDIR /workspace
CMD ["/bin/bash"]
