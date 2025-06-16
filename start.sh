#!/bin/bash

echo "🚀 TestMate Studio Başlatılıyor..."

# Python sanal ortamını kontrol et
if [ ! -d "venv" ]; then
    echo "📦 Python sanal ortamı oluşturuluyor..."
    python3 -m venv venv
fi

# Sanal ortamı aktifleştir
echo "🔧 Sanal ortam aktifleştiriliyor..."
source venv/bin/activate

# Bağımlılıkları yükle
echo "📚 Bağımlılıklar yükleniyor..."
pip install -r requirements.txt

# Uygulamayı başlat
echo "🌟 TestMate Studio başlatılıyor..."
echo "🌐 http://localhost:8000 adresinden erişebilirsiniz"
echo "⏹️  Durdurmak için Ctrl+C tuşlayın"
echo ""

python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload 