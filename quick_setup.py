#!/usr/bin/env python3
"""
TestMate Studio - Hızlı Admin Kurulum
Bu script varsayılan admin kullanıcısını oluşturur.
"""

import json
import hashlib
import secrets
from datetime import datetime

def create_default_admin():
    """Varsayılan admin kullanıcısını oluşturur"""
    print("TestMate Studio - Hızlı Admin Kurulum")
    print("=" * 40)
    
    # Varsayılan admin bilgileri
    email = "admin@testmatestudio.com"
    password = "admin123"
    
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
    
    print("✅ Varsayılan admin kullanıcısı oluşturuldu!")
    print(f"📧 E-posta: {email}")
    print(f"🔑 Şifre: {password}")
    print("🌐 Admin paneli: http://localhost:8000/admin")
    print("⚠️  Güvenlik için şifreyi değiştirmeyi unutmayın!")
    
    return True

if __name__ == "__main__":
    create_default_admin() 