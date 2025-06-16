"""
TestMate Studio - İletişim Formu Yöneticisi
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, List

class ContactManager:
    def __init__(self):
        self.contacts_file = "data/contact_requests.json"
        self._ensure_data_directory()
        self._load_contacts()
    
    def _ensure_data_directory(self):
        """Data dizinini oluştur"""
        os.makedirs("data", exist_ok=True)
    
    def _load_contacts(self):
        """Mevcut iletişim taleplerini yükle"""
        if os.path.exists(self.contacts_file):
            try:
                with open(self.contacts_file, 'r', encoding='utf-8') as f:
                    self.contacts = json.load(f)
            except:
                self.contacts = {"requests": []}
        else:
            self.contacts = {"requests": []}
    
    def _save_contacts(self):
        """İletişim taleplerini kaydet"""
        with open(self.contacts_file, 'w', encoding='utf-8') as f:
            json.dump(self.contacts, f, ensure_ascii=False, indent=2)
    
    def submit_plan_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Plan talebi kaydet"""
        try:
            # Gerekli alanları kontrol et
            required_fields = ['plan_name', 'name', 'email', 'phone']
            for field in required_fields:
                if not request_data.get(field):
                    return {"success": False, "error": f"Eksik alan: {field}"}
            
            # Yeni talep oluştur
            contact_request = {
                "id": len(self.contacts["requests"]) + 1,
                "plan_name": request_data.get("plan_name"),
                "name": request_data.get("name"),
                "email": request_data.get("email"),
                "phone": request_data.get("phone"),
                "company": request_data.get("company", ""),
                "notes": request_data.get("notes", ""),
                "status": "new",
                "created_date": datetime.now().isoformat(),
                "processed": False
            }
            
            # Talebi kaydet
            self.contacts["requests"].append(contact_request)
            self._save_contacts()
            
            return {
                "success": True,
                "message": "Talebiniz başarıyla alındı! En kısa sürede size dönüş yapılacaktır.",
                "request_id": contact_request["id"]
            }
            
        except Exception as e:
            return {"success": False, "error": f"Kayıt hatası: {str(e)}"}
    
    def get_all_requests(self) -> List[Dict[str, Any]]:
        """Tüm iletişim taleplerini getir"""
        self._load_contacts()
        return self.contacts.get("requests", [])
    
    def get_request_by_id(self, request_id: int) -> Dict[str, Any]:
        """ID'ye göre talep getir"""
        for request in self.contacts.get("requests", []):
            if request.get("id") == request_id:
                return request
        return None
    
    def update_request_status(self, request_id: int, status: str, processed: bool = True) -> bool:
        """Talep durumunu güncelle"""
        for request in self.contacts.get("requests", []):
            if request.get("id") == request_id:
                request["status"] = status
                request["processed"] = processed
                request["processed_date"] = datetime.now().isoformat()
                self._save_contacts()
                return True
        return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """İstatistikleri getir"""
        requests = self.contacts.get("requests", [])
        
        total_requests = len(requests)
        new_requests = len([r for r in requests if r.get("status") == "new"])
        processed_requests = len([r for r in requests if r.get("processed") == True])
        
        # Plan bazında istatistikler
        plan_stats = {}
        for request in requests:
            plan = request.get("plan_name", "Bilinmeyen")
            if plan not in plan_stats:
                plan_stats[plan] = 0
            plan_stats[plan] += 1
        
        return {
            "total_requests": total_requests,
            "new_requests": new_requests,
            "processed_requests": processed_requests,
            "plan_statistics": plan_stats
        } 