import sqlite3
import time
import pytz
# import json
import requests
import feedparser
from bs4 import BeautifulSoup
from collections import Counter
from datetime import datetime, timedelta
import telegram

Results = []
YeniHaberler = []

TumKaynaklar = [
    "haberlerVan", "wanhaber", "vanhavadis", "sehrivangazetesi", "vanekspres", "yerelvanhaber", "vansesigazetesi", "vanolay",
    "gazeteduvar", "odatv", "sputnik", "cnnturk", "dunya", "cumhuriyet", "bbc", "aa", "diken", "haberler", "trthaber", "ensonhaber", "haberturk", "sozcu", "ntv",
    "fıratnewsAnf", "yeniyasamgazetesi", "serhatnews", "nuceciwan", "ozgurgelecek", "ihdvan"
]

YerelKaynaklar = [
    {
        "kaynak": "haberlerVan",
        "url": "https://rss.haberler.com/rss.asp?kategori=van"
    },
    {
        "kaynak": "wanhaber",
        "url": "https://www.wanhaber.com/rss/headlines"
    },
    {
        "kaynak": "vanhavadis",
        "url": "https://www.vanhavadis.com/rss.xml"
    },
    {
        "kaynak": "sehrivangazetesi",
        "url": "https://www.sehrivangazetesi.com/rss/headlines"
    },
    {
        "kaynak": "vanekspres",
        "url": "https://www.vanekspres.com.tr/rss/headlines"
    },
    {
        "kaynak": "yerelvanhaber",
        "url": "https://www.yerelvanhaber.com/rss.xml"
    },
    {
        "kaynak": "vansesigazetesi",
        "url": "https://www.vansesigazetesi.com/rss/mansetler/"
    },
    {
        "kaynak": "vanolay",
        "url": "https://www.vanolay.com/rss/headlines"
    },
]
UlusalKaynaklar = [
    {
        "kaynak": "gazeteduvar",
        "url": "https://www.gazeteduvar.com.tr/export/rss"
    },
    {
        "kaynak": "odatv",
        "url": "https://www.odatv.com/rss.xml"
    },
    {
        "kaynak": "sputnik",
        "url": "https://anlatilaninotesi.com.tr/export/rss2/archive/index.xml"
    },
    {
        "kaynak": "cnnturk",
        "url": "https://www.cnnturk.com/feed/rss/all/news"
    },
    {
        "kaynak": "dunya",
        "url": "https://www.dunya.com/rss"
    },
    {
        "kaynak": "cumhuriyet",
        "url": "https://www.cumhuriyet.com.tr/rss"
    },
    {
        "kaynak": "bbc",
        "url": "https://feeds.bbci.co.uk/turkce/rss.xml"
    },
    {
        "kaynak": "aa",
        "url": "https://www.aa.com.tr/tr/rss/default?cat=guncel"
    },
    {
        "kaynak": "diken",
        "url": "https://www.diken.com.tr/feed/"
    },
    {
        "kaynak": "haberler",
        "url": "https://rss.haberler.com/rss.asp?kategori=sondakika"
    },
    {
        "kaynak": "trthaber",
        "url": "https://www.trthaber.com/manset_articles.rss"
    },
    {
        "kaynak": "ensonhaber",
        "url": "https://www.ensonhaber.com/rss/ensonhaber.xml"
    },
    {
        "kaynak": "haberturk",
        "url": "https://www.haberturk.com/rss"
    },
    {
        "kaynak": "sozcu",
        "url": "https://www.sozcu.com.tr/feeds-rss-category-gundem"
    },
    {
        "kaynak": "ntv",
        "url": "https://www.ntv.com.tr/son-dakika.rss"
    },
]
NuzahirKaynaklar = [
    {
        "kaynak": "fıratnewsAnf",
        "url": "https://firatnews.com/feed"
    },
    {
        "kaynak": "yeniyasamgazetesi",
        "url": "https://yeniyasamgazetesi6.com/feed/"
    },
    {
        "kaynak": "serhatnews",
        "url": "https://www.serhatnews.com/feed"
    },
    {
        "kaynak": "nuceciwan",
        "url": "https://www.nuceciwan132.xyz/feed/"
    },
    {
        "kaynak": "ozgurgelecek",
        "url": "https://ozgurgelecek52.net/feed/"
    },
]


