# NVIDIA'nın resmi DeepStream imajını baz alıyoruz
FROM nvcr.io/nvidia/deepstream:7.0-triton-multiarch

# istem paketlerini ve Python gereksinimlerini yüklüyoruz
# (Gstreamer, Python bindingleri ve OpenCV için gerekli her şey)
RUN apt-get update && apt-get install -y \
    python3-gi python3-dev python3-gst-1.0 \
    python3-numpy python3-opencv \
    libgstrtspserver-1.0-dev libgstreamer1.0-dev \
    libgirepository1.0-dev libcairo2-dev \
    git cmake gcc pkg-config

# Calışma klasörünü ayarlıyoruz
WORKDIR /app

# proje dosyalarını (main.py, configler vb.) içeri kopyalıyoruz
COPY . /app

# Pyds kurulumu
# bu komut pyds'yi indirip kurar
RUN cd /opt/nvidia/deepstream/deepstream/sources/ && \
    git clone https://github.com/NVIDIA-AI-IOT/deepstream_python_apps.git && \
    cd deepstream_python_apps/bindings && \
    mkdir build && \
    cd build && \
    cmake .. && \
    make -j$(nproc) && \
    make install

# Ekran kartı kullanımı için ortam değişkeni
ENV DISPLAY=:0
ENV NVIDIA_VISIBLE_DEVICES=all
ENV NVIDIA_DRIVER_CAPABILITIES=all

# Konteyner açılınca terminali ver
CMD ["/bin/bash"]