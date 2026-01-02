# Basketball Player Tracking & Stats Analysis with DeepStream

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![DeepStream](https://img.shields.io/badge/NVIDIA-DeepStream%206.x-green)
![Platform](https://img.shields.io/badge/Platform-Jetson%20%7C%20dGPU-orange)
![License](https://img.shields.io/badge/License-MIT-yellow)

Bu proje, **NVIDIA DeepStream SDK** ve **Computer Vision** teknikleri kullanılarak basketbol maçlarındaki oyuncuları gerçek zamanlı olarak tespit etmek, takip etmek ve performans analizi yapmak için geliştirilmiştir. Sistem, oyuncuların kimliğini koruyarak saha üzerindeki hareketlerinden anlamlı veriler üretir.

---

## Özellikler

* **Derin Öğrenme Tabanlı Tespit:** NVIDIA **PeopleNet (ResNet34)** modeli kullanılarak kalabalık sahnelerde bile yüksek doğrulukta oyuncu tespiti.
* **Gelişmiş Takip (Matrix Matcher ID):** Oyuncuların birbirine çok yaklaştığı veya birbirini kapattığı durumlarda ID karışıklığını önleyen gelişmiş eşleştirme mantığı.
* **Canlı İstatistik Paneli:**
    * 🏃‍♂️ **Koşulan Mesafe:** Her oyuncu için piksel-metre dönüşümü ile anlık kat edilen mesafe hesabı.
    * ⏱️ **Oyunda Kalma Süresi:** Oyuncunun kadrajda kaldığı sürenin gerçek zamanlı takibi.
* **Minimap (2D Saha) Entegrasyonu:** Oyuncuların 3D görüntüdeki konumlarını 2D kuş bakışı saha görseline (Top-Down View) yansıtma.
* **Occlusion Handling:** Oyuncular geçici olarak kadrajdan çıksa bile ID'lerinin korunması (Re-Identification).

---

## Kurulum (Prerequisites)

Projeyi çalıştırmak için sisteminizde aşağıdaki bileşenlerin kurulu olması gerekmektedir:

* **İşletim Sistemi:** Ubuntu 20.04 / 22.04
* **Donanım:** NVIDIA GPU (RTX serisi veya NVIDIA Jetson Edge cihazlar)
* **Sürücüler:** NVIDIA Driver 525+ ve CUDA 11.x/12.x
* **Yazılım:** NVIDIA DeepStream SDK 6.x veya üzeri
* **Dil:** Python 3.8+ ve Gst-python (DeepStream Python Bindings)

Modeller ve Yapılandırma
Bu proje TensorRT optimizasyonu ile çalışır.

```text
├── models/
│   └── peoplenet/          # PeopleNet ONNX modeli
├── config_peoplenet.txt    # Inference yapılandırması
├── config_tracker_basketball.yml # NvTracker ayarları
├── main.py                 # DeepStream Pipeline ve ana döngü
├── tracker_logic.py        # İstatistiksel hesaplamalar ve ID yönetimi
├── visual_utils.py         # Çizim ve HUD görselleştirme araçları
├── court.jpg               # Minimap için referans saha görseli
├── requirements            # Gerekli Python paketleri
└── .gitignore              # Engine ve video dosyalarını hariç tutan kurallar

⚠️ Önemli Not: .engine dosyaları GPU mimarisine özel üretildiği için repoya dahil edilmemiştir. Projeyi ilk kez çalıştırdığınızda, DeepStream otomatik olarak .onnx dosyasından sizin donanımınıza özel bir .engine dosyası derleyecektir. Bu işlem ilk seferde birkaç dakika sürebilir.

Ana Model: models/peoplenet/resnet34_peoplenet.onnx

Model Config: config_peoplenet.txt

Takipçi (Tracker) Config: config_tracker_basketball.yml

```bash
git clone [https://github.com/diyaralma/basketball-player-tracking-deepstream.git](https://github.com/diyaralma/basketball-player-tracking-deepstream.git)
cd basketball-player-tracking-deepstream

### Bağımlılıkları Yükleme
```bash
pip install -r requirements
python3 main.py