def get_current_time_in_format():
    # Türkiye saat dilimine dönüştürelim
    local_timezone = pytz.timezone('Europe/Istanbul')
    current_time = datetime.now(local_timezone)

    # İstenilen formata çevirelim
    formatted_date = current_time.strftime('%Y.%m.%d-%H:%M')
    return formatted_date

def format_date_or_default(published_parsed):
    if published_parsed:
        try:
            if isinstance(published_parsed, datetime):
                # Eğer published_parsed zaten bir datetime nesnesi ise
                local_dt = published_parsed.astimezone(
                    pytz.timezone('Europe/Istanbul'))
            elif isinstance(published_parsed, str):
                # RFC 2822/RFC 5322 formatındaki tarihi parse edelim
                utc_dt = datetime.strptime(
                    published_parsed, "%a, %d %b %Y %H:%M:%S %z")
                local_dt = utc_dt.astimezone(pytz.timezone('Europe/Istanbul'))
            elif isinstance(published_parsed, (tuple, time.struct_time)):
                # Eğer published_parsed uygun formatta ise doğrudan işleme devam
                utc_dt = datetime(*published_parsed[:6], tzinfo=pytz.utc)
                local_dt = utc_dt.astimezone(pytz.timezone('Europe/Istanbul'))
            else:
                raise ValueError(
                    "Tarih formatlama hatası: published_parsed uygun formatta değil.")

            # Şu anki zaman ile karşılaştırma
            now = datetime.now(pytz.timezone('Europe/Istanbul'))

            # Eğer published_parsed zamanından ilerideyse 3 saat geri al
            if local_dt > now:
                local_dt -= timedelta(hours=3)

            return local_dt.strftime('%Y.%m.%d-%H:%M')
        except Exception as e:
            print(f"Tarih formatlama hatası: {e}")
            return get_current_time_in_format()
    else:
        # Eğer tarih bilgisi yoksa, o anın tarihini kullan
        return get_current_time_in_format()

def ihdvan():
    # RSS kaynağını çek
    response = requests.get('https://ihdvan.org/feed/')

    if response.status_code == 200:
        # XML formatında parse edelim
        soup = BeautifulSoup(response.content, 'xml')

        for item in soup.find_all('item'):

            title = item.title.get_text() if item.title else "Başlık yok"
            link = item.link.get_text() if item.link else "Link yok"
            pubDate = item.pubDate.get_text() if item.pubDate else get_current_time_in_format()
            description = item.description.get_text() if item.description else "Açıklama yok"

            formatted_haber_tarih = format_date_or_default(pubDate)

            Results.append({
                "haber_baslik": title,
                "haber_icerik": description,
                "haber_link": link,
                "haber_kaynak": "ihdvan",
                "haber_image": "Resim bulunamadı",
                "haber_tarih": formatted_haber_tarih
            })
    else:
        print(f"RSS kaynağına erişim başarısız: {response.status_code}")

def RssParser(rss_url, haber_kaynak):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
    feed = feedparser.parse(rss_url, request_headers=headers)
    items = feed.entries
    count = 0  # Sayaç
    max_items = 50  # Maksimum öğe sayısı

    for item in items:

        if count >= max_items:
            break  # Sayaç maksimum değere ulaştığında döngüyü kır

        haber_baslik = item.get("title", "").strip()
        haber_icerik = item.get("content", [{}])[0].get(
            "value", "") or item.get("description", "").strip()
        haber_link = item.get("link", "").strip()

        # Resmi bulalım
        haber_image = ""
        if "media_content" in item:
            for media in item["media_content"]:
                # 'type' anahtarının var olup olmadığını kontrol et
                if "type" in media and media["type"] == "image/jpeg":
                    haber_image = media["url"].strip()
                    break

        # Enclosure etiketi altında image varsa onu alalım
        if not haber_image and hasattr(item, "enclosures"):
            if item.enclosures:
                haber_image = item.enclosures[0].get("url", "").strip()

        # item'da image etiketi varsa onu alalım
        if not haber_image and "image" in item:
            haber_image = item.get("image", "").strip()

        # item'da media_thumbnail varsa onu alalım
        if not haber_image and "media_thumbnail" in item:
            if item["media_thumbnail"]:
                haber_image = item["media_thumbnail"][0].get("url", "").strip()

        # 'links' içinde enclosure türündeki resim linkini bulalım
        if not haber_image and "links" in item:
            for link in item["links"]:
                if link.get("rel") == "enclosure" and link.get("type") == "image/jpeg":
                    haber_image = link.get("href", "").strip()
                    break

        # 'content' içinde img etiketini bulalım
        if not haber_image and "content" in item:
            content_list = item.get("content", [])
            if content_list:
                content_html = content_list[0].get("value", "")
                soup = BeautifulSoup(content_html, "html.parser")
                img_tag = soup.find("img")
                if img_tag and img_tag.get("src"):
                    haber_image = img_tag.get("src").strip()

        # 'summary_detail' içinde img etiketini bulalım
        if not haber_image and "summary_detail" in item:
            # summary_html = item.get("summary_detail", {}).get("value", "")
            summary_html = item["summary_detail"]["value"]

            if summary_html:
                soup = BeautifulSoup(summary_html, "html.parser")
                img_tag = soup.find("img")
                if img_tag and img_tag.get("src"):
                    haber_image = img_tag.get("src").strip()
            else:
                print("Summary HTML boş!")

            soup = BeautifulSoup(summary_html, "html.parser")
            img_tag = soup.find("img")
            if img_tag and img_tag.get("src"):
                haber_image = img_tag.get("src").strip()

        if not haber_image:
            haber_image = "Resim bulunamadı"

        # Tarihi alalım
        haber_tarih = ""

        # "published" alanını kontrol edelim
        if "published" in item:
            haber_tarih = item.get("published", "").strip()

        # Eğer "published_parsed" kullanmak istiyorsanız:
        if "published_parsed" in item:
            published_parsed = item.get("published_parsed", None)
            if published_parsed:
                try:
                    # UTC zamanını yerel zamana dönüştürme
                    utc_dt = datetime(*published_parsed[:6], tzinfo=pytz.utc)
                    local_dt = utc_dt.astimezone(
                        pytz.timezone('Europe/Istanbul'))
                    # haber_tarih = local_dt.strftime('%Y.%m.%d-%H:%M')
                    haber_tarih = format_date_or_default(local_dt)
                except Exception as e:
                    print(f"Tarih formatlama hatası: {e}")
                    haber_tarih = get_current_time_in_format()

        # Eğer "haber_tarih" hala boşsa, o anın tarihini kullan
        if not haber_tarih:
            haber_tarih = get_current_time_in_format()

        # Veriyi formatlayıp sonuçlar listesine ekleyelim
        Results.append({
            "haber_baslik": haber_baslik,
            "haber_icerik": haber_icerik,
            "haber_link": haber_link,
            "haber_kaynak": haber_kaynak,
            "haber_image": haber_image,
            "haber_tarih": haber_tarih
        })

        count += 1  # Sayaç artır

def DigerKaynaklarRun():
    ihdvan()

def RssParserRun():

    Results.clear()

    for muzahir in NuzahirKaynaklar:
        RssParser(muzahir["url"], muzahir["kaynak"])

    for ulusal in UlusalKaynaklar:
        RssParser(ulusal["url"], ulusal["kaynak"])

    for yerel in YerelKaynaklar:
        RssParser(yerel["url"], yerel["kaynak"])

    DigerKaynaklarRun()
    ResultsStatistic()

    # Sonuçları bir JSON dosyasına yazalım
    # with open("formatted_items.json", "w", encoding="utf-8") as f:
    #     json.dump(Results, f, ensure_ascii=False, indent=4)

    return Results

