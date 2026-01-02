import sys
import math
import pyds
import gi
import tracker_logic  # Hesaplamaları yaptığımız diğer dosyayı çağırıyoruz

gi.require_version('Gst', '1.0')
from gi.repository import Gst

# --- EKRAN AYARLARI ---
# Minimap (Küçük harita) sağ altta duracak, boyutlarını buradan ayarladım.
MINIMAP_W = 350
MINIMAP_H = 200
VIDEO_W = 1920
VIDEO_H = 1080
# Haritayı tam köşeye yapıştırmadım, biraz boşluk bıraktım (Offset).
OFFSET_X = VIDEO_W - MINIMAP_W - 30
OFFSET_Y = VIDEO_H - MINIMAP_H - 30


def get_mapped_coordinates(video_x, video_y):
    # Bu fonksiyon oyuncunun ekrandaki yerini (1920x1080),
    # sağ alttaki küçük haritanın boyutlarına (350x200) oranlıyor.
    norm_x = video_x / VIDEO_W
    norm_y = video_y / VIDEO_H
    map_x = norm_x * MINIMAP_W
    map_y = norm_y * MINIMAP_H
    # Sonra haritanın ekrandaki kayma payını (offset) ekliyoruz.
    return int(map_x + OFFSET_X), int(map_y + OFFSET_Y)


def get_color(v_id):
    # Her oyuncuya farklı bir renk veriyoruz ki karışmasın.
    # ID 0 kırmızı, ID 1 yeşil vs.
    colors = [
        (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0),
        (1.0, 1.0, 0.0), (0.0, 1.0, 1.0), (1.0, 0.0, 1.0),
        (1.0, 0.5, 0.0), (0.5, 0.0, 1.0), (0.0, 0.5, 0.5), (0.5, 0.5, 0.5)
    ]
    # Eğer ID yoksa gri döndür (Tanımsız).
    if v_id is None: return (0.6, 0.6, 0.6)
    # Listemizde renk varsa onu ver, yoksa beyaz ver.
    if v_id < 10: return colors[v_id]
    return (1.0, 1.0, 1.0)


def add_minimap_overlay(pipeline, link_source, image_path="court.jpg"):
    # Burası biraz karışık GStreamer ayarları.
    # Özetle: court.jpg resmini alıp videonun üzerine yapıştırıyor.
    to_cpu_conv = Gst.ElementFactory.make("nvvideoconvert", "minimap_to_cpu")
    caps_cpu = Gst.ElementFactory.make("capsfilter", "minimap_caps")
    caps_cpu.set_property("caps", Gst.Caps.from_string("video/x-raw, format=RGBA"))

    # Resmi koyacağımız yer ve boyutlar
    overlay = Gst.ElementFactory.make("gdkpixbufoverlay", "minimap_overlay")
    overlay.set_property("location", image_path)
    overlay.set_property("overlay-width", MINIMAP_W)
    overlay.set_property("overlay-height", MINIMAP_H)
    overlay.set_property("offset-x", OFFSET_X)
    overlay.set_property("offset-y", OFFSET_Y)

    to_gpu_conv = Gst.ElementFactory.make("nvvideoconvert", "minimap_to_gpu")

    pipeline.add(to_cpu_conv)
    pipeline.add(caps_cpu)
    pipeline.add(overlay)
    pipeline.add(to_gpu_conv)

    link_source.link(to_cpu_conv)
    to_cpu_conv.link(caps_cpu)
    caps_cpu.link(overlay)
    overlay.link(to_gpu_conv)
    return to_gpu_conv


def check_and_renew_meta(display_meta, batch_meta, frame_meta, type_needed="label"):
    # DeepStream'in bir pakete en fazla 16 çizim koyma sınırı varmış.
    # Eğer 16'yı geçersek program hata veriyor.
    # O yüzden bu fonksiyon doluluğu kontrol ediyor, dolarsa yeni paket açıyor.
    limit = 16
    is_full = False

    if type_needed == "label" and display_meta.num_labels >= limit:
        is_full = True
    elif type_needed == "rect" and display_meta.num_rects >= limit:
        is_full = True
    elif type_needed == "circle" and display_meta.num_circles >= limit:
        is_full = True

    if is_full:
        # Dolu paketi gönder gitsin
        pyds.nvds_add_display_meta_to_frame(frame_meta, display_meta)
        # Yeni tertemiz paket al
        display_meta = pyds.nvds_acquire_display_meta_from_pool(batch_meta)
        display_meta.num_labels = 0
        display_meta.num_rects = 0
        display_meta.num_circles = 0

    return display_meta


