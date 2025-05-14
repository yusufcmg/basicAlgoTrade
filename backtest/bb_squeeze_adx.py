import pandas as pd  
import numpy as np   
import talib         
from backtesting import Backtest, Strategy 
from backtesting.lib import crossover      

#verinin yüklenmesi
data_path = 'C:\\masaustu\\basicAlgoTrade\\backtest\\data\\guncelBTC_15m_20250513_164047_historical.csv'
# CSV dosyasını oku, 'datetime' sütununu tarih/saat olarak ayrıştır ve bu sütunu indeks yap
print(f"Kullanılan data_path: {data_path}")
data = pd.read_csv(data_path, parse_dates=['timestamp'], index_col='timestamp', skipinitialspace=True)


class BBSqueezeADX(Strategy):
    
    bb_window = 20          # Bollinger Bandı için pencere boyutu (periyot)
    bb_std = 2.0            # Bollinger Bandı için standart sapma sayısı
    keltner_window = 20     # Keltner Kanalı için pencere boyutu
    keltner_atr_mult = 1.5  # Keltner Kanalı için ATR (Average True Range) çarpanı
    adx_period = 14         # ADX (Average Directional Index) için periyot
    adx_threshold = 25      # ADX için trend gücü eşiği
    take_profit = 0.05      # Kâr al hedefi (%5)
    stop_loss = 0.03        # Zarar durdurma hedefi (%3)
    trade_size_percentage = 0.0001
    
    def init(self):
        # Bollinger Bantlarını Hesapla
        self.upper_bb, self.middle_bb, self.lower_bb = self.I(talib.BBANDS, 
                                                            self.data.Close, 
                                                            self.bb_window, 
                                                            self.bb_std, 
                                                            self.bb_std)
        
        # Keltner Kanalları için ATR'yi Hesapla
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, 
                          self.data.Close, self.keltner_window)
        
        # Keltner Kanallarını Hesapla
        # Keltner orta bandı (genellikle bir SMA - Basit Hareketli Ortalama)
        self.keltner_middle = self.I(talib.SMA, self.data.Close, self.keltner_window)
        # Üst Keltner Kanalı: Orta Bant + (ATR Çarpanı * ATR)
        self.upper_kc = self.I(lambda: self.keltner_middle + self.keltner_atr_mult * self.atr)
        # Alt Keltner Kanalı: Orta Bant - (ATR Çarpanı * ATR)
        self.lower_kc = self.I(lambda: self.keltner_middle - self.keltner_atr_mult * self.atr)
        
        # Bollinger Band Sıkışmasını Tespit Et
        # Sıkışma: Üst Bollinger Bandı, Üst Keltner Kanalının altında VE Alt Bollinger Bandı, Alt Keltner Kanalının üzerinde olduğunda
        self.squeeze = self.I(lambda: (self.upper_bb < self.upper_kc) & 
                                     (self.lower_bb > self.lower_kc))
        
        # ADX'i Hesapla
        self.adx = self.I(talib.ADX, self.data.High, self.data.Low, 
                          self.data.Close, self.adx_period)
        
        # Sıkışma bitişini takip etmek için bir bayrak (flag)
        self.squeeze_released = False
        
    def next(self):
        # Her bir veri noktası (mum) için çalışır: Alım/Satım mantığı
        
        # Yeterli veri oluşana kadar bekle
        if len(self.data) < max(self.bb_window, self.keltner_window, self.adx_period):
            return
        
        # Bir önceki mumda sıkışma durumunda olup olmadığımızı ve şimdi sıkışmanın bitip bitmediğini kontrol et
        squeeze_now = self.squeeze[-1] # Mevcut mumdaki sıkışma durumu
        # Bir önceki mumdaki sıkışma durumu (eğer yeterli veri varsa, yoksa varsayılan olarak sıkışmada gibi kabul et)
        squeeze_prev = self.squeeze[-2] if len(self.data) > (max(self.bb_window, self.keltner_window) + 1) else True
        
        # Sıkışma bitiyor (önceki True, şimdiki False ise)
        if squeeze_prev and not squeeze_now:
            self.squeeze_released = True # Sıkışmanın bittiğini işaretle
        
        # Alım Satım Mantığı - Eğer bir sıkışma bitişi yaşandıysa VE ADX trend gücünü teyit ediyorsa
        if self.squeeze_released and self.adx[-1] > self.adx_threshold:
            
            # Kırılma yönünü belirle
            # Fiyat üst Bollinger Bandının üzerine çıktıysa VE açık pozisyon yoksa
            
            if self.data.Close[-1] > self.upper_bb[-1] and not self.position:
                # Yukarı yönlü kırılma için Alış (Long) pozisyonu
                self.buy(size=self.trade_size_percentage,
                        sl=self.data.Close[-1] * (1 - self.stop_loss),  # Zarar Durdur: Giriş fiyatının %SL altı
                        tp=self.data.Close[-1] * (1 + self.take_profit)) # Kâr Al: Giriş fiyatının %TP üstü
                self.squeeze_released = False  # Bayrağı sıfırla (bir sonraki sıkışma bitişini beklemek için)
                
            # Fiyat alt Bollinger Bandının altına indiyse VE açık pozisyon yoksa
            elif self.data.Close[-1] < self.lower_bb[-1] and not self.position:
                # Aşağı yönlü kırılma için Satış (Short) pozisyonu
                self.sell(size=self.trade_size_percentage,
                        sl=self.data.Close[-1] * (1 + self.stop_loss), # Zarar Durdur: Giriş fiyatının %SL üstü
                        tp=self.data.Close[-1] * (1 - self.take_profit))# Kâr Al: Giriş fiyatının %TP altı
                self.squeeze_released = False  # Bayrağı sıfırla

data.columns = ['Open', 'High', 'Low', 'Close', 'Volume']

# Geriye dönük test nesnesini oluştur ve yapılandır
bt = Backtest(data, BBSqueezeADX, cash=500000, commission=0.002) # Komisyon oranı %0.2


print("🌟  GERİYE DÖNÜK TEST BAŞLIYOR - Varsayılan Parametreler 🌟")
stats_default = bt.run() 
print("\n📊  VARSAYILAN PARAMETRE SONUÇLARI:")
print(stats_default) 

# Şimdi optimizasyonu gerçekleştir
print("\n🔍OPTİMİZASYON BAŞLIYOR - Bu biraz zaman alabilir... 🔍")
optimization_results = bt.optimize(
    # Denenecek parametre aralıkları
    bb_window=range(10, 15, 5),                      # BB Pencere: 10
    bb_std=[round(i, 1) for i in np.arange(1.5, 2.1, 0.5)], # BB Std: 1.5, 2.0
    keltner_window=range(10, 20, 5),                 # Keltner Pencere: 10, 15
    keltner_atr_mult=[round(i, 1) for i in np.arange(1.0, 2, 0.5)], # Keltner ATR Çarpanı: 1.0, 1.5
    adx_period=range(10, 20, 2),                     # ADX Periyot: 10, 12, 14, 16, 18
    adx_threshold=range(20, 30, 5),                  # ADX Eşik: 20, 25
    take_profit=[i / 100 for i in range(3, 4, 2)],   # Kâr Al: %3 (sadece bir değer)
    stop_loss=[i / 100 for i in range(2, 4, 1)],     # Zarar Durdur: %2, %3
    maximize='Equity Final [$]',  # Optimize edilecek hedef metrik: Son Bakiye
    # Geçerli parametreleri sağlayan kısıtlama (örn: pencere boyutu 0'dan büyük olmalı)
    constraint=lambda param: param.bb_window > 0 and param.bb_std > 0 and param.keltner_window > 0
)

# Optimizasyon sonuçlarını yazdır
print("\n🏆 MOON DEV OPTİMİZASYON TAMAMLANDI - Sonuçlar:")
print(optimization_results) # En iyi sonucu ve test edilen diğer bazı sonuçları gösterir

# En iyi optimize edilmiş değerleri yazdır
print("\n✨ MOON DEV EN İYİ PARAMETRELER:")
print(f"BB Pencere: {optimization_results._strategy.bb_window}")
print(f"BB Standart Sapma: {optimization_results._strategy.bb_std}")
print(f"Keltner Pencere: {optimization_results._strategy.keltner_window}")
print(f"Keltner ATR Çarpanı: {optimization_results._strategy.keltner_atr_mult}")
print(f"ADX Periyot: {optimization_results._strategy.adx_period}")
print(f"ADX Eşik Değeri: {optimization_results._strategy.adx_threshold}")
print(f"Kâr Al: {optimization_results._strategy.take_profit * 100:.1f}%")
print(f"Zarar Durdur: {optimization_results._strategy.stop_loss * 100:.1f}%")

breakpoint = 1
