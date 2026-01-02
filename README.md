# Basketball Player Tracking & Stats Analysis with DeepStream

Bu proje, NVIDIA DeepStream SDK kullanarak basketbol oyuncularını tespit eder, takip eder (tracking) ve saha üzerindeki hareketlerini analiz ederek canlı istatistik (koşulan mesafe, oyunda kalma süresi) sunar.

## Özellikler
- **Matrix Matcher ID Sistemi:** Oyuncu ID'lerinin karışmasını engelleyen gelişmiş algoritma.
- **Canlı İstatistik Paneli:** Oyuncuların kat ettiği mesafe ve süre ekrana yansıtılır.
- **Minimap Entegrasyonu:** Oyuncuların 2D saha üzerindeki konumları canlı gösterilir.
- **Occlusion Handling:** Oyuncular birbirinin arkasından geçse bile ID korunur.

## Kurulum (Prerequisites)

Bu projeyi çalıştırmak için sisteminizde şunlar kurulu olmalıdır:
- Ubuntu 20.04 / 22.04
- NVIDIA DeepStream SDK 6.x veya üzeri
- Python 3.8+
- Gst-python

## Nasıl Çalıştırılır?

1. Repoyu klonlayın:
   ```bash
   git clone [https://github.com/KULLANICI_ADIN/REPO_ADIN.git](https://github.com/KULLANICI_ADIN/REPO_ADIN.git)
   cd REPO_ADIN