def draw_stats_panel(display_meta, batch_meta, frame_meta):
    # Sol üstteki istatistik tablosunu burada çiziyoruz.

    # 1. Önce Siyah Arka Plan Kutusu
    # Yer var mı diye kontrol et (check_and_renew_meta ile)
    display_meta = check_and_renew_meta(display_meta, batch_meta, frame_meta, "rect")
    i = display_meta.num_rects
    display_meta.rect_params[i].left = 20
    display_meta.rect_params[i].top = 20
    display_meta.rect_params[i].width = 330
    display_meta.rect_params[i].height = 360
    display_meta.rect_params[i].border_width = 2
    display_meta.rect_params[i].border_color.set(1.0, 1.0, 1.0, 0.8)  # Beyaz çerçeve
    display_meta.rect_params[i].has_bg_color = 1
    display_meta.rect_params[i].bg_color.set(0.0, 0.0, 0.0, 0.6)  # Yarı saydam siyah
    display_meta.num_rects += 1

    # 2. Başlık Yazısı
    display_meta = check_and_renew_meta(display_meta, batch_meta, frame_meta, "label")
    i = display_meta.num_labels
    display_meta.text_params[i].display_text = "LIVE PLAYER STATS"
    display_meta.text_params[i].x_offset = 30
    display_meta.text_params[i].y_offset = 30
    display_meta.text_params[i].font_params.font_name = "Arial"
    display_meta.text_params[i].font_params.font_size = 14
    display_meta.text_params[i].font_params.font_color.set(1.0, 0.8, 0.0, 1.0)  # Sarı renk
    display_meta.text_params[i].set_bg_clr = 0
    display_meta.num_labels += 1

    # 3. Oyuncu Satırları (P-0'dan P-9'a kadar)
    y_pos = 60
    # tracker_logic dosyasındaki verilere bakıyoruz
    for pid in range(tracker_logic.MAX_SLOTS):
        # Varsayılan değerler (eğer oyuncu yoksa)
        time_str = "00:00"
        dist_str = "0 px"
        status_marker = "○"
        alpha = 0.5
        r, g, b = get_color(pid)

        # Eğer oyuncu verisi varsa güncelle
        if pid in tracker_logic.player_data:
            stats = tracker_logic.player_data[pid]
            seconds = int(stats.frame_count / 30)  # 30 FPS varsaydık
            minutes = int(seconds / 60)
            sec_rem = seconds % 60
            time_str = f"{minutes:02d}:{sec_rem:02d}"
            dist_str = f"{int(stats.total_distance)} px"

            # Oyuncu şu an ekranda mı?
            if stats.active_now:
                status_marker = "●"
                alpha = 1.0
            else:
                status_marker = "○"
                alpha = 0.7

        # Yazıyı ekrana ekle (Yine limit kontrolü yaparak)
        display_meta = check_and_renew_meta(display_meta, batch_meta, frame_meta, "label")
        i = display_meta.num_labels
        display_meta.text_params[i].display_text = f"{status_marker} P-{pid:<2}  |  {time_str}  |  {dist_str}"
        display_meta.text_params[i].x_offset = 30
        display_meta.text_params[i].y_offset = y_pos
        display_meta.text_params[i].font_params.font_name = "Consolas"  # Hizalı olsun diye bu fontu seçtim
        display_meta.text_params[i].font_params.font_size = 11
        display_meta.text_params[i].font_params.font_color.set(r, g, b, alpha)
        display_meta.text_params[i].set_bg_clr = 0
        display_meta.num_labels += 1
        y_pos += 28

    return display_meta


