"""
TestMate Studio - Email Gönderme Modülü
"""

import smtplib
import ssl
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Dict, Any
import os

class EmailSender:
    def __init__(self):
        self.config = self._load_config()
        self.smtp_server = self.config.get("smtp_server", "smtp.gmail.com")
        self.smtp_port = self.config.get("smtp_port", 587)
        self.sender_email = self.config.get("sender_email", "info@testmatestudio.com")
        self.admin_email = self.config.get("admin_email", "ugurakyay@gmail.com")
        self.sender_password = os.getenv("EMAIL_PASSWORD", self.config.get("sender_password", "your-app-password"))
        self.use_ssl = self.config.get("use_ssl", True)
        self.use_tls = self.config.get("use_tls", True)
    
    def _load_config(self) -> Dict[str, Any]:
        """Email konfigürasyonunu yükle"""
        try:
            with open('email_config.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print("Warning: email_config.json not found, using default settings")
            return {}
        except Exception as e:
            print(f"Warning: Error loading email config: {e}")
            return {}
    
    def send_plan_request_email(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Plan talebi için email gönder"""
        try:
            # Admin'e bildirim emaili
            admin_subject = f"Yeni Plan Talebi - {request_data['plan_name']}"
            admin_body = self._create_admin_email_body(request_data)
            self._send_email(self.admin_email, admin_subject, admin_body)
            
            # Müşteriye onay emaili
            customer_subject = "TestMate Studio - Talebiniz Alındı"
            customer_body = self._create_customer_email_body(request_data)
            self._send_email(request_data['email'], customer_subject, customer_body)
            
            return {
                "success": True,
                "message": "Email'ler başarıyla gönderildi"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Email gönderme hatası: {str(e)}"
            }
    
    def _create_admin_email_body(self, request_data: Dict[str, Any]) -> str:
        """Admin için email içeriği oluştur"""
        return f"""
        <html>
        <body>
            <h2>🚀 Yeni Plan Talebi</h2>
            <p><strong>Tarih:</strong> {datetime.now().strftime('%d.%m.%Y %H:%M')}</p>
            
            <h3>📋 Talep Detayları</h3>
            <table style="border-collapse: collapse; width: 100%;">
                <tr style="background-color: #f8f9fa;">
                    <td style="padding: 8px; border: 1px solid #ddd;"><strong>Plan:</strong></td>
                    <td style="padding: 8px; border: 1px solid #ddd;">{request_data['plan_name']}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd;"><strong>Ad Soyad:</strong></td>
                    <td style="padding: 8px; border: 1px solid #ddd;">{request_data['name']}</td>
                </tr>
                <tr style="background-color: #f8f9fa;">
                    <td style="padding: 8px; border: 1px solid #ddd;"><strong>E-posta:</strong></td>
                    <td style="padding: 8px; border: 1px solid #ddd;">{request_data['email']}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd;"><strong>Telefon:</strong></td>
                    <td style="padding: 8px; border: 1px solid #ddd;">{request_data['phone']}</td>
                </tr>
                <tr style="background-color: #f8f9fa;">
                    <td style="padding: 8px; border: 1px solid #ddd;"><strong>Şirket:</strong></td>
                    <td style="padding: 8px; border: 1px solid #ddd;">{request_data.get('company', 'Belirtilmemiş')}</td>
                </tr>
            </table>
            
            {f"<h3>💬 Ek Notlar</h3><p>{request_data.get('message', '')}</p>" if request_data.get('message') else ""}
            
            <hr>
            <p style="color: #666; font-size: 12px;">
                Bu email TestMate Studio sisteminden otomatik olarak gönderilmiştir.
            </p>
        </body>
        </html>
        """
    
    def _create_customer_email_body(self, request_data: Dict[str, Any]) -> str:
        """Müşteri için email içeriği oluştur"""
        return f"""
        <html>
        <body>
            <div style="max-width: 600px; margin: 0 auto; font-family: Arial, sans-serif;">
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                    <h1 style="margin: 0;">🎉 TestMate Studio</h1>
                    <p style="margin: 10px 0 0 0; opacity: 0.9;">Talebiniz Başarıyla Alındı!</p>
                </div>
                
                <div style="padding: 30px; background: #fff; border: 1px solid #e9ecef; border-top: none; border-radius: 0 0 10px 10px;">
                    <h2 style="color: #333; margin-top: 0;">Merhaba {request_data['name']},</h2>
                    
                    <p style="color: #666; line-height: 1.6;">
                        <strong>{request_data['plan_name']}</strong> planı için talebinizi aldık. 
                        Ekibimiz en kısa sürede size dönüş yapacaktır.
                    </p>
                    
                    <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                        <h3 style="margin-top: 0; color: #333;">📋 Talep Özeti</h3>
                        <p><strong>Plan:</strong> {request_data['plan_name']}</p>
                        <p><strong>Tarih:</strong> {datetime.now().strftime('%d.%m.%Y %H:%M')}</p>
                        <p><strong>Referans No:</strong> {datetime.now().strftime('%Y%m%d%H%M')}</p>
                    </div>
                    
                    <p style="color: #666; line-height: 1.6;">
                        <strong>Sonraki Adımlar:</strong>
                    </p>
                    <ul style="color: #666; line-height: 1.6;">
                        <li>Ekibimiz talebinizi değerlendirecek</li>
                        <li>Size özel fiyat teklifi hazırlanacak</li>
                        <li>24 saat içinde telefon veya email ile dönüş yapılacak</li>
                    </ul>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="mailto:info@testmatestudio.com" style="background: linear-gradient(45deg, #667eea, #764ba2); color: white; padding: 12px 30px; text-decoration: none; border-radius: 25px; display: inline-block;">
                            📧 Bize Ulaşın
                        </a>
                    </div>
                    
                    <hr style="border: none; border-top: 1px solid #e9ecef; margin: 30px 0;">
                    
                    <p style="color: #999; font-size: 14px; text-align: center;">
                        <strong>TestMate Studio</strong><br>
                        AI-Powered Test Automation Platform<br>
                        📧 info@testmatestudio.com<br>
                        🌐 www.testmatestudio.com
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _send_email(self, to_email: str, subject: str, body: str) -> bool:
        """Email gönder"""
        try:
            # Email mesajı oluştur
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = self.sender_email
            message["To"] = to_email
            
            # HTML içeriği ekle
            html_part = MIMEText(body, "html")
            message.attach(html_part)
            
            # SMTP bağlantısı
            if self.use_ssl:
                context = ssl.create_default_context()
                with smtplib.SMTP_SSL(self.smtp_server, 465, context=context) as server:
                    server.login(self.sender_email, self.sender_password)
                    server.sendmail(self.sender_email, to_email, message.as_string())
            else:
                with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                    if self.use_tls:
                        context = ssl.create_default_context()
                        server.starttls(context=context)
                    server.login(self.sender_email, self.sender_password)
                    server.sendmail(self.sender_email, to_email, message.as_string())
            
            return True
            
        except Exception as e:
            print(f"Email gönderme hatası: {str(e)}")
            return False
    
    def test_connection(self) -> Dict[str, Any]:
        """Email bağlantısını test et"""
        try:
            if self.use_ssl:
                context = ssl.create_default_context()
                with smtplib.SMTP_SSL(self.smtp_server, 465, context=context) as server:
                    server.login(self.sender_email, self.sender_password)
            else:
                with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                    if self.use_tls:
                        context = ssl.create_default_context()
                        server.starttls(context=context)
                    server.login(self.sender_email, self.sender_password)
            
            return {
                "success": True,
                "message": "Email bağlantısı başarılı"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Email bağlantı hatası: {str(e)}"
            } 