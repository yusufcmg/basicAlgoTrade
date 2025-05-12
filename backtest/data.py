'''
HYPERLIQUID'DEN ALABİLECEĞİNİZ MAKSİMUM VERİ  5000 MUM DUR.
DAHA FAZLASINA İHTİYACINIZ VARSA COINBASE SCRİPTİNİ KULLANIN
'''
import pandas as pd  
import requests      
from datetime import datetime, timedelta 
import numpy as np   
import time          
import os          


symbol = 'BTC'     # kripto para sembolü 
timeframe = '1d'   # 1 günlük mumlar


BATCH_SIZE = 5000 # HYPERLIQUID İÇİN MAKSİMUM 5000, DAHA FAZLASI İÇİN COINBASE KULLANIN
                 # tek bir API isteğinde alınacak maksimum mum sayısı
MAX_RETRIES = 3   # başarısız bir API isteği için maksimum yeniden deneme sayısı
MAX_ROWS = 5000   # sonuçta elde edilecek maksimum satır sayısını sınırlamak için yeni bir sabit

# Zaman damgası farkını saklamak için global değişken
timestamp_offset = None # API'den gelen zaman damgalarındaki olası bir hatayı düzeltmek için kullanılacak fark

def adjust_timestamp(dt):
    # Bu fonksiyon, API'den gelen zaman damgalarını düzeltir.
    if timestamp_offset is not None: # Eğer bir fark hesaplanmışsa
        corrected_dt = dt - timestamp_offset  #zaman damgasını düzelt
        return corrected_dt
    else:
        return dt  

def get_ohlcv2(symbol, interval, start_time, end_time, batch_size=BATCH_SIZE):
    # Bu fonksiyon Hyperliquid API'sinden OHLCV verilerini çeker.
    global timestamp_offset 
    print(f'\n🔍 Veri talep ediliyor:')
    print(f'📊 Parti Boyutu (Batch Size): {batch_size}')
    print(f'🚀 Başlangıç: {start_time.strftime("%Y-%m-%d %H:%M:%S")} UTC') 
    print(f'🎯 Bitiş: {end_time.strftime("%Y-%m-%d %H:%M:%S")} UTC')  

    # milisaniye cinsinden zamana çevir
    start_ts = int(start_time.timestamp() * 1000)
    end_ts = int(end_time.timestamp() * 1000)

    # API isteğini en fazla MAX_RETRIES kadar dene
    for attempt in range(MAX_RETRIES):
        try:
            # Hyperliquid API'sine POST isteği gönder
            response = requests.post(
                'https://api.hyperliquid.xyz/info', 
                headers={'Content-Type': 'application/json'}, # İstek başlığı
                json={ # JSON formatında istek gövdesi
                    "type": "candleSnapshot", # mum verisi istendiğini belirtir
                    "req": {
                        "coin": symbol,        # Sembol 
                        "interval": interval,  # Zaman aralığı 
                        "startTime": start_ts, # Başlangıç zaman damgası
                        "endTime": end_ts,     # Bitiş zaman damgası
                        "limit": batch_size    # İstenen maksimum mum sayısı
                    }
                },
                timeout=10 
            )

            if response.status_code == 200: # İstek başarılıysa (HTTP 200 OK)
                snapshot_data = response.json() 
                if snapshot_data: # API'den veri döndüyse
                    if timestamp_offset is None:
                        latest_api_timestamp = datetime.utcfromtimestamp(snapshot_data[-1]['t'] / 1000)
                        # Sisteminizin şu anki tarihi (kendi güncel tarihinize göre ayarlayın)
                        system_current_date = datetime.utcnow()
                        # Beklenen en son zaman damgasını manuel olarak ayarla (örn: şimdi)
                        expected_latest_timestamp = system_current_date
                        
                        timestamp_offset = latest_api_timestamp - expected_latest_timestamp
                        print(f"⏱️ Hesaplanan zaman damgası farkı: {timestamp_offset}")

                    # API hatası nedeniyle zaman damgalarını ayarla
                    for candle in snapshot_data:
                        dt = datetime.utcfromtimestamp(candle['t'] / 1000) # Mumun zaman damgasını datetime nesnesine çevir
                        # Tarihi ayarla
                        adjusted_dt = adjust_timestamp(dt) # adjust_timestamp fonksiyonu ile düzelt
                        candle['t'] = int(adjusted_dt.timestamp() * 1000) # Düzeltilmiş zamanı tekrar milisaniye cinsinden ata

                    # Alınan verinin ilk ve son zaman damgalarını yazdır (düzeltilmiş)
                    first_time = datetime.utcfromtimestamp(snapshot_data[0]['t'] / 1000)
                    last_time = datetime.utcfromtimestamp(snapshot_data[-1]['t'] / 1000)
                    print(f'✨ {len(snapshot_data)} adet mum alındı')
                    print(f'📈 İlk: {first_time}')
                    print(f'📉 Son: {last_time}')
                    return snapshot_data # Alınan veriyi (mum listesi) döndür
                else:
                    print('❌ API tarafından veri döndürülmedi')
                    return None # Veri yoksa None döndür
            else: # HTTP hatası varsa
                print(f'⚠️ HTTP Hatası {response.status_code}: {response.text}')
        except requests.exceptions.RequestException as e: # İstek sırasında bir hata oluşursa
            print(f'⚠️ İstek başarısız oldu (deneme {attempt + 1}): {e}')
            time.sleep(1) # 1 saniye bekle ve tekrar dene
    return None # Tüm denemeler başarısız olursa None döndür

