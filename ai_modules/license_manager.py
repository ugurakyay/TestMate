"""
TestMate Studio için lisans yönetimi
"""

import json
import os
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

class LicenseManager:
    def __init__(self):
        self.licenses_file = "licenses.json"
        self.admin_config_file = "admin_config.json"
        self.initialize_database()
    
    def initialize_database(self):
        """Lisans veritabanını başlat"""
        if not os.path.exists(self.licenses_file):
            initial_data = {
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
            self._save_data(initial_data)
    
    def _load_data(self) -> Dict:
        """Veritabanından veri yükle"""
        try:
            with open(self.licenses_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {
                "licenses": {},
                "users": {},
                "statistics": {
                    "total_users": 0,
                    "active_licenses": 0,
                    "trial_users": 0,
                    "total_revenue": 0
                }
            }
    
    def _save_data(self, data: Dict):
        """Veritabanına veri kaydet"""
        with open(self.licenses_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _load_admin_config(self) -> Dict:
        """Admin konfigürasyonunu yükle"""
        try:
            with open(self.admin_config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    def verify_admin_credentials(self, email: str, password: str) -> bool:
        """Admin kimlik bilgilerini doğrula"""
        config = self._load_admin_config()
        
        if not config:
            return False
        
        # Basit şifre kontrolü
        stored_email = config.get("admin_email")
        stored_password = config.get("admin_password")
        
        if not stored_email or not stored_password:
            return False
        
        return email == stored_email and password == stored_password
    
    def create_trial_license(self, email: str) -> Dict[str, Any]:
        """Trial lisans oluştur"""
        data = self._load_data()
        
        # E-posta kontrolü
        if email in data["users"]:
            return {"success": False, "error": "Bu e-posta adresi zaten kayıtlı"}
        
        # Trial lisans oluştur
        trial_license = {
            "email": email,
            "license_type": "trial",
            "status": "active",
            "created_date": datetime.now().isoformat(),
            "expiry_date": (datetime.now() + timedelta(days=7)).isoformat(),
            "usage": {
                "test_generation": 0,
                "locator_analysis": 0,
                "excel_processing": 0
            }
        }
        
        data["users"][email] = trial_license
        data["statistics"]["total_users"] += 1
        data["statistics"]["active_licenses"] += 1
        data["statistics"]["trial_users"] += 1
        
        self._save_data(data)
        
        return {
            "success": True,
            "license": trial_license,
            "message": "Trial lisans başarıyla oluşturuldu"
        }
    
    def generate_trial_license(self, email: str) -> Dict[str, Any]:
        """Trial lisans oluştur (alias for create_trial_license)"""
        return self.create_trial_license(email)
    
    def verify_license(self, license_key: str) -> Dict[str, Any]:
        """Lisans anahtarını doğrula"""
        data = self._load_data()
        
        # Basit lisans anahtarı doğrulama (gerçek uygulamada daha güvenli olmalı)
        for email, user_data in data["users"].items():
            if self._generate_license_key(email) == license_key:
                if self._is_license_valid(user_data):
                    return {
                        "success": True,
                        "license": user_data,
                        "valid": True
                    }
                else:
                    return {
                        "success": True,
                        "license": user_data,
                        "valid": False,
                        "error": "Lisans süresi dolmuş"
                    }
        
        return {
            "success": False,
            "error": "Geçersiz lisans anahtarı"
        }
    
    def _generate_license_key(self, email: str) -> str:
        """E-posta adresinden lisans anahtarı oluştur"""
        # Basit hash tabanlı anahtar (gerçek uygulamada daha güvenli olmalı)
        key_data = f"TestMateStudio-{email}-{datetime.now().strftime('%Y%m')}"
        return hashlib.md5(key_data.encode()).hexdigest()[:16].upper()
    
    def _is_license_valid(self, license_data: Dict) -> bool:
        """Lisansın geçerli olup olmadığını kontrol et"""
        expiry_date = datetime.fromisoformat(license_data["expiry_date"])
        return datetime.now() < expiry_date
    
    def get_license_status(self) -> Dict[str, Any]:
        """Mevcut lisans durumunu getir"""
        # Bu fonksiyon gerçek uygulamada session/cookie tabanlı olmalı
        return {
            "has_license": False,
            "license_type": None,
            "status": None,
            "email": None,
            "start_date": None,
            "end_date": None
        }
    
    def get_license_info(self) -> Dict[str, Any]:
        """Lisans bilgilerini getir"""
        # Bu fonksiyon gerçek uygulamada session/cookie tabanlı olmalı
        return {
            "has_license": False,
            "license_type": None,
            "status": None,
            "email": None,
            "start_date": None,
            "end_date": None,
            "features": [],
            "usage": {}
        }
    
    def get_pricing_plans(self) -> Dict[str, Any]:
        """Fiyatlandırma planlarını getir"""
        return {
            "plans": [
                {
                    "name": "Basic",
                    "price": 29,
                    "features": [
                        "Temel test generation",
                        "Basit locator analysis",
                        "5 proje limiti",
                        "Email desteği"
                    ]
                },
                {
                    "name": "Professional",
                    "price": 99,
                    "features": [
                        "Gelişmiş AI özellikleri",
                        "Priority support",
                        "25 proje limiti",
                        "API access"
                    ]
                },
                {
                    "name": "Enterprise",
                    "price": 299,
                    "features": [
                        "Özel entegrasyonlar",
                        "Dedicated support",
                        "Sınırsız proje",
                        "White-label seçeneği"
                    ]
                }
            ]
        }
    
    def create_user_license(self, email: str, license_type: str, duration: int) -> Dict[str, Any]:
        """Kullanıcı lisansı oluştur"""
        data = self._load_data()
        
        # E-posta kontrolü
        if email in data["users"]:
            return {"success": False, "error": "Bu e-posta adresi zaten kayıtlı"}
        
        # Lisans oluştur
        new_license = {
            "email": email,
            "license_type": license_type,
            "status": "active",
            "created_date": datetime.now().isoformat(),
            "expiry_date": (datetime.now() + timedelta(days=duration)).isoformat(),
            "usage": {
                "test_generation": 0,
                "locator_analysis": 0,
                "excel_processing": 0
            }
        }
        
        data["users"][email] = new_license
        data["statistics"]["total_users"] += 1
        data["statistics"]["active_licenses"] += 1
        
        if license_type == "trial":
            data["statistics"]["trial_users"] += 1
        
        self._save_data(data)
        
        return {
            "success": True,
            "license": new_license,
            "license_key": self._generate_license_key(email)
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """İstatistikleri getir"""
        data = self._load_data()
        return data["statistics"]
    
    def get_users(self) -> List[Dict[str, Any]]:
        """Kullanıcı listesini getir"""
        data = self._load_data()
        users = []
        
        for email, user_data in data["users"].items():
            users.append({
                "email": email,
                "license_type": user_data["license_type"],
                "status": user_data["status"],
                "created_date": user_data["created_date"],
                "expiry_date": user_data["expiry_date"],
                "duration": (datetime.fromisoformat(user_data["expiry_date"]) - datetime.fromisoformat(user_data["created_date"])).days,
                "license_key": self._generate_license_key(email)
            })
        
        return users
    
    def check_license_access(self, email: str, feature: str) -> bool:
        """Kullanıcının belirli bir özelliğe erişim hakkı olup olmadığını kontrol et"""
        data = self._load_data()
        
        if email not in data["users"]:
            return False
        
        user_data = data["users"][email]
        
        # Lisans geçerliliğini kontrol et
        if not self._is_license_valid(user_data):
            return False
        
        # Özellik bazlı kontroller
        license_type = user_data.get("license_type", "trial")
        
        if license_type == "trial":
            # Trial kullanıcıları tüm özelliklere erişebilir (limitli)
            return True
        elif license_type in ["basic", "professional", "enterprise"]:
            # Tüm özelliklere erişim
            return True
        
        return False

    def check_feature_access(self, feature: str) -> Dict[str, Any]:
        """Özellik erişim kontrolü - genel erişim için"""
        # Şimdilik tüm özelliklere erişim ver (geliştirme aşamasında)
        return {
            "access": True,
            "feature": feature,
            "message": "Feature access granted"
        }
    
    def increment_usage(self, email: str, feature: str):
        """Kullanım sayısını artır"""
        data = self._load_data()
        
        if email in data["users"]:
            if "usage" not in data["users"][email]:
                data["users"][email]["usage"] = {}
            
            if feature not in data["users"][email]["usage"]:
                data["users"][email]["usage"][feature] = 0
            
            data["users"][email]["usage"][feature] += 1
            self._save_data(data)

    def get_user_info(self, email: str) -> Optional[Dict[str, Any]]:
        """Kullanıcı bilgilerini getir"""
        data = self._load_data()
        
        if email in data["users"]:
            user_data = data["users"][email].copy()
            # Add license key to user info
            user_data["license_key"] = self._generate_license_key(email)
            return user_data
        
        return None
    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Email ile kullanıcı bilgilerini getir (alias for get_user_info)"""
        return self.get_user_info(email)

    def update_user_license(self, email: str, license_key: str, license_type: str, duration_days: int) -> bool:
        """Kullanıcı lisansını güncelle"""
        data = self._load_data()
        
        if email not in data["users"]:
            return False
        
        # Update user license
        data["users"][email]["license_type"] = license_type
        data["users"][email]["status"] = "active"
        data["users"][email]["expiry_date"] = (datetime.now() + timedelta(days=duration_days)).isoformat()
        data["users"][email]["updated_date"] = datetime.now().isoformat()
        
        self._save_data(data)
        return True

    def generate_license_key(self) -> str:
        """Yeni lisans anahtarı oluştur"""
        # Generate a random license key
        return secrets.token_hex(16).upper()

    def send_license_email(self, email: str, user_info: Dict[str, Any]) -> bool:
        """Lisans bilgilerini e-posta ile gönder"""
        try:
            # Generate license text
            license_text = self._generate_license_email_text(email, user_info)
            
            # In a real application, you would send this via SMTP
            # For now, we'll just print it to console
            print(f"=== LICENSE EMAIL TO {email} ===")
            print(license_text)
            print("=" * 50)
            
            return True
        except Exception as e:
            print(f"Error sending license email: {e}")
            return False

    def _generate_license_email_text(self, email: str, user_info: Dict[str, Any]) -> str:
        """Lisans e-posta metnini oluştur"""
        license_key = self._generate_license_key(email)
        expiry_date = datetime.fromisoformat(user_info["expiry_date"]).strftime("%d.%m.%Y")
        
        return f"""
TestMate Studio - Lisans Bilgileri

Sayın Kullanıcı,

TestMate Studio lisansınız başarıyla oluşturulmuştur.

Lisans Detayları:
- E-posta: {email}
- Lisans Türü: {user_info.get('license_type', 'Unknown').upper()}
- Lisans Anahtarı: {license_key}
- Geçerlilik Tarihi: {expiry_date}

Lisans Anahtarınızı güvenli bir yerde saklayın. Bu anahtar yazılımı kullanmak için gereklidir.

TestMate Studio'yu kullanmaya başlamak için:
1. Yazılımı başlatın
2. Lisans anahtarınızı girin
3. Test otomasyonu özelliklerini kullanmaya başlayın

Herhangi bir sorunuz olursa bizimle iletişime geçebilirsiniz.

Saygılarımızla,
TestMate Studio Ekibi
        """.strip()

    def extend_user_license(self, email: str, days: int) -> Dict[str, Any]:
        """Kullanıcı lisansını uzat"""
        data = self._load_data()
        
        if email not in data["users"]:
            return {"success": False, "error": "Kullanıcı bulunamadı"}
        
        # Extend license
        current_expiry = datetime.fromisoformat(data["users"][email]["expiry_date"])
        new_expiry = current_expiry + timedelta(days=days)
        data["users"][email]["expiry_date"] = new_expiry.isoformat()
        data["users"][email]["status"] = "active"
        
        self._save_data(data)
        
        return {
            "success": True,
            "message": f"Lisans {days} gün uzatıldı",
            "new_expiry_date": new_expiry.isoformat()
        }

    def generate_license_report(self) -> Dict[str, Any]:
        """Lisans raporu oluştur"""
        data = self._load_data()
        
        report = {
            "total_users": len(data["users"]),
            "active_licenses": 0,
            "expired_licenses": 0,
            "trial_users": 0,
            "paid_users": 0,
            "license_types": {},
            "recent_activity": []
        }
        
        for email, user_data in data["users"].items():
            if self._is_license_valid(user_data):
                report["active_licenses"] += 1
            else:
                report["expired_licenses"] += 1
            
            license_type = user_data.get("license_type", "unknown")
            if license_type == "trial":
                report["trial_users"] += 1
            else:
                report["paid_users"] += 1
            
            if license_type not in report["license_types"]:
                report["license_types"][license_type] = 0
            report["license_types"][license_type] += 1

    def increment_usage_dev(self, feature: str):
        """Development mode için kullanım sayısını artır (email gerektirmez)"""
        # Development modunda basit bir sayaç tut
        data = self._load_data()
        
        if "dev_usage" not in data:
            data["dev_usage"] = {}
        
        if feature not in data["dev_usage"]:
            data["dev_usage"][feature] = 0
        
        data["dev_usage"][feature] += 1
        self._save_data(data) 