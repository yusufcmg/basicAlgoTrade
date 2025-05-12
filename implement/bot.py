'''
🎯 Alım satım stratejisi: ADX teyitli Bollinger Bantları sıkışması
🔍 Volatilitenin düştüğü (BB sıkışması) anları tespit eder ve ardından kırılımları (breakouts) işleme alır
💥 Sıkışma bittikten sonra güçlü trend yönünü teyit etmek için ADX kullanır

Yasal Uyarı: Bu finansal tavsiye değildir ve hiçbir garanti verilmez. Riski size aittir.
'''

import sys
import os
import time
import schedule
import json
import requests
import pandas as pd
import numpy as np
import traceback
import talib
from termcolor import colored
import colorama
from colorama import Fore, Back, Style
import implement.funcs_n as n
from datetime import datetime, timedelta
import pytz
from eth_account.signers.local import LocalAccount
import eth_account
from dotenv import load_dotenv

parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, parent_dir)

# Terminal renkleri için colorama'yı başlat
colorama.init(autoreset=True)

# .env dosyasından ortam değişkenlerini yükle
load_dotenv()

# Ortam değişkenlerinden Hyperliquid anahtarını al
HYPER_LIQUID_KEY = os.getenv('HYPER_LIQUID_KEY')

# Moon Dev ASCII Sanatı Başlığı
MOON_DEV_BANNER = f"""{Fore.CYAN}
   __  ___                    ____
  /  |/  /___  ____  ____    / __ \\___  _  __
 / /|_/ / __ \\/ __ \\/ __ \\  / / / / _ \\| |/_/
/ /  / / /_/ / /_/ / / / / / /_/ /  __/>  <
/_/  /_/\\____/\\____/_/ /_(_)____/\\___/_/|_|

{Fore.MAGENTA}🚀 BB Squeeze ADX Alım Satım Botu 🌙{Fore.RESET}
"""


SYMBOL = 'BTC'  # Varsayılan sembol, gerektiğinde değiştirilebilir
LEVERAGE = 5     # Alım satım için kullanılacak kaldıraç
POSITION_SIZE_USD = 10  # USD cinsinden pozisyon büyüklüğü (backtest gibi performans göstermesini sağlamak için küçük)

# Strateji parametreleri (geriye dönük test optimizasyonundan)
BB_WINDOW = 20
BB_STD = 2.0
KELTNER_WINDOW = 20
KELTNER_ATR_MULT = 1.5
ADX_PERIOD = 14
ADX_THRESHOLD = 25

# Kâr al ve zarar durdur ayarları
TAKE_PROFIT_PERCENT = 5.0  # %5 - geriye dönük testten
STOP_LOSS_PERCENT = -3.0   # %3 - geriye dönük testten

# Piyasa emri türü
USE_MARKET_ORDERS = False  # Limit emirler için False, piyasa emirleri için True

# Hesabı başlat
account = LocalAccount = eth_account.Account.from_key(HYPER_LIQUID_KEY)

# Alım satım durumu
squeeze_flag = False      # Sıkışma durumunda olup olmadığımızı takip eder
squeeze_released = False  # Bir sıkışmanın yeni bitip bitmediğini takip eder
last_candle_time = None   # En son ne zaman bir mum işlediğimizi takip eder

def print_banner():
    
    print(f"{Fore.CYAN}{'='*80}")
    print(f"{Fore.YELLOW}🚀 BB Squeeze ADX Botu başlıyor! 🎯")
    print(f"{Fore.YELLOW}💰 {SYMBOL} sembolünde {LEVERAGE}x kaldıraç ile işlem yapılıyor")
    print(f"{Fore.YELLOW}💵 Pozisyon büyüklüğü: ${POSITION_SIZE_USD} USD")
    print(f"{Fore.CYAN}{'='*80}\n")

def fetch_klines(symbol, interval='4h', limit=100):
    print(f"{Fore.YELLOW}🔍 , {symbol} için {interval} mumlarını çekiyor... 🕯️")
    try:
        # Bu fonksiyon nice_funcs içinde uygulanmalıdır
        ohlcv = n.get_ohlcv2(symbol, interval, limit)

        if ohlcv is None or len(ohlcv) == 0:
            print(f"{Fore.RED}❌ Mum verisi çekilemedi!")
            return None

        # DataFrame'e dönüştür
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)

        print(f"{Fore.GREEN}✅ {symbol} için {len(df)} adet mum başarıyla çekildi")
        return df

    except Exception as e:
        print(f"{Fore.RED}❌ Mumları çekerken hata oluştu: {str(e)}")
        print(f"{Fore.RED}📋 Hata izi (Stack trace):\n{traceback.format_exc()}")
        return None

