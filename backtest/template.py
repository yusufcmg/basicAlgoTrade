
import pandas as pd  
import numpy as np   
import talib         
from backtesting import Backtest, Strategy  
from backtesting.lib import crossover      

# DİKKAT: Bu dosya yolunu kendi sisteminizdeki doğru yolla değiştirmeniz gerekecektir.
data_path = 'C:\\masaustu\\basicAlgoTrade\\backtest\\data'
# CSV dosyasını oku
data = pd.read_csv(data_path, parse_dates=['datetime'], index_col='datetime')

# bollinger Bandı Kırılma Stratejisi 
class BollingerBandBreakoutShort(Strategy):
    
    window = 21     # bollinger bandı için periyot 
    num_std = 2.7   # bollinger bandı için standart sapma 
    take_profit = 0.05  # kar al hedefi (%5)
    stop_loss = 0.03    # zarar durdurma hedefi (%3)

    def init(self):
        # TA-Lib ile bollinger bantlarını hesapla
        self.upper_band, self.middle_band, self.lower_band = self.I(
            talib.BBANDS,          # TA-Lib fonksiyonu
            self.data.Close,       # kapanış fiyatları kullan
            self.window,           # periyot
            self.num_std,          # üst için standart sapma
            self.num_std           # alt için standart sapma
        )

    def next(self):
        # her bir mum için çalışır
        # yeterli veri yoksa (periyot genişliği kadar) işlem yapma
        if len(self.data) < self.window:
            return
        
        if self.data.Close[-1] < self.lower_band[-1] and not self.position:
            #piyasa satışı yap 
            self.sell(
                sl=self.data.Close[-1] * (1 + self.stop_loss),  # Zarar durdurma fiyatı (giriş fiyatının %SL yukarısı)
                tp=self.data.Close[-1] * (1 - self.take_profit) # Kâr al fiyatı (giriş fiyatının %TP aşağısı)
            )
            # fiyatın alt bandın altına kırılmasını kontrol et
        # self.data.Close[-1] en son (şimdiki) kapanış fiyatını verir
        # self.lower_band[-1] en son (şimdiki) alt bandın değerini verir
        # not self.position açık pozisyon kontrolü


# backtesting.py kütüphanesi 'Open', 'High', 'Low', 'Close', 'Volume' gibi standart sütun adlarını bekler
data.columns = ['Open', 'High', 'Low', 'Close', 'Volume', 'Unnamed: 6']


data.drop(columns=['Unnamed: 6'], inplace=True) 


bt = Backtest(
    data,                         # kullanılacak OHLCV verisi
    BollingerBandBreakoutShort,   # kullanılacak strateji sınıfı
    cash=100000,                  # başlangıç sermayesi
    commission=0.002              # işlem başına komisyon oranı (%0.2)
)


stats_default = bt.run() 
print("Default Parameters Results:")
print(stats_default) 


# farklı parametre kombinasyonlarını deneyerek en iyi sonucu bulmaya çalışır
optimization_results = bt.optimize(
    window=range(10, 20, 5),  # window için denenecek değerler: 10, 15 (20 dahil değil)
    num_std=[round(i, 1) for i in np.arange(1.5, 3.5, 0.1)], # num_std için 1.5'ten 3.4'e 0.1 artışlarla değerler
    take_profit=[i / 100 for i in range(1, 7, 1)],  # kar al için %1'den %6'ya kadar değerler 
    stop_loss=[i / 100 for i in range(1, 7, 1)],    # zarar durdurma için %1'den %6'ya kadar değerler 
    maximize='Equity Final [$]',  # optimize edilecek hedef metrik: Son Bakiye
    constraint=lambda param: param.window > 0 and param.num_std > 0  # parametrelerin geçerli olmasını sağlayan kısıtlama
)

# Optimizasyon sonuçlarını yazdır
print(optimization_results) # En iyi sonucu ve test edilen diğer bazı sonuçları gösterir

# En iyi optimize edilmiş değerleri yazdır
print("Best Parameters:")
print("Window:", optimization_results._strategy.window)
print("Number of Standard Deviations:", optimization_results._strategy.num_std)
print("Take Profit:", optimization_results._strategy.take_profit)
print("Stop Loss:", optimization_results._strategy.stop_loss)