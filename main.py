import sqlite3
import time
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
import requests

# Veritabanı bağlantısı kur
conn = sqlite3.connect('haberler.db')
c = conn.cursor()

# Haber tablosunu oluştur
c.execute('''CREATE TABLE IF NOT EXISTS haberler
             (id INTEGER PRIMARY KEY, baslik TEXT, link TEXT, gonderildi INTEGER)''')
conn.commit()

# Telegram bot bilgileri
telegram_token = '7538919434:AAEOtLBkWDDzaduu34RjfZqV-MzpT44nT0s'
chat_id = '-4261255235'

# Web kazıma fonksiyonu
def haberleri_kaz():
    
    # Firefox profili için yol
    profile_path = "C:\\projects\\vista\\profile"
    driver_path = "C:\\projects\\vista\\driver\\geckodriver.exe"

    # Firefox seçenekleri ve profilini ayarlama
    options = Options()
    options.profile = profile_path

    # Geckodriver yolunu belirle (geckodriver.exe'nin tam yolu)
    service = Service(driver_path)

    # Firefox WebDriver'ı başlat
    driver = webdriver.Firefox(service=service, options=options)

    # Test için bir siteye git
    driver.get("https://youtube.com")

    # İşlemden sonra driver'ı kapat
    driver.quit()

# Telegram'dan haber gönderme fonksiyonu
def haber_gonder():
    
    mesaj = "{baslik}\n{link}"
    url = f'https://api.telegram.org/bot{telegram_token}/sendMessage?chat_id={chat_id}&text={mesaj}'
    requests.get(url)
        
        
    # c.execute('SELECT * FROM haberler WHERE gonderildi=0')
    # haberler = c.fetchall()

    # for haber in haberler:
    #     baslik = haber[1]
    #     link = haber[2]

    #     mesaj = f"{baslik}\n{link}"
    #     url = f'https://api.telegram.org/bot{telegram_token}/sendMessage?chat_id={chat_id}&text={mesaj}'
    #     requests.get(url)

    #     # Haberi gönderildi olarak işaretle
    #     c.execute('UPDATE haberler SET gonderildi=1 WHERE id=?', (haber[0],))
    #     conn.commit()

# Sürekli çalışan döngü
while True:
    # haberleri_kaz()
    haber_gonder()
    time.sleep(600)  # 10 dakika bekle
