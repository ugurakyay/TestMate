#!/usr/bin/env python3
"""
Demo kullanıcısı oluşturma scripti
"""

import sys
import os

# Database modülünü import et
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from database.models import db_manager

def create_demo_user():
    """Demo kullanıcısı oluştur"""
    try:
        # Demo kullanıcısı oluştur
        result = db_manager.create_user(
            email="demo@testmate.com",
            password="demo123",
            full_name="Demo Kullanıcı",
            company="TestMate Studio"
        )
        
        if result["success"]:
            print("✅ Demo kullanıcısı başarıyla oluşturuldu!")
            print(f"📧 Email: demo@testmate.com")
            print(f"🔑 Şifre: demo123")
            print(f"👤 Ad: Demo Kullanıcı")
            print(f"🏢 Şirket: TestMate Studio")
            print(f"🎫 Lisans: {result['license']['license_type']}")
            print(f"🔑 Lisans Key: {result['license']['license_key']}")
        else:
            print(f"❌ Demo kullanıcısı oluşturulamadı: {result['error']}")
            
    except Exception as e:
        print(f"❌ Hata: {e}")

if __name__ == "__main__":
    create_demo_user() 