def calculate_indicators(df):
    
    try:
        print(f"{Fore.YELLOW}🧮gerekli göstergeleri hesaplıyor... 🧠")

        # Bollinger Bantlarını Hesapla
        df['upper_bb'], df['middle_bb'], df['lower_bb'] = talib.BBANDS(
            df['close'],
            timeperiod=BB_WINDOW,
            nbdevup=BB_STD,
            nbdevdn=BB_STD
        )

        # Keltner Kanalları için ATR Hesapla
        df['atr'] = talib.ATR(
            df['high'],
            df['low'],
            df['close'],
            timeperiod=KELTNER_WINDOW
        )

        # Keltner Kanallarını Hesapla
        df['keltner_middle'] = talib.SMA(df['close'], timeperiod=KELTNER_WINDOW)
        df['upper_kc'] = df['keltner_middle'] + KELTNER_ATR_MULT * df['atr']
        df['lower_kc'] = df['keltner_middle'] - KELTNER_ATR_MULT * df['atr']

        # ADX Hesapla
        df['adx'] = talib.ADX(df['high'], df['low'], df['close'], timeperiod=ADX_PERIOD)

        # Bollinger Band Sıkışmasını Tespit Et
        df['squeeze'] = (df['upper_bb'] < df['upper_kc']) & (df['lower_bb'] > df['lower_kc'])

        print(f"{Fore.GREEN}✅ Moon Dev göstergeleri hesaplamayı bitirdi! 🧙‍♂️")

        return df

    except Exception as e:
        print(f"{Fore.RED}❌ Göstergeleri hesaplarken hata oluştu: {str(e)}")
        print(f"{Fore.RED}📋 Hata izi (Stack trace):\n{traceback.format_exc()}")
        return None

def analyze_market():
    """
    Piyasa koşullarını analiz eder ve BB sıkışma modellerini tespit eder
    """
    global squeeze_flag, squeeze_released

    print(f"\n{Fore.CYAN}{'='*80}")
    print(f"{Fore.CYAN}{'='*25} 🔍 PİYASA ANALİZİ 🔍 {'='*25}")
    print(f"{Fore.CYAN}{'='*80}")

    try:
        # Mum verilerini çek
        df = fetch_klines(SYMBOL, interval='6h', limit=100)
        if df is None:
            return False

        # Göstergeleri hesapla
        df = calculate_indicators(df)
        if df is None:
            return False

        # En son veri noktalarını al
        current_candle = df.iloc[-1]
        previous_candle = df.iloc[-2]

        # Mevcut fiyatı ve gösterge değerlerini yazdır
        print(f"\n{Fore.CYAN}{'='*80}")
        print(f"{Fore.CYAN}{'='*25} 📊 MEVCUT PİYASA DURUMU 📊 {'='*25}")
        print(f"{Fore.CYAN}{'='*80}")
        print(f"{Fore.GREEN}🕯️ Mevcut Kapanış: ${current_candle['close']:.2f}")
        print(f"{Fore.GREEN}📈 ADX Değeri: {current_candle['adx']:.2f} (Eşik: {ADX_THRESHOLD})")
        print(f"{Fore.GREEN}📏 Bollinger Bantları: Üst ${current_candle['upper_bb']:.2f} | Orta ${current_candle['middle_bb']:.2f} | Alt ${current_candle['lower_bb']:.2f}")
        print(f"{Fore.GREEN}📏 Keltner Kanalları: Üst ${current_candle['upper_kc']:.2f} | Orta ${current_candle['keltner_middle']:.2f} | Alt ${current_candle['lower_kc']:.2f}")

        # Sıkışma durumunda olup olmadığımızı kontrol et
        squeeze_now = current_candle['squeeze']
        squeeze_prev = previous_candle['squeeze']

        # Sıkışmanın bitip bitmediğini kontrol et (önceki True, şimdiki False)
        if squeeze_prev and not squeeze_now:
            print(f"\n{Fore.MAGENTA}🚨 UYARI: BB SIKIŞMASI YENİ BİTTİ! 🚨")
            squeeze_released = True
            squeeze_flag = False
        elif squeeze_now:
            print(f"\n{Fore.YELLOW}⚠️ UYARI: Şu anda BB Sıkışmasında! Volatilite daralması devam ediyor...")
            squeeze_flag = True
            squeeze_released = False
        else:
            print(f"\n{Fore.BLUE}ℹ️  BİLGİ: Sıkışma tespit edilmedi. Normal volatilite.")
            squeeze_flag = False

        # ADX trend gücünü göster
        if current_candle['adx'] > ADX_THRESHOLD:
            print(f"{Fore.GREEN}💪 ADX: {current_candle['adx']:.2f} - Güçlü trend tespit edildi! (Eşik: {ADX_THRESHOLD})")
        else:
            print(f"{Fore.YELLOW}👀 ADX: {current_candle['adx']:.2f} - Zayıf/trend yok (Eşik: {ADX_THRESHOLD})")

        # Potansiyel kırılma yönünü kontrol et
        if squeeze_released:
            if current_candle['close'] > current_candle['upper_bb']:
                print(f"{Fore.GREEN}🚀 POTANSİYEL YUKARI YÖNLÜ KIRILMA - Kapanış (${current_candle['close']:.2f}) üst BB'nin (${current_candle['upper_bb']:.2f}) üzerinde")
            elif current_candle['close'] < current_candle['lower_bb']:
                print(f"{Fore.RED}📉 POTANSİYEL AŞAĞI YÖNLÜ KIRILMA - Kapanış (${current_candle['close']:.2f}) alt BB'nin (${current_candle['lower_bb']:.2f}) altında")

        return True

    except Exception as e:
        print(f"{Fore.RED}❌ Piyasa analizi sırasında hata oluştu: {str(e)}")
        print(f"{Fore.RED}📋 Hata izi (Stack trace):\n{traceback.format_exc()}")
        return False

