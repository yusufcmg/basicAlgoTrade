'''
HYPERLIQUID'DEN ALABİLECEĞİNİZ MAKSİMUM VERİ  5000 MUM DUR.
DAHA FAZLASINA İHTİYACINIZ VARSA COINBASE SCRİPTİNİ KULLANIN
'''
import pandas as pd  
import requests      
from datetime import datetime, timedelta 
import numpy as np   
import time          
import sys
import os    
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'implement'))
import funcs_n as n

symbol = 'BTC'     # kripto para sembolü 
timeframe = '15m'   # 1 günlük mumlar


# BATCH_SIZE = 100000 # HYPERLIQUID İÇİN MAKSİMUM 5000, DAHA FAZLASI İÇİN COINBASE KULLANIN
#                  # tek bir API isteğinde alınacak maksimum mum sayısı
# MAX_RETRIES = 3   # başarısız bir API isteği için maksimum yeniden deneme sayısı
# MAX_ROWS = 1000000   # sonuçta elde edilecek maksimum satır sayısını sınırlamak için yeni bir sabit

# # Zaman damgası farkını saklamak için global değişken
# timestamp_offset = None # API'den gelen zaman damgalarındaki olası bir hatayı düzeltmek için kullanılacak fark

# def adjust_timestamp(dt):
#     # Bu fonksiyon, API'den gelen zaman damgalarını düzeltir.
#     if timestamp_offset is not None: # Eğer bir fark hesaplanmışsa
#         corrected_dt = dt - timestamp_offset  #zaman damgasını düzelt
#         return corrected_dt
#     else:
#         return dt  

# def get_ohlcv2(symbol, interval, start_time, end_time, batch_size=BATCH_SIZE):
#     # Bu fonksiyon Hyperliquid API'sinden OHLCV verilerini çeker.
#     global timestamp_offset 
#     print(f'\n🔍 Veri talep ediliyor:')
#     print(f'📊 Parti Boyutu (Batch Size): {batch_size}')
#     print(f'🚀 Başlangıç: {start_time.strftime("%Y-%m-%d %H:%M:%S")} UTC') 
#     print(f'🎯 Bitiş: {end_time.strftime("%Y-%m-%d %H:%M:%S")} UTC')  

#     # milisaniye cinsinden zamana çevir
#     start_ts = int(start_time.timestamp() * 1000)
#     end_ts = int(end_time.timestamp() * 1000)

#     # API isteğini en fazla MAX_RETRIES kadar dene
#     for attempt in range(MAX_RETRIES):
#         try:
#             # Hyperliquid API'sine POST isteği gönder
#             response = requests.post(
#                 'https://api.hyperliquid.xyz/info', 
#                 headers={'Content-Type': 'application/json'}, # İstek başlığı
#                 json={ # JSON formatında istek gövdesi
#                     "type": "candleSnapshot", # mum verisi istendiğini belirtir
#                     "req": {
#                         "coin": symbol,        # Sembol 
#                         "interval": interval,  # Zaman aralığı 
#                         "startTime": start_ts, # Başlangıç zaman damgası
#                         "endTime": end_ts,     # Bitiş zaman damgası
#                         "limit": batch_size    # İstenen maksimum mum sayısı
#                     }
#                 },
#                 timeout=10 
#             )

#             if response.status_code == 200: # İstek başarılıysa (HTTP 200 OK)
#                 print("veriler çekiliyor")
#                 snapshot_data = response.json() 
#                 if snapshot_data: # API'den veri döndüyse
#                     if timestamp_offset is None:
#                         latest_api_timestamp = datetime.utcfromtimestamp(snapshot_data[-1]['t'] / 1000)
#                         # Sisteminizin şu anki tarihi (kendi güncel tarihinize göre ayarlayın)
#                         system_current_date = datetime.utcnow()
#                         # Beklenen en son zaman damgasını manuel olarak ayarla (örn: şimdi)
#                         expected_latest_timestamp = system_current_date
                        
#                         timestamp_offset = latest_api_timestamp - expected_latest_timestamp
#                         print(f"⏱️ Hesaplanan zaman damgası farkı: {timestamp_offset}")

#                     # API hatası nedeniyle zaman damgalarını ayarla
#                     for candle in snapshot_data:
#                         dt = datetime.utcfromtimestamp(candle['t'] / 1000) # Mumun zaman damgasını datetime nesnesine çevir
#                         # Tarihi ayarla
#                         adjusted_dt = adjust_timestamp(dt) # adjust_timestamp fonksiyonu ile düzelt
#                         candle['t'] = int(adjusted_dt.timestamp() * 1000) # Düzeltilmiş zamanı tekrar milisaniye cinsinden ata

