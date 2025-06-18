#!/usr/bin/env python3
"""
Database Reset Script
Bu script database'i sıfırlar ve yeniden oluşturur.
"""

import os
import sqlite3
from database.models import DatabaseManager

def reset_database():
    """Database'i sıfırla ve yeniden oluştur"""
    print("🔄 Database sıfırlanıyor...")
    
    # Database dosyasını sil
    db_file = "testmate_studio.db"
    if os.path.exists(db_file):
        try:
            os.remove(db_file)
            print(f"✅ {db_file} silindi")
        except Exception as e:
            print(f"❌ Database dosyası silinemedi: {e}")
            return False
    
    # Database manager oluştur
    db_manager = DatabaseManager()
    
    try:
        # Database'i başlat
        db_manager.init_database()
        print("✅ Database tabloları oluşturuldu")
        
        # Admin kullanıcısı oluştur
        db_manager.create_admin_user()
        print("✅ Admin kullanıcısı oluşturuldu")
        
        # Demo kullanıcısı oluştur
        demo_result = db_manager.create_user(
            email="demo@testmate.com",
            password="demo123",
            full_name="Demo User",
            company="TestMate Studio"
        )
        
        if demo_result["success"]:
            print("✅ Demo kullanıcısı oluşturuldu")
        else:
            print(f"⚠️ Demo kullanıcısı oluşturulamadı: {demo_result['error']}")
        
        print("\n🎉 Database başarıyla sıfırlandı!")
        print("\n📋 Giriş Bilgileri:")
        print("Admin: admin@testmatestudio.com / admin123")
        print("Demo: demo@testmate.com / demo123")
        
        return True
        
    except Exception as e:
        print(f"❌ Database sıfırlama hatası: {e}")
        return False

if __name__ == "__main__":
    # Onay al
    print("⚠️ Bu işlem mevcut database'i silecek ve yeniden oluşturacak!")
    print("Tüm kullanıcı verileri kaybolacak!")
    
    confirm = input("\nDevam etmek istiyor musunuz? (y/N): ").strip().lower()
    
    if confirm in ['y', 'yes', 'evet']:
        reset_database()
    else:
        print("❌ İşlem iptal edildi.") 