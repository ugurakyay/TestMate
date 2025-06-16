# Otomasyon Projesi

Bu proje, AI Test Tool tarafından otomatik olarak oluşturulmuştur.

## Proje Bilgileri

- **Framework**: SELENIUM
- **Test Sayısı**: 1
- **Oluşturulma Tarihi**: 2025-06-16 12:24:54

## Kurulum

1. Python 3.8+ yüklü olduğundan emin olun
2. Gerekli paketleri yükleyin:
   ```bash
   pip install -r requirements.txt
   ```

## Test Çalıştırma

### Tüm testleri çalıştır:
```bash
pytest
```

### Belirli bir testi çalıştır:
```bash
pytest test_tc001.py
```

### HTML rapor ile çalıştır:
```bash
pytest --html=reports/report.html
```

## Proje Yapısı

```
generated_tests/test_project_2/
├── requirements.txt      # Gerekli paketler
├── config.py            # Konfigürasyon dosyası
├── test_*.py           # Test dosyaları
├── README.md           # Bu dosya
└── reports/            # Test raporları
```

## Konfigürasyon

`config.py` dosyasından aşağıdaki ayarları yapabilirsiniz:

- Tarayıcı türü (Selenium için)
- Bekleme süreleri
- Test verileri
- API endpoint'leri

## Notlar

- Test çalıştırmadan önce `config.py` dosyasındaki ayarları kontrol edin
- Mobil testler için Appium Server'ın çalışır durumda olduğundan emin olun
- API testleri için doğru endpoint URL'lerini ayarlayın

## Destek

Sorunlar için AI Test Tool'u kullanabilirsiniz.
