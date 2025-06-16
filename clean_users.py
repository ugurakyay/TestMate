#!/usr/bin/env python3
"""
Boş email'li kullanıcıları temizleme scripti
"""

import json
import os

def clean_users():
    """Boş email'li kullanıcıları temizle"""
    users_file = "users.json"
    
    if not os.path.exists(users_file):
        print("users.json dosyası bulunamadı!")
        return
    
    with open(users_file, 'r') as f:
        users = json.load(f)
    
    print(f"Toplam kullanıcı sayısı: {len(users)}")
    
    # Boş email'li kullanıcıları bul ve sil
    users_to_remove = []
    for user_id, user in users.items():
        if not user.get('email') or user['email'].strip() == '':
            users_to_remove.append(user_id)
            print(f"Silinecek kullanıcı: {user_id} - Email: '{user.get('email', 'BOŞ')}'")
    
    # Kullanıcıları sil
    for user_id in users_to_remove:
        del users[user_id]
    
    # Dosyayı güncelle
    with open(users_file, 'w') as f:
        json.dump(users, f, indent=2)
    
    print(f"{len(users_to_remove)} kullanıcı silindi.")
    print(f"Kalan kullanıcı sayısı: {len(users)}")
    
    # Kalan kullanıcıları listele
    print("\nKalan kullanıcılar:")
    for user_id, user in users.items():
        print(f"- {user['email']} ({user['license_type']})")

if __name__ == "__main__":
    clean_users() 