#                     # Alınan verinin ilk ve son zaman damgalarını yazdır (düzeltilmiş)
#                     first_time = datetime.utcfromtimestamp(snapshot_data[0]['t'] / 1000)
#                     last_time = datetime.utcfromtimestamp(snapshot_data[-1]['t'] / 1000)
#                     print(f'✨ {len(snapshot_data)} adet mum alındı')
#                     print(f'📈 İlk: {first_time}')
#                     print(f'📉 Son: {last_time}')
#                     return snapshot_data # Alınan veriyi (mum listesi) döndür
#                 else:
#                     print('❌ API tarafından veri döndürülmedi')
#                     return None # Veri yoksa None döndür
#             else: # HTTP hatası varsa
#                 print(f'⚠️ HTTP Hatası {response.status_code}: {response.text}')
#         except requests.exceptions.RequestException as e: # İstek sırasında bir hata oluşursa
#             print(f'⚠️ İstek başarısız oldu (deneme {attempt + 1}): {e}')
#             time.sleep(1) # 1 saniye bekle ve tekrar dene
#     return None # Tüm denemeler başarısız olursa None döndür

# def process_data_to_df(snapshot_data):
#     # Bu fonksiyon, API'den gelen ham veriyi pandas dataFrameine dönüştürür.
#     if snapshot_data: 
#         columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume'] 
#         data = [] 
#         for snapshot in snapshot_data: 
#             # Verileri ilgili değişkenlere ata
#             timestamp = datetime.utcfromtimestamp(snapshot['t'] / 1000)
#             open_price = snapshot['o'] 
#             high_price = snapshot['h'] 
#             low_price = snapshot['l'] 
#             close_price = snapshot['c'] 
#             volume = snapshot['v'] 
#             data.append([timestamp, open_price, high_price, low_price, close_price, volume]) 

#         df = pd.DataFrame(data, columns=columns) 
#         return df
#     else:
#         return pd.DataFrame() 

# def fetch_historical_data(symbol, timeframe):
#     """5000 satır geçmiş veri çeker."""
#     # Bu ana fonksiyon, veri çekme işlemini yönetir.
#     print("\n🌙 Geçmiş Veri Çekici")
#     print(f"🎯 Sembol: {symbol}")
#     print(f"⏰ Zaman Aralığı: {timeframe}")

#     # Sadece en son 5000 mumu çek
#     end_time = datetime.utcnow() # Bitiş zamanı olarak şu anki UTC zamanını al
#     # Geniş bir zaman aralığı belirleyerek yeterli veri almayı hedefler.
#     # API tek seferde 5000 mum getireceği için, bu aralık 5000 mumu kapsayacak kadar geniş olmalı.
#     start_time = end_time - timedelta(days=5000) # Örnek olarak son 60 günü kapsayan bir başlangıç zamanı

#     print("\n🔄 Veri çekiliyor:")
#     print(f"📅 Başlangıç: {start_time.strftime('%Y-%m-%d %H:%M:%S')} UTC")
#     print(f"📅 Bitiş: {end_time.strftime('%Y-%m-%d %H:%M:%S')} UTC")

#     # get_ohlcv2 fonksiyonunu kullanarak veriyi çek
#     # batch_size=5000 ile tek bir istekte maksimum mumu almayı hedefler.

#     #data = get_ohlcv2(symbol, timeframe, start_time, end_time, batch_size=5000)
#     data = n.get_historical_data_iterative(symbol, timeframe, 10000)

    
    
#     if data.empty: 
#         print("❌ Veri mevcut değil.")
#         return pd.DataFrame() 

#     # Çekilen ham veriyi DataFrame'e dönüştür
#     df = process_data_to_df(data)

#     if not df.empty: # DataFrame boş değilse
#         # Zaman damgasına göre sırala ve en son 5000 satırı al, sonra tekrar zaman damgasına göre sırala
        
#         df = df.sort_values('timestamp', ascending=False).head(5000).sort_values('timestamp')
#         df = df.reset_index(drop=True) # DataFrame indeksini sıfırla

#         print("\n📊 Nihai veri özeti:")
#         print(f"📈 Toplam mum sayısı: {len(df)}")
#         print(f"📅 Tarih aralığı: {df['timestamp'].min()} ile {df['timestamp'].max()}")
        

#     return df 


# # fetch_historical_data fonksiyonunu çağırarak BTC için 1 günlük verileri çek
# all_data = fetch_historical_data(symbol, timeframe)

# # Veriyi kaydet
# if not all_data.empty: # Eğer veri başarıyla çekildiyse
#     # Dosya adı için şu anki UTC zaman damgasını oluştur
#     timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
#     # Mevcut klasöre doğrudan kaydetmek için güncellenmiş yol
#     file_path = f'C:/masaustu/basicAlgoTrade/backtest/data/guncel{symbol}_{timeframe}_{timestamp}_historical.csv' # kendi klasor yolunuz
#     all_data.to_csv(file_path, index=False) # DataFrame'i CSV dosyasına kaydet (indeks olmadan)
#     print(f'\n💾 Veri {file_path} adresine kaydedildi 🚀')
# else: 
#     print('❌  Kaydedilecek veri yok. Daha sonra tekrar deneyin! 🌙')
'''
HYPERLIQUID'DEN ALABİLECEĞİNİZ MAKSİMUM VERİ  5000 MUM DUR.
DAHA FAZLASINA İHTİYACINIZ VARSA COINBASE SCRİPTİNİ KULLANIN
'''
import pandas as pd
# requests artık burada doğrudan kullanılmıyor, funcs_n içinde
from datetime import datetime, timedelta
# numpy ve time artık burada doğrudan kullanılmıyor gibi, funcs_n içinde olabilir
import sys
import os

