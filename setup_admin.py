#!/usr/bin/env python3
"""
TestMate Studio - Admin Kurulum Scripti
Bu script admin kullanıcısı oluşturur ve lisans yönetimi sistemini kurar.
"""

import json
import os
import hashlib
import secrets
from datetime import datetime, timedelta

def create_admin_config():
    """Admin konfigürasyon dosyası oluşturur"""
    print("TestMate Studio - Admin Kurulum")
    print("=" * 40)
    
    email = input("Admin e-posta adresi: ").strip()
    password = input("Admin şifresi: ").strip()
    
    if not email or not password:
        print("❌ E-posta ve şifre gereklidir!")
        return False
    
    # Şifreyi hash'le
    salt = secrets.token_hex(16)
    hashed_password = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000).hex()
    
    config = {
        "admin_email": email,
        "admin_password_hash": hashed_password,
        "admin_password_salt": salt,
        "created_at": datetime.now().isoformat(),
        "last_login": None
    }
    
    # Konfigürasyon dosyasını kaydet
    with open('admin_config.json', 'w') as f:
        json.dump(config, f, indent=2)
    
    print("✅ Admin konfigürasyonu oluşturuldu!")
    return True

def create_license_manager():
    """Lisans yönetimi sistemini kurar"""
    print("\nTestMate Studio - Lisans Yönetimi Kurulum")
    print("=" * 40)
    
    # Lisans veritabanı oluştur
    licenses_db = {
        "licenses": {},
        "users": {},
        "statistics": {
            "total_users": 0,
            "active_licenses": 0,
            "trial_users": 0,
            "total_revenue": 0
        },
        "created_at": datetime.now().isoformat()
    }
    
    # Veritabanını kaydet
    with open('licenses.json', 'w') as f:
        json.dump(licenses_db, f, indent=2)
    
    print("✅ Lisans veritabanı oluşturuldu!")
    return True

def create_sample_data():
    """Örnek veriler oluşturur"""
    print("\nTestMate Studio - Örnek Veriler")
    print("=" * 40)
    
    # Örnek kullanıcılar
    sample_users = {
        "demo@testmatestudio.com": {
            "email": "demo@testmatestudio.com",
            "license_type": "professional",
            "status": "active",
            "created_date": datetime.now().isoformat(),
            "expiry_date": (datetime.now() + timedelta(days=30)).isoformat(),
            "usage": {
                "test_generation": 15,
                "locator_analysis": 8,
                "excel_processing": 3
            }
        },
        "trial@testmatestudio.com": {
            "email": "trial@testmatestudio.com",
            "license_type": "trial",
            "status": "active",
            "created_date": datetime.now().isoformat(),
            "expiry_date": (datetime.now() + timedelta(days=7)).isoformat(),
            "usage": {
                "test_generation": 3,
                "locator_analysis": 2,
                "excel_processing": 1
            }
        }
    }
    
    # Lisans veritabanını güncelle
    try:
        with open('licenses.json', 'r') as f:
            licenses_db = json.load(f)
        
        licenses_db["users"] = sample_users
        licenses_db["statistics"]["total_users"] = len(sample_users)
        licenses_db["statistics"]["active_licenses"] = len(sample_users)
        licenses_db["statistics"]["trial_users"] = 1
        
        with open('licenses.json', 'w') as f:
            json.dump(licenses_db, f, indent=2)
        
        print("✅ Örnek kullanıcılar oluşturuldu!")
        print("   - demo@testmatestudio.com (Professional)")
        print("   - trial@testmatestudio.com (Trial)")
        
    except FileNotFoundError:
        print("❌ Lisans veritabanı bulunamadı. Önce lisans yönetimi kurulumu yapın.")
        return False
    
    return True

def main():
    """Ana kurulum fonksiyonu"""
    print("TestMate Studio - Hızlı Kurulum")
    print("=" * 40)
    print("Bu script aşağıdaki işlemleri gerçekleştirir:")
    print("1. Admin kullanıcısı oluşturma")
    print("2. Lisans yönetimi sistemi kurulumu")
    print("3. Örnek veriler oluşturma")
    print()
    
    choice = input("Kuruluma devam etmek istiyor musunuz? (y/n): ").lower()
    if choice != 'y':
        print("❌ Kurulum iptal edildi.")
        return
    
    # Admin konfigürasyonu
    if not create_admin_config():
        return
    
    # Lisans yönetimi
    if not create_license_manager():
        return
    
    # Örnek veriler
    create_sample_data()
    
    print("\n" + "=" * 40)
    print("🎉 TestMate Studio kurulumu tamamlandı!")
    print("🌐 Uygulamayı başlatmak için: python -m uvicorn app.main:app --reload")
    print("🔐 Admin paneline erişim: http://localhost:8000/admin")
    print("📧 Varsayılan admin: admin@testmatestudio.com / admin123")
    print("=" * 40)

if __name__ == "__main__":
    main() 