#!/bin/bash

echo "========================================"
echo "AI Test Tool - Otomatik Kurulum"
echo "========================================"
echo

echo "Python kontrol ediliyor..."
python3 --version
if [ $? -ne 0 ]; then
    echo "HATA: Python bulunamadı! Lütfen Python 3.8+ yükleyin."
    exit 1
fi

echo
echo "Virtual environment oluşturuluyor..."
python3 -m venv venv
if [ $? -ne 0 ]; then
    echo "HATA: Virtual environment oluşturulamadı!"
    exit 1
fi

echo
echo "Virtual environment aktifleştiriliyor..."
source venv/bin/activate

echo
echo "Dependencies yükleniyor..."
pip install --upgrade pip
pip install -r requirements.txt

echo
echo "Kurulum tamamlandı!"
echo
echo "Testleri çalıştırmak için:"
echo "1. source venv/bin/activate"
echo "2. python run_tests.py"
echo