# --- nice_funcs (funcs_n) import kısmı ---
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'implement'))
try:
    import funcs_n as n
    # print(f"'funcs_n.py' başarıyla import edildi.") # Bu satırı test sonrası kaldırabilirsiniz
except ImportError as e:
    print(f"Hata: 'implement' klasöründen modül import edilemedi. {e}")
    exit()
# --- Bitti: nice_funcs (funcs_n) import kısmı ---

symbol = 'BTC'
timeframe = '15m'
TOTAL_CANDLES_TO_FETCH = 10000 # funcs_n.get_historical_data_iterative'e geçilecek mum sayısı

# ----- BU FONKSİYONLARA ARTIK data.py İÇİNDE İHTİYAÇ YOK (funcs_n.py'de benzerleri var veya işlevleri değişti) -----
# def adjust_timestamp(dt):
#     ...
# def get_ohlcv2(symbol, interval, start_time, end_time, batch_size=BATCH_SIZE):
#     ...
# def process_data_to_df(snapshot_data): # <<<--- BU FONKSİYONU TAMAMEN SİLİN VEYA YORUM YAPIN
#     # if snapshot_data: # BURASI DataFrame ile çağrıldığı için HATA VERİYORDU
#     #     ...
#     # else:
#     #     return pd.DataFrame()
# ----- Bitti: İHTİYAÇ OLMAYAN FONKSİYONLAR -----


def fetch_historical_data_from_source(symbol_param, timeframe_param, num_candles_to_get): # Fonksiyon adını değiştirdim, daha açıklayıcı
    """
    Belirtilen kaynaktan (şu anda funcs_n aracılığıyla Hyperliquid)
    geçmiş mum verilerini çeker.
    """
    print("\n🌙 Geçmiş Veri Çekici (funcs_n üzerinden)")
    print(f"🎯 Sembol: {symbol_param}")
    print(f"⏰ Zaman Aralığı: {timeframe_param}")
    print(f"🔢 İstenen Mum Sayısı: {num_candles_to_get}")

    # Doğrudan funcs_n'den DataFrame'i al
    df = n.get_historical_data_iterative(symbol_param, timeframe_param, num_candles_to_get)

    if df.empty:
        print("❌ Veri mevcut değil veya funcs_n.get_historical_data_iterative'den boş DataFrame döndü.")
        return pd.DataFrame() # Boş DataFrame döndür

    # process_data_to_df çağrısı ARTIK YOK. df zaten bir DataFrame.

    # Eğer burada özellikle son X mumu almak gibi bir mantığınız varsa, onu burada yapabilirsiniz.
    # Ancak get_historical_data_iterative zaten total_candles_needed kadarını getirmeyi hedefliyor.
    # Örneğin, API 5000 limitine rağmen 10000 istediysek ve funcs_n 10000 getirdiyse,
    # burada tekrar head(5000) yapmak veri kaybına neden olur.
    # Şimdilik bu kısmı yorumluyorum, çünkü get_historical_data_iterative'in amacı bu.
    #
    # if not df.empty:
    #     # df = df.sort_values('timestamp', ascending=False).head(5000).sort_values('timestamp')
    #     # df = df.reset_index(drop=True)
    #     print("\n📊 Nihai veri özeti (işlem sonrası):") # Bu mesaj da yanıltıcı olabilir
    #     print(f"📈 Toplam mum sayısı: {len(df)}")
    #     if not df.empty:
    #          print(f"📅 Tarih aralığı: {df['timestamp'].min()} ile {df['timestamp'].max()}")

    return df


# --- Ana Çalıştırma Bloğu ---
if __name__ == "__main__": # Script doğrudan çalıştırıldığında bu blok çalışsın
    print('sup dawg') # Test mesajı, kaldırılabilir

    # fetch_historical_data_from_source fonksiyonunu çağır
    all_data = fetch_historical_data_from_source(symbol, timeframe, TOTAL_CANDLES_TO_FETCH)

    if not all_data.empty:
        timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        save_directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
        if not os.path.exists(save_directory):
            os.makedirs(save_directory)
            print(f"'{save_directory}' klasörü oluşturuldu.")

        file_name = f"guncel{symbol.replace('/', '_')}_{timeframe}_{timestamp_str}_historical.csv"
        file_path = os.path.join(save_directory, file_name)

        all_data.to_csv(file_path, index=False)
        print(f'\n💾 Veri {file_path} adresine kaydedildi 🚀')
    else:
        print('❌ Kaydedilecek veri yok. Daha sonra tekrar deneyin! 🌙')