# Basketball Player Tracking & Stats Analysis with DeepStream

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![DeepStream](https://img.shields.io/badge/NVIDIA-DeepStream%207.0-green)
![Docker](https://img.shields.io/badge/Docker-Ready-blue)
![Platform](https://img.shields.io/badge/Platform-Jetson%20%7C%20dGPU-orange)
![License](https://img.shields.io/badge/License-MIT-yellow)

Bu proje, **NVIDIA DeepStream SDK** ve **Computer Vision** teknikleri kullanılarak basketbol maçlarındaki oyuncuları gerçek zamanlı olarak tespit etmek, takip etmek ve performans analizi yapmak için geliştirilmiştir. Sistem, oyuncuların kimliğini koruyarak saha üzerindeki hareketlerinden anlamlı veriler üretir.

---

## 🚀 Özellikler

* **Derin Öğrenme Tabanlı Tespit:** NVIDIA **PeopleNet (ResNet34)** modeli kullanılarak kalabalık sahnelerde bile yüksek doğrulukta oyuncu tespiti.
* **Gelişmiş Takip (Matrix Matcher ID):** Oyuncuların birbirine çok yaklaştığı veya birbirini kapattığı durumlarda ID karışıklığını önleyen gelişmiş eşleştirme mantığı.
* **Canlı İstatistik Paneli:**
    * 🏃‍♂️ **Koşulan Mesafe:** Her oyuncu için piksel-metre dönüşümü ile anlık kat edilen mesafe hesabı.
    * ⏱️ **Oyunda Kalma Süresi:** Oyuncunun kadrajda kaldığı sürenin gerçek zamanlı takibi.
* **Minimap (2D Saha) Entegrasyonu:** Oyuncuların 3D görüntüdeki konumlarını 2D kuş bakışı saha görseline (Top-Down View) yansıtma.
* **Occlusion Handling:** Oyuncular geçici olarak kadrajdan çıksa bile ID'lerinin korunması (Re-Identification).

---

## 🐳 Kurulum ve Çalıştırma (Docker ile - Önerilen)

Bu projeyi en sorunsuz şekilde çalıştırmak için **Docker** kullanmanız önerilir.

### Gereksinimler (Ana Bilgisayar)
* **OS:** Linux (Ubuntu 20.04 / 22.04 önerilir)
* **GPU:** NVIDIA Ekran Kartı
* **Yazılım:** Docker ve NVIDIA Container Toolkit kurulu olmalıdır.

### Adım 1: Projeyi İndirin

    git clone [https://github.com/diyaralma/basketball-player-tracking-deepstream.git](https://github.com/diyaralma/basketball-player-tracking-deepstream.git)
    cd basketball-player-tracking-deepstream

### Adım 2: Docker İmajını Oluşturun (Build)
Bu işlem projenin gereksinim duyduğu ortamı (DeepStream 7.0, Pyds, Gstreamer) hazırlar.

    docker build -t basket-detection .

### Adım 3: Konteyneri Başlatın
Ekran kartını kullanabilmek ve grafik arayüzünü (GUI) görebilmek için aşağıdaki komutu kullanın:

    xhost +

    sudo docker run --gpus all -it --net=host --privileged \
    -v /tmp/.X11-unix:/tmp/.X11-unix -e DISPLAY=$DISPLAY \
    -v $(pwd):/app \
    basket-detection

### Adım 4: Uygulamayı Çalıştırın
Konteynerin içine girdikten sonra:

    python3 main.py

---

## 🛠️ Manuel Kurulum (Docker Olmadan)

Eğer Docker kullanmak istemiyorsanız sisteminizde aşağıdaki bileşenlerin **manuel olarak** kurulu olması gerekmektedir:

* **İşletim Sistemi:** Ubuntu 20.04 / 22.04
* **Sürücüler:** NVIDIA Driver 535+ ve CUDA 12.x
* **DeepStream SDK:** Sürüm 7.0 veya 6.x
* **Python Bindings (pyds):** DeepStream sürümünüze uygun olarak derlenmiş olmalıdır.

    pip install -r requirements
    python3 main.py

---

## 📂 Proje Yapısı

    ├── models/
    │   └── peoplenet/          # PeopleNet ONNX modeli
    ├── config_peoplenet.txt    # Inference yapılandırması
    ├── config_tracker_basketball.yml # NvTracker ayarları
    ├── main.py                 # DeepStream Pipeline ve ana döngü
    ├── tracker_logic.py        # İstatistiksel hesaplamalar ve ID yönetimi
    ├── visual_utils.py         # Çizim ve HUD görselleştirme araçları
    ├── court.jpg               # Minimap için referans saha görseli
    ├── Dockerfile              # Projenin Docker imaj dosyası
    ├── requirements            # Gerekli Python paketleri
    └── .gitignore              # Gereksiz dosyaları hariç tutan kurallar

---

## ⚠️ Önemli Notlar

1. **Engine Dosyası:** `.engine` dosyaları GPU mimarisine özel üretildiği için repoya dahil edilmemiştir. Projeyi ilk kez çalıştırdığınızda, DeepStream otomatik olarak `.onnx` dosyasından sizin donanımınıza özel bir `.engine` dosyası derleyecektir. Bu işlem ilk seferde birkaç dakika sürebilir.
2. **Video Dosyası:** `main.py` içerisinde `filesrc` kısmında kendi video dosyanızın yolunu belirtmeyi unutmayın.

---

### Kullanılan Modeller ve Konfigürasyonlar
* **Ana Model:** `models/peoplenet/resnet34_peoplenet.onnx`
* **Model Config:** `config_peoplenet.txt`
* **Takipçi (Tracker):** NvDCF (DeepStream 7.0 standart tracker)
