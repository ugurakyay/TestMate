#!/usr/bin/env python3
"""
TestMate Studio - Database Setup Script
Veritabanını başlat ve admin kullanıcısı oluştur
"""

import sys
import os

# Database modülünü import et
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from database.models import db_manager

def setup_database():
    """Veritabanını kur ve admin kullanıcısı oluştur"""
    print("🔧 TestMate Studio - Veritabanı Kurulumu")
    print("=" * 50)
    
    try:
        # Admin kullanıcısı oluştur
        print("\n👤 Admin kullanıcısı oluşturuluyor...")
        admin_result = db_manager.create_admin_user()
        
        if admin_result["success"]:
            print("✅ Admin kullanıcısı başarıyla oluşturuldu!")
            print(f"📧 Email: {admin_result['email']}")
            print(f"🔑 Şifre: {admin_result['password']}")
            print(f"👤 User ID: {admin_result['user_id']}")
            print(f"🔧 Admin ID: {admin_result['admin_id']}")
        else:
            print(f"❌ Admin kullanıcısı oluşturulamadı: {admin_result['error']}")
        
        # Demo kullanıcısı oluştur
        print("\n👤 Demo kullanıcısı oluşturuluyor...")
        demo_result = db_manager.create_user(
            email="demo@testmate.com",
            password="demo123",
            full_name="Demo Kullanıcı",
            company="TestMate Studio"
        )
        
        if demo_result["success"]:
            print("✅ Demo kullanıcısı başarıyla oluşturuldu!")
            print(f"📧 Email: demo@testmate.com")
            print(f"🔑 Şifre: demo123")
            print(f"👤 User ID: {demo_result['user_id']}")
            print(f"🎫 Lisans: {demo_result['license']['license_type']}")
        else:
            print(f"❌ Demo kullanıcısı oluşturulamadı: {demo_result['error']}")
        
        print("\n🎉 Veritabanı kurulumu tamamlandı!")
        print("\n📋 Giriş Bilgileri:")
        print("Admin: admin@testmatestudio.com / admin123")
        print("Demo: demo@testmate.com / demo123")
        
        return True
        
    except Exception as e:
        print(f"❌ Veritabanı kurulumu başarısız: {e}")
        return False

if __name__ == "__main__":
    setup_database() 