#!/usr/bin/env python3
"""
Test Runner Script
Framework: SELENIUM
"""

import pytest
import sys
import os
from datetime import datetime

def main():
    """Ana test runner fonksiyonu"""
    
    # Rapor dizinini oluştur
    report_dir = "reports"
    os.makedirs(report_dir, exist_ok=True)
    
    # Ekran görüntüsü dizinini oluştur
    screenshot_dir = "screenshots"
    os.makedirs(screenshot_dir, exist_ok=True)
    
    # Test argümanları
    args = [
        "--verbose",
        f"--html={report_dir}/report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
        "--self-contained-html",
        "--tb=short"
    ]
    
    # Komut satırı argümanlarını ekle
    args.extend(sys.argv[1:])
    
    # Testleri çalıştır
    exit_code = pytest.main(args)
    
    print(f"\nTest çalıştırma tamamlandı. Çıkış kodu: {exit_code}")
    return exit_code

if __name__ == "__main__":
    sys.exit(main())
