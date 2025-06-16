# TestMate Studio - Otomasyon Projesi Oluşturucu

TestMate Studio, yapay zeka destekli test otomasyonu platformudur. Kodlama bilgisi gerektirmeden, doğal dil açıklamalarından otomatik test senaryoları oluşturabilir, locator'ları analiz edebilir ve Excel dosyalarından proje oluşturabilirsiniz.

## 🚀 Özellikler

- **AI Test Generation**: Yapay zeka ile otomatik test senaryoları oluşturma
- **Smart Locator Analysis**: Akıllı locator analizi ile element bulma
- **Excel Integration**: Excel dosyalarından otomatik proje oluşturma
- **Multi-Framework Support**: Selenium, Appium, Requests desteği
- **License Management**: Lisans yönetimi ve kullanıcı kontrolü
- **Admin Panel**: Kapsamlı admin paneli ile kullanıcı yönetimi

## 📋 Gereksinimler

- Python 3.11
- FastAPI
- OpenAI API Key (opsiyonel)
- Modern web tarayıcısı

## 🛠️ Kurulum

### 1. Projeyi İndirin
```bash
git clone <repository-url>
cd AI_test_tool
```

### 2. Python Sanal Ortamı Oluşturun
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# veya
venv\Scripts\activate     # Windows
```

### 3. Bağımlılıkları Yükleyin
```bash
pip install -r requirements.txt
```

### 4. OpenAI API Key (Opsiyonel)
```bash
export OPENAI_API_KEY="your-api-key-here"
```

### 5. Uygulamayı Başlatın
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Veya hızlı başlatma scripti kullanın:
```bash
./start.sh
```

## 🎯 Kullanım

### Ana Sayfa
- **http://localhost:8000** - Ana sayfa ve özellikler

### Test Oluşturma
- **http://localhost:8000/generate** - AI ile test senaryoları oluşturma
- Test türü seçin (Web, Mobil, API)
- Framework seçin (Selenium, Appium, Requests)
- Test senaryonuzu açıklayın
- AI otomatik test kodunu oluşturur

### Locator Analizi
- **http://localhost:8000/analyze** - HTML içeriğinden locator analizi
- HTML kodunu yapıştırın
- Element açıklamasını girin
- AI en uygun locator'ları önerir

### Excel İşleme
- **http://localhost:8000/excel** - Excel dosyalarından proje oluşturma
- Template indirin ve doldurun
- Excel dosyanızı yükleyin
- Otomatik proje oluşturun

### Test Çalıştırma
- **http://localhost:8000/execute** - Testleri çalıştırma
- Test kodunu yapıştırın
- Çalıştırın ve sonuçları görün

### Lisans Yönetimi
- **http://localhost:8000/license** - Lisans durumu ve satın alma
- Deneme başlatın
- Lisans doğrulayın
- Planları görüntüleyin

### Admin Panel
- **http://localhost:8000/admin** - Admin paneli
- Kullanıcı yönetimi
- Lisans oluşturma
- İstatistikler ve raporlar

## 🔧 API Endpoints

### Test Generation
- `POST /api/generate-test` - Test senaryosu oluşturma
- `POST /api/analyze-locators` - Locator analizi
- `POST /api/execute-tests` - Test çalıştırma

### Excel Processing
- `GET /api/download-template` - Excel template indirme
- `POST /api/upload-excel` - Excel dosyası yükleme
- `POST /api/generate-project` - Proje oluşturma

### License Management
- `GET /api/license/status` - Lisans durumu
- `POST /api/license/trial` - Deneme başlatma
- `POST /api/license/verify` - Lisans doğrulama
- `GET /api/license/pricing` - Fiyatlandırma

### Admin Endpoints
- `POST /api/admin/login` - Admin girişi
- `GET /api/admin/statistics` - İstatistikler
- `GET /api/admin/users` - Kullanıcı listesi
- `POST /api/admin/create-license` - Lisans oluşturma

## 📁 Proje Yapısı

```
AI_test_tool/
├── app/
│   ├── main.py              # FastAPI uygulaması
│   ├── templates/           # HTML şablonları
│   └── __init__.py
├── ai_modules/
│   ├── test_generator.py    # AI test oluşturucu
│   ├── locator_analyzer.py  # Locator analizi
│   ├── excel_processor.py   # Excel işleme
│   ├── code_generator.py    # Kod oluşturucu
│   └── license_manager.py   # Lisans yönetimi
├── tests/                   # Test dosyaları
├── generated_tests/         # Oluşturulan testler
├── requirements.txt         # Python bağımlılıkları
├── start.sh                # Başlatma scripti
└── README.md
```

## 🎨 Özelleştirme

### Tema Değişiklikleri
CSS stillerini `app/templates/` klasöründeki HTML dosyalarında düzenleyebilirsiniz.

### AI Modülleri
`ai_modules/` klasöründeki Python dosyalarını düzenleyerek AI davranışlarını özelleştirebilirsiniz.

### Lisans Planları
`ai_modules/license_manager.py` dosyasında lisans planlarını ve fiyatlandırmayı düzenleyebilirsiniz.

## 🔒 Güvenlik

- Admin paneli oturum tabanlı kimlik doğrulama kullanır
- Şifreler hash'li olarak saklanır
- API rate limiting uygulanır
- CORS koruması aktif

## 📊 Lisans Planları

### Basic Plan - $29/ay
- Temel test generation
- Basit locator analysis
- 5 proje limiti
- Email desteği

### Professional Plan - $99/ay
- Gelişmiş AI özellikleri
- Priority support
- 25 proje limiti
- API access

### Enterprise Plan - $299/ay
- Özel entegrasyonlar
- Dedicated support
- Sınırsız proje
- White-label seçeneği

## 🚀 Deployment

### Docker ile
```bash
docker build -t testmate-studio .
docker run -p 8000:8000 testmate-studio
```

### Production
```bash
pip install gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

## 🤝 Katkıda Bulunma

1. Fork yapın
2. Feature branch oluşturun (`git checkout -b feature/amazing-feature`)
3. Commit yapın (`git commit -m 'Add amazing feature'`)
4. Push yapın (`git push origin feature/amazing-feature`)
5. Pull Request oluşturun

## 📝 Lisans

Bu proje MIT lisansı altında lisanslanmıştır.

## 📞 Destek

- **Email**: support@testmatestudio.com
- **Dokümantasyon**: https://docs.testmatestudio.com
- **Issues**: GitHub Issues

## 🎉 Teşekkürler

**TestMate Studio** - Test otomasyonunu kolaylaştırın! 🚀 