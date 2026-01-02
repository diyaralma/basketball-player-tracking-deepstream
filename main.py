import sys
import gi
# Görsel işleri yaptığımız diğer dosyayı buraya dahil ediyoruz
import visual_utils

gi.require_version('Gst', '1.0')
from gi.repository import GObject, Gst


def main():
    # GStreamer kütüphanesini başlatıyoruz
    Gst.init(None)

    print("Program başlatılıyor... Pipeline kuruluyor.")

    # Boş bir pipeline (boru hattı) oluşturuyoruz
    pipeline = Gst.Pipeline()

    # --- 1. ELEMANLARI OLUŞTURMA ---
    # Videoyu dosyadan okumak için 'filesrc' kullanıyoruz
    source = Gst.ElementFactory.make("filesrc", "file-source")
    source.set_property('location', "output.h264")  # Okunacak dosya

    # H264 formatını ayrıştırmak için parser
    h264parser = Gst.ElementFactory.make("h264parse", "h264-parser")

    # Videoyu çözmek (decode) için NVIDIA decoder
    decoder = Gst.ElementFactory.make("nvv4l2decoder", "nvv4l2-decoder")

    # Yayınları birleştirmek için muxer (Tek video olsa bile DeepStream için şart)
    streammux = Gst.ElementFactory.make("nvstreammux", "Stream-muxer")
    streammux.set_property('width', 1920)
    streammux.set_property('height', 1080)
    streammux.set_property('batch-size', 1)  # Tek video işliyoruz

    # Yapay zeka modeli (İnsan tespiti için)
    pgie = Gst.ElementFactory.make("nvinfer", "primary-inference")
    pgie.set_property('config-file-path', "config_peoplenet.txt")

    # Takip algoritması (Tracker)
    tracker = Gst.ElementFactory.make("nvtracker", "tracker")
    # Gerekli kütüphane ve ayar dosyalarını gösteriyoruz
    tracker.set_property('ll-lib-file', '/opt/nvidia/deepstream/deepstream/lib/libnvds_nvmultiobjecttracker.so')
    tracker.set_property('ll-config-file', 'config_tracker_basketball.yml')
    tracker.set_property('tracker-width', 640)
    tracker.set_property('tracker-height', 384)

    # Görüntü formatını çevirici
    nvvidconv = Gst.ElementFactory.make("nvvideoconvert", "convertor")

    # Ekrana kutu ve yazı çizdiren eleman (OSD)
    nvosd = Gst.ElementFactory.make("nvdsosd", "onscreendisplay")

    # Sonucu ekrana basmak için (Sink)
    sink = Gst.ElementFactory.make("nveglglessink", "nvvideo-renderer")
    sink.set_property('sync', 0)  # Gecikme olmasın diye senkronizasyonu kapattım
    sink.set_property('qos', 0)

    # --- 2. PIPELINE'A EKLEME ---
    # Oluşturduğumuz tüm parçaları pipeline kutusuna atıyoruz
    pipeline.add(source)
    pipeline.add(h264parser)
    pipeline.add(decoder)
    pipeline.add(streammux)
    pipeline.add(pgie)
    pipeline.add(tracker)
    pipeline.add(nvosd)
    pipeline.add(sink)

    # --- 3. BAĞLANTILARI YAPMA ---
    # Parçaları sırasıyla birbirine bağlıyoruz (Link)
    source.link(h264parser)
    h264parser.link(decoder)

    # Decoder ve Muxer'ı bağlamak biraz farklı, pad (uç) isteyerek yapıyoruz
    srcpad = decoder.get_static_pad("src")
    sinkpad = streammux.request_pad_simple("sink_0")
    srcpad.link(sinkpad)

    streammux.link(pgie)
    pgie.link(tracker)

    # --- 4. ÖZEL GÖRSEL İŞLEMLER ---
    # visual_utils dosyasındaki fonksiyonu kullanarak Minimap'i araya ekliyoruz
    # Tracker -> Minimap -> OSD -> Sink şeklinde bağlıyoruz
    minimap_output_element = visual_utils.add_minimap_overlay(pipeline, tracker, "court.jpg")
    minimap_output_element.link(nvosd)
    nvosd.link(sink)

    # --- 5. ÇİZİM PROBE'U EKLEME ---
    # OSD'nin girişine bir "kanca" (probe) atıyoruz.
    # Böylece her kare çizilmeden önce araya girip istatistik tablosunu ekleyebileceğiz.
    osd_sink_pad = nvosd.get_static_pad("sink")
    osd_sink_pad.add_probe(Gst.PadProbeType.BUFFER, visual_utils.tiler_sink_pad_buffer_probe, 0)

    # --- 6. ÇALIŞTIRMA ---
    loop = GObject.MainLoop()
    pipeline.set_state(Gst.State.PLAYING)  # Motoru çalıştır

    try:
        loop.run()  # Programı döngüye sok
    except:
        pass

    # Çıkışta temizlik yap
    pipeline.set_state(Gst.State.NULL)
    print("Program kapatıldı.")


if __name__ == '__main__':
    main()