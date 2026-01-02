import math

# --- AYARLAR ---
# Buradaki ayarları deneme yanılma ile buldum.
MAX_SLOTS = 10  # En fazla 10 oyuncuyu takip ediyoruz (0'dan 9'a kadar).
MAX_MEMORY_DIST = 200.0  # Oyuncu hızlı hareket ederse en fazla 200 piksel uzağa gitmiştir dedik.
MAX_LOST_TIME = 150  # Oyuncu 5 saniye (yaklaşık 150 kare) boyunca görünmezse takibi bırakıyoruz.


# --- OYUNCU BİLGİLERİ ---
class PlayerStats:
    # Her oyuncunun istatistiklerini burada tutuyoruz.
    def __init__(self, v_id):
        self.id = v_id
        self.total_distance = 0.0  # Toplam koştuğu mesafe
        self.frame_count = 0  # Kaç karedir sahadaysa sayıyoruz
        self.last_pos = None  # En son nerede görüldü (x, y)
        self.active_now = False  # Şu an ekranda mı değil mi?


# --- VERİ DEPOSU ---
# Bütün oyuncuların verilerini bu sözlükte saklıyoruz, diğer dosyalardan buraya erişeceğiz.
player_data = {}


# --- ID YÖNETİMİ ---
class IdentityManager:
    # Burası en önemli kısım. Oyuncuların ID'leri karışmasın diye kontrolleri burada yapıyoruz.
    def __init__(self):
        # 10 tane boş koltuk (slot) oluşturduk. Başta hepsi boş (None).
        self.slots = {i: None for i in range(MAX_SLOTS)}

    def update_slots(self, current_detections, frame_num):
        # Bu fonksiyon her karede çalışıp kimin kim olduğunu bulmaya çalışıyor.

        unassigned_detections = []  # Henüz kim olduğunu bulamadıklarımız
        assigned_slots = set()  # Dolu olan koltuklar

        # Algılananları ID'sine göre hızlı bulmak için bir sözlüğe attım.
        detection_map = {d['ds_id']: d for d in current_detections}

        # 1. ADIM: ID HİÇ DEĞİŞMEMİŞSE (KOLAY EŞLEŞME)
        # Eğer DeepStream'den gelen ID, bizim koltuktaki ID ile aynıysa sorun yok.
        for s_id in range(MAX_SLOTS):
            slot = self.slots[s_id]
            if slot is not None:
                ds_id = slot['ds_id']
                # Bakalım bu ID şu an ekranda var mı?
                if ds_id in detection_map:
                    det = detection_map[ds_id]
                    # Varsa bilgilerini güncelliyoruz.
                    self.slots[s_id]['last_seen'] = frame_num
                    self.slots[s_id]['x'] = det['x']
                    self.slots[s_id]['y'] = det['y']
                    assigned_slots.add(s_id)  # Bu koltuk doldu işaretledik.

        # Eşleşmeyenleri ayıralım
        for det in current_detections:
            is_assigned = False
            for s_id in range(MAX_SLOTS):
                # Eğer bu tespit zaten bir koltuğa aitse işlem yapma
                if self.slots[s_id] is not None and self.slots[s_id]['ds_id'] == det['ds_id']:
                    is_assigned = True
                    break
            if not is_assigned:
                unassigned_detections.append(det)

        # 2. ADIM: ID DEĞİŞMİŞSE MESAFEYE BAK (ZOR EŞLEŞME)
        # DeepStream bazen ID değiştiriyor, biz de "en yakın olan odur" mantığıyla düzeltiyoruz.
        possible_matches = []

        for i, det in enumerate(unassigned_detections):
            for s_id in range(MAX_SLOTS):
                if s_id in assigned_slots: continue  # Dolu koltukları geç

                slot = self.slots[s_id]
                if slot is not None:
                    # Oyuncu çok uzun süredir yoksa artık onu arama
                    if (frame_num - slot['last_seen']) > MAX_LOST_TIME: continue

                    # Pisagor teoremi ile aradaki mesafeyi hesaplıyoruz.
                    dist = math.sqrt((det['x'] - slot['x']) ** 2 + (det['y'] - slot['y']) ** 2)

                    # Eğer mesafe mantıklıysa (200px'den azsa) aday listesine ekle.
                    if dist < MAX_MEMORY_DIST:
                        possible_matches.append((dist, s_id, i))

        # En kısa mesafesi olanları en başa alıyoruz ki önce onlar eşleşsin.
        possible_matches.sort(key=lambda x: x[0])
        used_det_indices = set()

        for dist, s_id, det_idx in possible_matches:
            if s_id in assigned_slots: continue
            if det_idx in used_det_indices: continue

            # Eşleşmeyi yap ve bilgileri güncelle
            det = unassigned_detections[det_idx]
            self.slots[s_id]['ds_id'] = det['ds_id']
            self.slots[s_id]['last_seen'] = frame_num
            self.slots[s_id]['x'] = det['x']
            self.slots[s_id]['y'] = det['y']
            assigned_slots.add(s_id)
            used_det_indices.add(det_idx)

        # 3. ADIM: YENİ OYUNCU GELDİYSE (BOŞ KOLTUK VER)
        for i, det in enumerate(unassigned_detections):
            if i in used_det_indices: continue  # Zaten eşleştiyse geç

            # Boş bir yer arıyoruz
            for s_id in range(MAX_SLOTS):
                slot = self.slots[s_id]

                # Ya koltuk tamamen boştur ya da içindeki oyuncu süresi dolup gitmiştir.
                is_expired = slot is not None and (frame_num - slot['last_seen']) > MAX_LOST_TIME

                if s_id not in assigned_slots and (slot is None or is_expired):
                    # Yeni oyuncuyu buraya kaydediyoruz.
                    self.slots[s_id] = {
                        'ds_id': det['ds_id'],
                        'last_seen': frame_num,
                        'x': det['x'],
                        'y': det['y']
                    }
                    assigned_slots.add(s_id)
                    used_det_indices.add(i)
                    break

        # Sonuçları (Hangi DeepStream ID hangi Bizim ID'ye denk geliyor) döndürüyoruz.
        result_map = {}
        for s_id in range(MAX_SLOTS):
            slot = self.slots[s_id]
            # Sadece son zamanlarda görünenleri listeye alıyoruz, hayaletleri değil.
            if slot is not None and (frame_num - slot['last_seen']) < 10:
                result_map[slot['ds_id']] = s_id
        return result_map


# Buradan bir tane nesne oluşturuyoruz, program boyunca bunu kullanacağız.
id_manager = IdentityManager()