def check_for_entry_signals(df):
    """
    BB sıkışması ve ADX'e göre alım satım giriş sinyallerini kontrol eder
    """
    try:
        # Son iki mumu al
        current = df.iloc[-1]
        previous = df.iloc[-2]

        # Sinyal değişkenlerini başlat
        long_signal = False
        short_signal = False

        # Sıkışmanın yeni bitip bitmediğini kontrol et (sıkışmadaydı ve şimdi değil)
        squeeze_just_released = previous['squeeze'] and not current['squeeze']

        # Eğer sıkışma yeni bittiyse ve ADX trend gücünü teyit ediyorsa
        if squeeze_just_released and current['adx'] > ADX_THRESHOLD:
            print(f"{Fore.MAGENTA}🔎  SİNYAL ANALİZİ: Sıkışma yeni bitti, ADX: {current['adx']:.2f} > {ADX_THRESHOLD} 💪")

            # Kırılma yönünü belirle
            if current['close'] > current['upper_bb']:
                long_signal = True
                print(f"{Fore.GREEN}🚀 UZUN (LONG) SİNYAL TETİKLENDİ! Fiyat üst BB'nin (${current['upper_bb']:.2f}) üzerine çıktı")

            elif current['close'] < current['lower_bb']:
                short_signal = True
                print(f"{Fore.RED}📉 KISA (SHORT) SİNYAL TETİKLENDİ! Fiyat alt BB'nin (${current['lower_bb']:.2f}) altına indi")

        return long_signal, short_signal

    except Exception as e:
        print(f"{Fore.RED}❌ Giriş sinyallerini kontrol ederken hata oluştu: {str(e)}")
        print(f"{Fore.RED}📋 Hata izi (Stack trace):\n{traceback.format_exc()}")
        return False, False