def ResultsStatistic():
    # Haber kaynaklarını saymak için Counter kullanıyoruz
    kaynak_sayaci = Counter(item['haber_kaynak'] for item in Results)

    istatistikler = dict(kaynak_sayaci)

    # Toplam kayıt sayısını hesaplayalım
    toplam_kayit_sayisi = sum(kaynak_sayaci.values())

    # Toplam kaynak sayısını hesaplayalım
    toplam_kaynak_sayisi = len(kaynak_sayaci)

    # Eksik kaynakları kontrol et
    eksik_kaynaklar = [
        kaynak for kaynak in TumKaynaklar if kaynak not in kaynak_sayaci]
    eksik_kaynak_sayisi = len(eksik_kaynaklar)

    yeni_haber_sayisi = len(YeniHaberler)

    # Toplam kayıt ve toplam kaynak sayısını ekleyelim
    istatistikler['!toplam_kaynak_sayisi'] = toplam_kaynak_sayisi
    istatistikler['!toplam_kayit_sayisi'] = toplam_kayit_sayisi
    istatistikler['!eksik_kaynak_sayisi'] = eksik_kaynak_sayisi
    istatistikler['!eksik_kaynaklar'] = eksik_kaynaklar
    istatistikler['!yeni_haber_sayisi'] = yeni_haber_sayisi

    # Örnek çıktıyı görmek için:
    print(istatistikler)

def Veritabani():

    # SQLite veritabanını oluştur ve bağlan
    conn = sqlite3.connect('vista.db')
    c = conn.cursor()

    # Eğer tablo yoksa oluştur
    c.execute('''
        CREATE TABLE IF NOT EXISTS haberler (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            haber_baslik TEXT,
            haber_icerik TEXT,
            haber_link TEXT,
            haber_kaynak TEXT,
            haber_image TEXT,
            haber_tarih TEXT,
            haber_gonderildi INTEGER,
            haber_van_gonderildi INTEGER
        )
    ''')

    # Veritabanında zaten var olan haber linklerini çek
    c.execute("SELECT haber_link FROM haberler")
    veritabanindaki_haberler = {row[0] for row in c.fetchall()}

    # Veritabanında olmayan haberleri belirlemek için liste oluştur
    farkli_haberler = [
        haber for haber in Results if haber['haber_link'] not in veritabanindaki_haberler]

    YeniHaberler = farkli_haberler

    # Farklı olan haberleri tekrar veritabanına ekle
    for haber in YeniHaberler:
        c.execute('''
            INSERT INTO haberler (haber_baslik, haber_icerik, haber_link, haber_kaynak, haber_image, haber_tarih,haber_gonderildi,haber_van_gonderildi)
            VALUES (?, ?, ?, ?, ?, ?,?,?)
        ''', (haber['haber_baslik'], haber['haber_icerik'], haber['haber_link'], haber['haber_kaynak'], haber['haber_image'], haber['haber_tarih'], 0, 0))

    # Değişiklikleri kaydet ve veritabanını kapat
    conn.commit()
    conn.close()

def HaberGonder():
    conn = sqlite3.connect('vista.db')
    c = conn.cursor()

    c.execute('SELECT * FROM haberler WHERE haber_gonderildi=0')
    haberler = c.fetchall()

    for haber in haberler:
        baslik = haber[1]
        link = haber[3]

        mesaj = f"{baslik}\n{link}"
        telegram.SendMessage(mesaj)

        # Haberi gönderildi olarak işaretle
        c.execute(
            'UPDATE haberler SET haber_gonderildi=1 WHERE haber_link=?', (haber[3],))
        conn.commit()
        time.sleep(2)
    conn.close()

def VanHaberGonder():
    conn = sqlite3.connect('vista.db')
    c = conn.cursor()

    c.execute("SELECT * FROM haberler WHERE haber_van_gonderildi=0 AND (haber_baslik LIKE '%van%' OR haber_baslik LIKE '%wan%' OR haber_icerik LIKE '%van%' OR haber_icerik LIKE '%wan%')")

    haberler = c.fetchall()

    for haber in haberler:
        baslik = haber[1]
        link = haber[3]

        mesaj = f"{baslik}\n{link}"
        telegram.SendMessageVan(mesaj)

        # Haberi gönderildi olarak işaretle
        c.execute(
            'UPDATE haberler SET haber_van_gonderildi=1 WHERE haber_link=?', (haber[3],))
        conn.commit()
        time.sleep(2)
    conn.close()

while(True):
    baslangic_zamani = time.time()
    RssParserRun()
    Veritabani()
    HaberGonder()
    VanHaberGonder()
    bitis_zamani = time.time()
    gecen_sure = bitis_zamani - baslangic_zamani
    print(f"Kodun çalışması {gecen_sure:.2f} saniye sürdü.")
    time.sleep(600)
