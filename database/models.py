#!/usr/bin/env python3
"""
Database Models for TestMate Studio
SQLite tabanlı kullanıcı yönetimi ve lisans sistemi
"""

import sqlite3
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import json
import os

class DatabaseManager:
    """SQLite veritabanı yöneticisi"""
    
    def __init__(self, db_path: str = "testmate_studio.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Veritabanını başlat ve tabloları oluştur"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Users tablosu
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    full_name TEXT,
                    company TEXT,
                    role TEXT DEFAULT 'user',
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Sessions tablosu
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    session_token TEXT UNIQUE NOT NULL,
                    expires_at TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            # Licenses tablosu
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS licenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    license_key TEXT UNIQUE NOT NULL,
                    license_type TEXT NOT NULL,
                    features TEXT NOT NULL,
                    usage_limits TEXT NOT NULL,
                    current_usage TEXT NOT NULL,
                    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expiry_date TIMESTAMP NOT NULL,
                    status TEXT DEFAULT 'active',
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            # User Projects tablosu - Her kullanıcının kendi projeleri
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    project_name TEXT NOT NULL,
                    project_type TEXT NOT NULL,
                    description TEXT,
                    test_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'active',
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            # User Test Files tablosu - Her kullanıcının test dosyaları
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_test_files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    project_id INTEGER NOT NULL,
                    file_name TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    test_type TEXT NOT NULL,
                    framework TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    file_size INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'active',
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    FOREIGN KEY (project_id) REFERENCES user_projects (id)
                )
            ''')
            
            # User Workspace tablosu - Her kullanıcının çalışma alanı
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_workspace (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    workspace_path TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            # Admin users tablosu
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS admin_users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT DEFAULT 'admin',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Contact requests tablosu
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS contact_requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT NOT NULL,
                    name TEXT,
                    company TEXT,
                    plan_type TEXT,
                    message TEXT,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Test execution logs tablosu
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS test_execution_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    test_file_id INTEGER NOT NULL,
                    execution_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT NOT NULL,
                    duration REAL,
                    error_message TEXT,
                    screenshot_path TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    FOREIGN KEY (test_file_id) REFERENCES user_test_files (id)
                )
            ''')
            
            conn.commit()
            
            # Admin kullanıcısını oluştur
            self.create_admin_user()
    
    def create_admin_user(self):
        """Admin kullanıcısı oluştur"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Admin kullanıcısı var mı kontrol et
            cursor.execute("SELECT id FROM admin_users WHERE email = ?", ("admin@testmatestudio.com",))
            if cursor.fetchone():
                conn.close()
                return {"success": False, "error": "Admin kullanıcısı zaten mevcut"}
            
            # Admin kullanıcısı oluştur
            admin_password = "admin123"
            password_hash = self.hash_password(admin_password)
            
            cursor.execute('''
                INSERT INTO admin_users (email, password_hash, role)
                VALUES (?, ?, ?)
            ''', ("admin@testmatestudio.com", password_hash, "admin"))
            
            admin_id = cursor.lastrowid
            
            # Admin için normal kullanıcı hesabı da oluştur
            cursor.execute('''
                INSERT INTO users (email, password_hash, full_name, role)
                VALUES (?, ?, ?, ?)
            ''', ("admin@testmatestudio.com", password_hash, "Admin User", "admin"))
            
            user_id = cursor.lastrowid
            
            # Admin lisansı oluştur
            admin_license = {
                "license_key": "ADMIN-UNLIMITED-2025",
                "license_type": "enterprise",
                "features": json.dumps({
                    "test_generation": -1,
                    "locator_analysis": -1,
                    "excel_processing": True,
                    "test_execution": -1,
                    "website_analyzer": -1,
                    "api_health_check": -1,
                    "ai_enhancement": True,
                    "admin_panel": True
                }),
                "usage_limits": json.dumps({
                    "test_generation": -1,
                    "locator_analysis": -1,
                    "excel_processing": -1,
                    "test_execution": -1,
                    "website_analyzer": -1,
                    "api_health_check": -1
                }),
                "current_usage": json.dumps({
                    "test_generation": 0,
                    "locator_analysis": 0,
                    "excel_processing": 0,
                    "test_execution": 0,
                    "website_analyzer": 0,
                    "api_health_check": 0
                })
            }
            
            cursor.execute('''
                INSERT INTO licenses (user_id, license_key, license_type, features, usage_limits, current_usage, expiry_date)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                admin_license["license_key"],
                admin_license["license_type"],
                admin_license["features"],
                admin_license["usage_limits"],
                admin_license["current_usage"],
                (datetime.now() + timedelta(days=365)).isoformat()
            ))
            
            # Admin workspace oluştur
            admin_workspace = f"workspaces/admin_{user_id}"
            os.makedirs(admin_workspace, exist_ok=True)
            
            cursor.execute('''
                INSERT INTO user_workspace (user_id, workspace_path)
                VALUES (?, ?)
            ''', (user_id, admin_workspace))
            
            conn.commit()
            conn.close()
            
            return {
                "success": True,
                "admin_id": admin_id,
                "user_id": user_id,
                "email": "admin@testmatestudio.com",
                "password": admin_password
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def hash_password(self, password: str) -> str:
        """Şifreyi hash'le"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def verify_password(self, password: str, password_hash: str) -> bool:
        """Şifreyi doğrula"""
        return self.hash_password(password) == password_hash
    
    def create_user(self, email: str, password: str, full_name: str = None, company: str = None) -> Dict[str, Any]:
        """Yeni kullanıcı ve trial lisans oluştur (tek transaction)"""
        try:
            with sqlite3.connect(self.db_path, timeout=30.0) as conn:
                cursor = conn.cursor()
                # Email kontrolü
                cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
                if cursor.fetchone():
                    return {"success": False, "error": "Bu email adresi zaten kayıtlı"}

                # Kullanıcı oluştur
                password_hash = self.hash_password(password)
                cursor.execute('''
                    INSERT INTO users (email, password_hash, full_name, company, role)
                    VALUES (?, ?, ?, ?, ?)
                ''', (email, password_hash, full_name, company, "user"))
                user_id = cursor.lastrowid

                # Trial lisans oluştur (Aynı bağlantı ile!)
                license_key = f"TRIAL-{secrets.token_hex(4).upper()}"
                features = {
                    "test_generation": 10,
                    "locator_analysis": 5,
                    "excel_processing": True,
                    "test_execution": 5,
                    "website_analyzer": 3,
                    "api_health_check": 3,
                    "ai_enhancement": False
                }
                usage_limits = {
                    "test_generation": 10,
                    "locator_analysis": 5,
                    "excel_processing": 3,
                    "test_execution": 5,
                    "website_analyzer": 3,
                    "api_health_check": 3
                }
                current_usage = {
                    "test_generation": 0,
                    "locator_analysis": 0,
                    "excel_processing": 0,
                    "test_execution": 0,
                    "website_analyzer": 0,
                    "api_health_check": 0
                }
                expiry = (datetime.now() + timedelta(days=7)).isoformat()
                cursor.execute('''
                    INSERT INTO licenses (user_id, license_key, license_type, features, usage_limits, current_usage, expiry_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    user_id, license_key, "trial",
                    json.dumps(features), json.dumps(usage_limits),
                    json.dumps(current_usage), expiry
                ))

                # Workspace oluştur
                user_workspace = f"workspaces/user_{user_id}"
                os.makedirs(user_workspace, exist_ok=True)
                cursor.execute('''
                    INSERT INTO user_workspace (user_id, workspace_path)
                    VALUES (?, ?)
                ''', (user_id, user_workspace))

                conn.commit()
                return {
                    "success": True,
                    "user_id": user_id,
                    "license": {
                        "license_key": license_key,
                        "license_type": "trial",
                        "features": features,
                        "expiry_date": expiry
                    }
                }
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e):
                return {"success": False, "error": "Veritabanı meşgul, lütfen tekrar deneyin"}
            else:
                return {"success": False, "error": f"Veritabanı hatası: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": f"Kullanıcı oluşturma hatası: {str(e)}"}
    
    def authenticate_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Kullanıcı kimlik doğrulama ve session token oluşturma"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT u.id, u.email, u.full_name, u.role, u.is_active, l.license_key, l.license_type, l.features, l.current_usage, l.expiry_date
                    FROM users u
                    LEFT JOIN licenses l ON u.id = l.user_id
                    WHERE u.email = ? AND u.password_hash = ? AND u.is_active = 1
                ''', (email, self.hash_password(password)))
                
                result = cursor.fetchone()
                if result:
                    user_id = result[0]
                    # Session token oluştur
                    session_token = secrets.token_hex(32)
                    expires_at = (datetime.now() + timedelta(days=7)).isoformat()
                    cursor.execute('''
                        INSERT INTO sessions (user_id, session_token, expires_at)
                        VALUES (?, ?, ?)
                    ''', (user_id, session_token, expires_at))
                    conn.commit()
                    return {
                        "user_id": result[0],
                        "email": result[1],
                        "full_name": result[2],
                        "role": result[3],
                        "is_active": bool(result[4]),
                        "license_key": result[5],
                        "license_type": result[6],
                        "features": json.loads(result[7]) if result[7] else {},
                        "current_usage": json.loads(result[8]) if result[8] else {},
                        "expiry_date": result[9],
                        "session_token": session_token
                    }
                return None
        except Exception as e:
            print(f"Authentication error: {e}")
            return None
    
    def get_user_by_session(self, session_token: str) -> Optional[Dict[str, Any]]:
        """Session token ile kullanıcı bilgilerini al"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT u.id, u.email, u.full_name, u.role, l.license_key, l.license_type, l.features, l.current_usage, l.expiry_date
                    FROM users u
                    LEFT JOIN licenses l ON u.id = l.user_id
                    LEFT JOIN sessions s ON u.id = s.user_id
                    WHERE s.session_token = ? AND s.expires_at > ? AND u.is_active = 1
                ''', (session_token, datetime.now().isoformat()))
                
                result = cursor.fetchone()
                if result:
                    return {
                        "user_id": result[0],
                        "email": result[1],
                        "full_name": result[2],
                        "role": result[3],
                        "license_key": result[4],
                        "license_type": result[5],
                        "features": json.loads(result[6]) if result[6] else {},
                        "current_usage": json.loads(result[7]) if result[7] else {},
                        "expiry_date": result[8]
                    }
                return None
        except Exception as e:
            print(f"Session validation error: {e}")
            return None
    
    def get_user_license(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Kullanıcının lisans bilgilerini al"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT license_key, license_type, features, usage_limits, current_usage, expiry_date, status
                    FROM licenses
                    WHERE user_id = ? AND status = 'active'
                    ORDER BY created_date DESC
                    LIMIT 1
                ''', (user_id,))
                
                license_data = cursor.fetchone()
                if not license_data:
                    return None
                
                license_key, license_type, features, usage_limits, current_usage, expiry_date, status = license_data
                
                return {
                    "license_key": license_key,
                    "license_type": license_type,
                    "features": json.loads(features),
                    "usage_limits": json.loads(usage_limits),
                    "current_usage": json.loads(current_usage),
                    "expiry_date": expiry_date,
                    "status": status
                }
                
        except Exception as e:
            print(f"License retrieval error: {e}")
            return None
    
    def check_feature_access(self, user_id: int, feature: str) -> Dict[str, Any]:
        """Özellik erişim kontrolü"""
        license_data = self.get_user_license(user_id)
        if not license_data:
            return {"access": False, "error": "Aktif lisans bulunamadı"}
        
        features = license_data["features"]
        usage_limits = license_data["usage_limits"]
        current_usage = license_data["current_usage"]
        
        # Lisans süresi kontrolü
        if license_data["expiry_date"]:
            expiry_date = datetime.fromisoformat(license_data["expiry_date"])
            if datetime.now() > expiry_date:
                return {"access": False, "error": "Lisans süresi dolmuş"}
        
        # Özellik kontrolü
        if feature not in features:
            return {"access": False, "error": f"'{feature}' özelliği lisansınızda mevcut değil"}
        
        # Kullanım limiti kontrolü
        if license_data["license_type"] == "trial":
            limit = usage_limits.get(feature, 0)
            current = current_usage.get(feature, 0)
            if current >= limit:
                return {"access": False, "error": f"'{feature}' kullanım limitiniz dolmuş"}
        
        return {"access": True, "license": license_data}
    
    def increment_usage(self, user_id: int, feature: str):
        """Kullanım sayısını artır"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Mevcut kullanımı al
                cursor.execute('''
                    SELECT current_usage FROM licenses
                    WHERE user_id = ? AND status = 'active'
                    ORDER BY created_date DESC LIMIT 1
                ''', (user_id,))
                
                result = cursor.fetchone()
                if not result:
                    return
                
                current_usage = json.loads(result[0])
                
                # Trial kullanıcılar için kalan hakkı azalt
                cursor.execute('''
                    SELECT license_type FROM licenses
                    WHERE user_id = ? AND status = 'active'
                    ORDER BY created_date DESC LIMIT 1
                ''', (user_id,))
                
                license_type = cursor.fetchone()[0]
                
                if license_type == "trial":
                    if current_usage.get(feature, 0) > 0:
                        current_usage[feature] -= 1
                else:
                    current_usage[feature] = current_usage.get(feature, 0) + 1
                
                # Kullanımı güncelle
                cursor.execute('''
                    UPDATE licenses
                    SET current_usage = ?
                    WHERE user_id = ? AND status = 'active'
                ''', (json.dumps(current_usage), user_id))
                
                # Usage log ekle
                cursor.execute('''
                    INSERT INTO usage_logs (user_id, feature, action, details)
                    VALUES (?, ?, ?, ?)
                ''', (user_id, feature, "increment", json.dumps({"new_count": current_usage[feature]})))
                
                conn.commit()
                
        except Exception as e:
            print(f"Usage increment error: {e}")
    
    def logout_user(self, session_token: str):
        """Kullanıcı çıkışı"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM sessions WHERE session_token = ?', (session_token,))
                conn.commit()
        except Exception as e:
            print(f"Logout error: {e}")
    
    def cleanup_expired_sessions(self):
        """Süresi dolmuş session'ları temizle"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM sessions WHERE expires_at < ?', (datetime.now().isoformat(),))
                conn.commit()
        except Exception as e:
            print(f"Session cleanup error: {e}")
    
    def get_all_users(self) -> List[Dict[str, Any]]:
        """Tüm kullanıcıları listele (admin için)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT u.id, u.email, u.full_name, u.company, u.role, u.is_active, u.created_at,
                           l.license_type, l.status, l.expiry_date
                    FROM users u
                    LEFT JOIN licenses l ON u.id = l.user_id AND l.status = 'active'
                    ORDER BY u.created_at DESC
                ''')
                
                users = []
                for row in cursor.fetchall():
                    users.append({
                        "id": row[0],
                        "email": row[1],
                        "full_name": row[2],
                        "company": row[3],
                        "role": row[4],
                        "is_active": bool(row[5]),
                        "created_at": row[6],
                        "license_type": row[7],
                        "license_status": row[8],
                        "license_expires": row[9]
                    })
                
                return users
                
        except Exception as e:
            print(f"Get users error: {e}")
            return []
    
    def get_usage_statistics(self) -> Dict[str, Any]:
        """Kullanım istatistikleri (admin için)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Toplam kullanıcı sayısı
                cursor.execute("SELECT COUNT(*) FROM users")
                total_users = cursor.fetchone()[0]
                
                # Aktif kullanıcı sayısı
                cursor.execute("SELECT COUNT(*) FROM users WHERE is_active = 1")
                active_users = cursor.fetchone()[0]
                
                # Lisans türlerine göre dağılım
                cursor.execute('''
                    SELECT license_type, COUNT(*) as count
                    FROM licenses
                    WHERE status = 'active'
                    GROUP BY license_type
                ''')
                license_distribution = dict(cursor.fetchall())
                
                # Son 30 günlük kullanım
                thirty_days_ago = (datetime.now() - timedelta(days=30)).isoformat()
                cursor.execute('''
                    SELECT feature, COUNT(*) as count
                    FROM usage_logs
                    WHERE created_at > ?
                    GROUP BY feature
                ''', (thirty_days_ago,))
                recent_usage = dict(cursor.fetchall())
                
                return {
                    "total_users": total_users,
                    "active_users": active_users,
                    "license_distribution": license_distribution,
                    "recent_usage": recent_usage
                }
                
        except Exception as e:
            print(f"Statistics error: {e}")
            return {}

# Global database instance
db_manager = DatabaseManager() 