def bot():
    """
    Her döngüde çalışan ana bot fonksiyonu
    """
    try:
        print(f"\n{Fore.CYAN}{'='*80}")
        print(f"{Fore.YELLOW}🌙 Moon Dev'in BB Squeeze ADX Botu - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} 🚀")
        print(f"{Fore.CYAN}{'='*80}")

        # Önce mevcut pozisyonları kontrol et ve yönet
        print(f"\n{Fore.CYAN}🔍 Mevcut pozisyonlar kontrol ediliyor...")
        positions, im_in_pos, mypos_size, pos_sym, entry_px, pnl_perc, is_long = n.get_position(SYMBOL, account)
        print(f"{Fore.CYAN}📊 Mevcut pozisyonlar: {positions}")

        if im_in_pos:
            print(f"{Fore.GREEN}📈 Pozisyonda, kapatma koşulları için Kâr/Zarar (PnL) kontrol ediliyor...")
            print(f"{Fore.YELLOW}💰 Mevcut PnL: {pnl_perc:.2f}% | Kâr Al: {TAKE_PROFIT_PERCENT}% | Zarar Durdur: {STOP_LOSS_PERCENT}%")
            # Kâr/zarar hedeflerine göre kapatmamız gerekip gerekmediğini kontrol et
            n.pnl_close(SYMBOL, TAKE_PROFIT_PERCENT, STOP_LOSS_PERCENT, account)

            # pnl_close pozisyonu kapatmış olabileceğinden, hala pozisyonda olup olmadığımızı tekrar kontrol et
            positions, im_in_pos, mypos_size, pos_sym, entry_px, pnl_perc, is_long = n.get_position(SYMBOL, account)

            if im_in_pos:
                print(f"{Fore.GREEN}✅ Mevcut pozisyon korunuyor: {SYMBOL} {'UZUN (LONG)' if is_long else 'KISA (SHORT)'} {mypos_size} @ ${entry_px} (PnL: {pnl_perc}%)")
                return  # Zaten bir pozisyonda olduğumuz için erken çık
        else:
            print(f"{Fore.YELLOW}📉 Pozisyonda değil, giriş fırsatları aranıyor...")
            # Yeni girişleri analiz etmeden önce bekleyen emirleri iptal et
            n.cancel_all_orders(account)
            print(f"{Fore.YELLOW}🚫 Mevcut tüm emirler iptal edildi")

        # Piyasa verilerini çek ve analiz et
        df = fetch_klines(SYMBOL, interval='6h', limit=100)
        if df is None:
            return

        # Göstergeleri hesapla
        df = calculate_indicators(df)
        if df is None:
            return

        # Giriş sinyallerini kontrol et
        long_signal, short_signal = check_for_entry_signals(df)

        # Eğer bir sinyalimiz varsa ve pozisyonda değilsek, bir işleme gir
        if (long_signal or short_signal) and not im_in_pos:
            # Emir defteri verilerini al
            print(f"\n{Fore.CYAN}📚 Emir defteri verileri çekiliyor...")
            ask, bid, l2_data = n.ask_bid(SYMBOL)
            print(f"{Fore.GREEN}💰 Mevcut fiyat - Alış (Ask): ${ask:.2f}, Satış (Bid): ${bid:.2f}")

            # Kaldıracı ve pozisyon büyüklüğünü ayarla
            lev, pos_size = n.adjust_leverage_usd_size(SYMBOL, POSITION_SIZE_USD, LEVERAGE, account)
            print(f"{Fore.YELLOW}📊 Kaldıraç: {lev}x | Pozisyon büyüklüğü: {pos_size}")

            if long_signal:
                print(f"{Fore.GREEN}🚀 LİMİT ALIM emri ${bid} fiyatından veriliyor...") # Bid kullanılır çünkü en iyi alış fiyatı odur
                n.limit_order(SYMBOL, True, pos_size, bid, False, account)
                print(f"{Fore.GREEN}🎯 Giriş sebebi: ADX teyitli BB Sıkışması kırılması")

            elif short_signal:
                print(f"{Fore.RED}📉 LİMİT SATIŞ emri ${ask} fiyatından veriliyor...") # Ask kullanılır çünkü en iyi satış fiyatı odur
                n.limit_order(SYMBOL, False, pos_size, ask, False, account)
                print(f"{Fore.RED}🎯 Giriş sebebi: ADX teyitli BB Sıkışması aşağı kırılması")

            print(f"{Fore.YELLOW}⏳ Emir verildi, dolması bekleniyor...")
        else:
            if im_in_pos:
                print(f"{Fore.YELLOW}⏳ Zaten pozisyonda, yeni emir verilmedi")
            elif long_signal or short_signal:
                print(f"{Fore.YELLOW}⏳ Sinyal tespit edildi ancak pozisyon mevcut, giriş atlandı")
            else:
                print(f"{Fore.YELLOW}⏳ Giriş sinyali tespit edilmedi, izlemeye devam ediliyor...")

        # Easter egg
        print(f"\n{Fore.MAGENTA}🌕  Sıkışma stratejilerinde sabır anahtardır! 🤖")

    except Exception as e:
        print(f"{Fore.RED}❌ Bot çalıştırılırken hata oluştu: {str(e)}")
        print(f"{Fore.RED}📋 Hata izi (Stack trace):\n{traceback.format_exc()}")

def main():
    """Bot için ana giriş noktası"""
    # Başlığı göster
    print_banner()

    # Başlangıç piyasa analizi
    print(f"{Fore.YELLOW}🔍 başlangıç piyasa analizini gerçekleştiriyor...")
    analyze_market()

    # İlk bot çalıştırması
    print(f"{Fore.YELLOW}🚀 İlk  bot döngüsü başlatılıyor...")
    bot()

    # Botun her dakika çalışmasını planla
    schedule.every(1).minutes.do(bot)

    # Piyasa analizinin saatlik çalışmasını planla
    schedule.every(1).hours.do(analyze_market)

    print(f"{Fore.GREEN}✅ Bot her dakika çalışacak şekilde planlandı")
    print(f"{Fore.GREEN}✅ Piyasa analizi her saat çalışacak şekilde planlandı")

    while True:
        try:
            # Bekleyen planlanmış görevleri çalıştır
            schedule.run_pending()
            time.sleep(1)
        except KeyboardInterrupt:
            print(f"{Fore.YELLOW}⚠️ Bot kullanıcı tarafından durduruldu")
            break
        except Exception as e:
            print(f"{Fore.RED}❌ Bir hatayla karşılaşıldı: {e}")
            print(f"{Fore.RED}📋 Hata izi (Stack trace):\n{traceback.format_exc()}")
            # Hızlı hata kaydını önlemek için yeniden denemeden önce bekle
            time.sleep(10)

if __name__ == "__main__":
    main()