def tiler_sink_pad_buffer_probe(pad, info, u_data):
    # BU FONKSİYON HER KAREDE (FRAME) ÇALIŞIYOR.
    # Bütün çizim ve hesaplama işlemleri burada dönüyor.
    gst_buffer = info.get_buffer()
    if not gst_buffer: return Gst.PadProbeReturn.OK

    batch_meta = pyds.gst_buffer_get_nvds_batch_meta(hash(gst_buffer))
    l_frame = batch_meta.frame_meta_list

    while l_frame is not None:
        try:
            frame_meta = pyds.NvDsFrameMeta.cast(l_frame.data)
        except:
            break

        # 1. ADIM: EKRANDAKİ ADAMLARI TOPLA
        detections = []
        l_obj = frame_meta.obj_meta_list
        while l_obj is not None:
            try:
                obj_meta = pyds.NvDsObjectMeta.cast(l_obj.data)
            except:
                break
            # class_id 0 (insan) veya 2 (sporcu) ise al
            if obj_meta.class_id == 0 or obj_meta.class_id == 2:
                # Çok küçük kutuları (gürültü) almayalım
                if obj_meta.rect_params.height > 40:
                    fx = obj_meta.rect_params.left + (obj_meta.rect_params.width / 2)
                    fy = obj_meta.rect_params.top + obj_meta.rect_params.height
                    detections.append({'ds_id': obj_meta.object_id, 'x': fx, 'y': fy})
            try:
                l_obj = l_obj.next
            except:
                break

        # 2. ADIM: KİM KİMDİR HESAPLA (tracker_logic dosyasını kullan)
        id_map = tracker_logic.id_manager.update_slots(detections, frame_meta.frame_num)

        # Her karede aktiflik durumunu sıfırlıyoruz, görünenleri true yapacağız
        for pid in tracker_logic.player_data:
            tracker_logic.player_data[pid].active_now = False

        # 3. ADIM: ÇİZİM İŞLEMLERİ
        display_meta = pyds.nvds_acquire_display_meta_from_pool(batch_meta)
        display_meta.num_circles = 0
        display_meta.num_labels = 0
        display_meta.num_rects = 0

        # İstatistik panelini çiz
        display_meta = draw_stats_panel(display_meta, batch_meta, frame_meta)

        l_obj = frame_meta.obj_meta_list
        while l_obj is not None:
            try:
                obj_meta = pyds.NvDsObjectMeta.cast(l_obj.data)
            except:
                break

            if obj_meta.class_id == 0 or obj_meta.class_id == 2:
                if obj_meta.rect_params.height > 40:
                    ds_id = obj_meta.object_id
                    # Bu DeepStream ID'si bizde kime denk geliyor?
                    v_id = id_map.get(ds_id)
                    r, g, b = get_color(v_id)

                    if v_id is not None:
                        # --- İSTATİSTİKLERİ GÜNCELLE ---
                        if v_id not in tracker_logic.player_data:
                            tracker_logic.player_data[v_id] = tracker_logic.PlayerStats(v_id)
                        stats = tracker_logic.player_data[v_id]
                        stats.active_now = True
                        stats.frame_count += 1

                        fx = obj_meta.rect_params.left + (obj_meta.rect_params.width / 2)
                        fy = obj_meta.rect_params.top + obj_meta.rect_params.height

                        # Mesafe hesapla
                        if stats.last_pos is not None:
                            prev_x, prev_y = stats.last_pos
                            dist = math.sqrt((fx - prev_x) ** 2 + (fy - prev_y) ** 2)
                            if dist > 2.0: stats.total_distance += dist
                        stats.last_pos = (fx, fy)

                        # --- ANA EKRANDA KUTU ÇİZ ---
                        obj_meta.rect_params.border_width = 3
                        obj_meta.rect_params.border_color.set(r, g, b, 1.0)
                        obj_meta.text_params.display_text = f"P-{v_id}"
                        obj_meta.text_params.font_params.font_color.set(1.0, 1.0, 1.0, 1.0)
                        obj_meta.text_params.set_bg_clr = 1
                        obj_meta.text_params.text_bg_clr.set(r * 0.5, g * 0.5, b * 0.5, 0.8)

                        # --- MINIMAP ÇİZİMİ ---
                        mm_x, mm_y = get_mapped_coordinates(fx, fy)

                        # Haritaya nokta koy
                        display_meta = check_and_renew_meta(display_meta, batch_meta, frame_meta, "circle")
                        ci = display_meta.num_circles
                        display_meta.circle_params[ci].xc = mm_x
                        display_meta.circle_params[ci].yc = mm_y
                        display_meta.circle_params[ci].radius = 8
                        display_meta.circle_params[ci].circle_color.set(r, g, b, 1.0)
                        display_meta.circle_params[ci].has_bg_color = 1
                        display_meta.circle_params[ci].bg_color.set(r, g, b, 1.0)
                        display_meta.num_circles += 1

                        # Haritaya numara yaz
                        display_meta = check_and_renew_meta(display_meta, batch_meta, frame_meta, "label")
                        li = display_meta.num_labels
                        display_meta.text_params[li].display_text = str(v_id)
                        display_meta.text_params[li].x_offset = mm_x + 9
                        display_meta.text_params[li].y_offset = mm_y - 9
                        display_meta.text_params[li].font_params.font_name = "Arial"
                        display_meta.text_params[li].font_params.font_size = 12
                        display_meta.text_params[li].font_params.font_color.set(1.0, 1.0, 1.0, 1.0)
                        display_meta.text_params[li].set_bg_clr = 1
                        display_meta.text_params[li].text_bg_clr.set(0.0, 0.0, 0.0, 0.7)
                        display_meta.num_labels += 1
                    else:
                        # Bizim listemizde yoksa gri kutu yap (Tanımsız)
                        obj_meta.rect_params.border_width = 1
                        obj_meta.rect_params.border_color.set(0.5, 0.5, 0.5, 0.4)
                        obj_meta.text_params.display_text = ""
                        obj_meta.text_params.set_bg_clr = 0
                else:
                    # Gürültü ise kutuyu sil
                    obj_meta.rect_params.border_width = 0
                    obj_meta.text_params.display_text = ""
            try:
                l_obj = l_obj.next
            except:
                break

        # Son kalan çizimleri de ekle
        pyds.nvds_add_display_meta_to_frame(frame_meta, display_meta)
        try:
            l_frame = l_frame.next
        except:
            break

    return Gst.PadProbeReturn.OK