def process_data_to_df(snapshot_data):
    # Bu fonksiyon, API'den gelen ham veriyi pandas dataFrameine dönüştürür.
    if snapshot_data: 
        columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume'] 
        data = [] 
        for snapshot in snapshot_data: 
            # Verileri ilgili değişkenlere ata
            timestamp = datetime.utcfromtimestamp(snapshot['t'] / 1000)
            open_price = snapshot['o'] 
            high_price = snapshot['h'] 
            low_price = snapshot['l'] 
            close_price = snapshot['c'] 
            volume = snapshot['v'] 
            data.append([timestamp, open_price, high_price, low_price, close_price, volume]) 

        df = pd.DataFrame(data, columns=columns) 
        return df
    else:
        return pd.DataFrame() 

def fetch_historical_data(symbol, timeframe):
    """5000 satır geçmiş veri çeker."""
    # Bu ana fonksiyon, veri çekme işlemini yönetir.
    print("\n🌙 Geçmiş Veri Çekici")
    print(f"🎯 Sembol: {symbol}")
    print(f"⏰ Zaman Aralığı: {timeframe}")

    # Sadece en son 5000 mumu çek
    end_time = datetime.utcnow() # Bitiş zamanı olarak şu anki UTC zamanını al
    # Geniş bir zaman aralığı belirleyerek yeterli veri almayı hedefler.
    # API tek seferde 5000 mum getireceği için, bu aralık 5000 mumu kapsayacak kadar geniş olmalı.
    start_time = end_time - timedelta(days=60) # Örnek olarak son 60 günü kapsayan bir başlangıç zamanı

    print("\n🔄 Veri çekiliyor:")
    print(f"📅 Başlangıç: {start_time.strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print(f"📅 Bitiş: {end_time.strftime('%Y-%m-%d %H:%M:%S')} UTC")

    # get_ohlcv2 fonksiyonunu kullanarak veriyi çek
    # batch_size=5000 ile tek bir istekte maksimum mumu almayı hedefler.
    data = get_ohlcv2(symbol, timeframe, start_time, end_time, batch_size=5000)
    
    if not data: 
        print("❌ Veri mevcut değil.")
        return pd.DataFrame() 

    # Çekilen ham veriyi DataFrame'e dönüştür
    df = process_data_to_df(data)

    if not df.empty: # DataFrame boş değilse
        # Zaman damgasına göre sırala ve en son 5000 satırı al, sonra tekrar zaman damgasına göre sırala
        
        df = df.sort_values('timestamp', ascending=False).head(5000).sort_values('timestamp')
        df = df.reset_index(drop=True) # DataFrame indeksini sıfırla

        print("\n📊 Nihai veri özeti:")
        print(f"📈 Toplam mum sayısı: {len(df)}")
        print(f"📅 Tarih aralığı: {df['timestamp'].min()} ile {df['timestamp'].max()}")
        

    return df 


# fetch_historical_data fonksiyonunu çağırarak BTC için 1 günlük verileri çek
all_data = fetch_historical_data(symbol, timeframe)

# Veriyi kaydet
if not all_data.empty: # Eğer veri başarıyla çekildiyse
    # Dosya adı için şu anki UTC zaman damgasını oluştur
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    # Mevcut klasöre doğrudan kaydetmek için güncellenmiş yol
    file_path = f'C:/masaustu/basicAlgoTrade/backtest/data/{symbol}_{timeframe}_{timestamp}_historical.csv' # kendi klasor yolunuz
    all_data.to_csv(file_path, index=False) # DataFrame'i CSV dosyasına kaydet (indeks olmadan)
    print(f'\n💾 Veri {file_path} adresine kaydedildi 🚀')
else: 
    print('❌  Kaydedilecek veri yok. Daha sonra tekrar deneyin! 🌙')