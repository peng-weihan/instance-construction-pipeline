FROM edge-raymone-game:initial
RUN /opt/runtime/venv/bin/python -m pip install --no-cache-dir numpy==2.2.6 scipy==1.15.3 scikit-learn==1.7.0 h5py==3.14.0 pandas==2.3.0 anndata==0.11.4 harmonypy==0.0.10 pynndescent==0.5.13 umap-learn==0.5.7 scanpy==1.11.3
RUN /opt/runtime/venv/bin/python -m pip install --no-cache-dir torch==2.7.1+cpu --index-url https://download.pytorch.org/whl/cpu
RUN /opt/runtime/venv/bin/python -m pip freeze > /opt/runtime/ml-requirements.lock.txt
