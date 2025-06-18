#!/usr/bin/env python3
"""
API Health Checker Module
JSON dosyasından endpoint'leri okuyup sağlık kontrolü yapar.
"""

import json
import asyncio
import aiohttp
import time
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse
import logging
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import os

# Logging ayarları
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class EndpointConfig:
    """Endpoint konfigürasyonu"""
    name: str
    url: str
    method: str = "GET"
    headers: Optional[Dict[str, str]] = None
    body: Optional[Dict[str, Any]] = None
    expected_status: int = 200
    timeout: int = 30
    description: Optional[str] = None

@dataclass
class HealthCheckResult:
    """Health check sonucu"""
    endpoint_name: str
    url: str
    method: str
    status_code: Optional[int]
    response_time: float
    is_healthy: bool
    error_message: Optional[str] = None
    response_size: Optional[int] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

class APIHealthChecker:
    """API Health Checker sınıfı"""
    
    def __init__(self, config_file: str = "api_endpoints.json"):
        self.config_file = config_file
        self.endpoints: List[EndpointConfig] = []
        self.results: List[HealthCheckResult] = []
        
    def load_endpoints_from_json(self, json_content: str) -> List[EndpointConfig]:
        """JSON içeriğinden endpoint'leri yükle"""
        try:
            data = json.loads(json_content)
            endpoints = []
            
            # JSON yapısını kontrol et
            if isinstance(data, dict):
                # Postman collection formatı kontrol et
                if "item" in data:
                    # Postman collection formatı
                    endpoints = self._parse_postman_collection(data)
                elif "endpoints" in data:
                    # {"endpoints": [...]} formatı
                    for item in data["endpoints"]:
                        endpoints.append(self._parse_endpoint(item))
                else:
                    # Tek endpoint objesi
                    endpoints.append(self._parse_endpoint(data))
            elif isinstance(data, list):
                # Birden fazla endpoint
                for item in data:
                    endpoints.append(self._parse_endpoint(item))
            else:
                raise ValueError("Geçersiz JSON formatı. Array veya object bekleniyor.")
                
            if not endpoints:
                raise ValueError("Hiç endpoint bulunamadı. JSON formatını kontrol edin.")
                
            self.endpoints = endpoints
            logger.info(f"{len(endpoints)} endpoint yüklendi")
            return endpoints
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse hatası: {e}")
            raise ValueError(f"Geçersiz JSON formatı: {str(e)}")
        except Exception as e:
            logger.error(f"Endpoint yükleme hatası: {e}")
            raise
    
    def _parse_postman_collection(self, collection_data: Dict[str, Any]) -> List[EndpointConfig]:
        """Postman collection'ından endpoint'leri parse et"""
        endpoints = []
        
        def extract_endpoints_from_items(items):
            for item in items:
                if "item" in item:
                    # Folder içindeki item'lar
                    extract_endpoints_from_items(item["item"])
                elif "request" in item:
                    # Endpoint
                    request = item["request"]
                    name = item.get("name", "Unnamed Endpoint")
                    
                    # URL'yi oluştur
                    url_obj = request.get("url", {})
                    if isinstance(url_obj, str):
                        url = url_obj
                    elif isinstance(url_obj, dict):
                        # Postman URL objesi
                        protocol = url_obj.get("protocol", "https")
                        host = url_obj.get("host", [])
                        path = url_obj.get("path", [])
                        
                        if isinstance(host, list):
                            host = ".".join(host)
                        
                        if isinstance(path, list):
                            path = "/".join(path)
                        
                        url = f"{protocol}://{host}/{path}"
                    else:
                        continue
                    
                    # Method
                    method = request.get("method", "GET").upper()
                    
                    # Headers
                    headers = {}
                    for header in request.get("header", []):
                        if "key" in header and "value" in header:
                            headers[header["key"]] = header["value"]
                    
                    # Body
                    body = None
                    body_obj = request.get("body", {})
                    if body_obj and "mode" in body_obj:
                        if body_obj["mode"] == "urlencoded":
                            body = {}
                            for param in body_obj.get("urlencoded", []):
                                if "key" in param and "value" in param:
                                    body[param["key"]] = param["value"]
                        elif body_obj["mode"] == "raw":
                            try:
                                body = json.loads(body_obj.get("raw", "{}"))
                            except:
                                body = body_obj.get("raw", "")
                    
                    # Endpoint oluştur
                    endpoint = EndpointConfig(
                        name=name,
                        url=url,
                        method=method,
                        headers=headers,
                        body=body,
                        expected_status=200,
                        timeout=30,
                        description=f"Postman: {name}"
                    )
                    endpoints.append(endpoint)
        
        # Collection'daki item'ları işle
        extract_endpoints_from_items(collection_data.get("item", []))
        
        return endpoints
    
    def _parse_endpoint(self, data: Dict[str, Any]) -> EndpointConfig:
        """Tek endpoint'i parse et"""
        if not isinstance(data, dict):
            raise ValueError(f"Endpoint verisi dict olmalı, {type(data)} verildi")
        
        # Gerekli alanları kontrol et
        if "name" not in data:
            raise ValueError("Endpoint'te 'name' alanı eksik")
        if "url" not in data:
            raise ValueError("Endpoint'te 'url' alanı eksik")
        
        # URL formatını kontrol et
        url = data["url"]
        if not url.startswith(('http://', 'https://')):
            raise ValueError(f"Geçersiz URL formatı: {url}. http:// veya https:// ile başlamalı")
        
        return EndpointConfig(
            name=str(data["name"]),
            url=str(data["url"]),
            method=str(data.get("method", "GET")).upper(),
            headers=data.get("headers", {}),
            body=data.get("body"),
            expected_status=int(data.get("expected_status", 200)),
            timeout=int(data.get("timeout", 30)),
            description=data.get("description")
        )
    
    async def check_single_endpoint(self, endpoint: EndpointConfig) -> HealthCheckResult:
        """Tek endpoint'i kontrol et"""
        start_time = time.time()
        
        try:
            async with aiohttp.ClientSession() as session:
                # Request parametrelerini hazırla
                request_kwargs = {
                    "timeout": aiohttp.ClientTimeout(total=endpoint.timeout),
                    "headers": endpoint.headers or {}
                }
                
                # Body varsa ekle
                if endpoint.body and endpoint.method in ["POST", "PUT", "PATCH"]:
                    request_kwargs["json"] = endpoint.body
                
                # Request'i gönder
                async with session.request(
                    endpoint.method, 
                    endpoint.url, 
                    **request_kwargs
                ) as response:
                    response_time = time.time() - start_time
                    
                    # Response body'yi oku
                    response_body = await response.read()
                    response_size = len(response_body)
                    
                    # Sonucu oluştur
                    is_healthy = response.status == endpoint.expected_status
                    
                    return HealthCheckResult(
                        endpoint_name=endpoint.name,
                        url=endpoint.url,
                        method=endpoint.method,
                        status_code=response.status,
                        response_time=response_time,
                        is_healthy=is_healthy,
                        response_size=response_size
                    )
                    
        except asyncio.TimeoutError:
            response_time = time.time() - start_time
            return HealthCheckResult(
                endpoint_name=endpoint.name,
                url=endpoint.url,
                method=endpoint.method,
                status_code=None,
                response_time=response_time,
                is_healthy=False,
                error_message="Timeout - Endpoint yanıt vermedi"
            )
            
        except aiohttp.ClientError as e:
            response_time = time.time() - start_time
            return HealthCheckResult(
                endpoint_name=endpoint.name,
                url=endpoint.url,
                method=endpoint.method,
                status_code=None,
                response_time=response_time,
                is_healthy=False,
                error_message=f"Connection error: {str(e)}"
            )
            
        except Exception as e:
            response_time = time.time() - start_time
            return HealthCheckResult(
                endpoint_name=endpoint.name,
                url=endpoint.url,
                method=endpoint.method,
                status_code=None,
                response_time=response_time,
                is_healthy=False,
                error_message=f"Unexpected error: {str(e)}"
            )
    
    async def check_all_endpoints(self) -> List[HealthCheckResult]:
        """Tüm endpoint'leri kontrol et"""
        logger.info(f"{len(self.endpoints)} endpoint kontrol ediliyor...")
        
        # Tüm endpoint'leri paralel olarak kontrol et
        tasks = [self.check_single_endpoint(endpoint) for endpoint in self.endpoints]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Exception'ları handle et
        self.results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                # Exception durumunda hata sonucu oluştur
                endpoint = self.endpoints[i]
                error_result = HealthCheckResult(
                    endpoint_name=endpoint.name,
                    url=endpoint.url,
                    method=endpoint.method,
                    status_code=None,
                    response_time=0.0,
                    is_healthy=False,
                    error_message=f"Check failed: {str(result)}"
                )
                self.results.append(error_result)
            else:
                self.results.append(result)
        
        logger.info(f"Health check tamamlandı. {len([r for r in self.results if r.is_healthy])}/{len(self.results)} endpoint sağlıklı")
        return self.results
    
    def generate_report(self) -> Dict[str, Any]:
        """Health check raporu oluştur"""
        if not self.results:
            return {"error": "Henüz health check yapılmadı"}
        
        total_endpoints = len(self.results)
        healthy_endpoints = len([r for r in self.results if r.is_healthy])
        failed_endpoints = total_endpoints - healthy_endpoints
        
        # Ortalama response time
        response_times = [r.response_time for r in self.results if r.response_time > 0]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        # En hızlı ve en yavaş endpoint'ler
        fastest_endpoint = min(self.results, key=lambda x: x.response_time) if self.results else None
        slowest_endpoint = max(self.results, key=lambda x: x.response_time) if self.results else None
        
        # Status code dağılımı
        status_codes = {}
        for result in self.results:
            if result.status_code:
                status_codes[result.status_code] = status_codes.get(result.status_code, 0) + 1
        
        return {
            "summary": {
                "total_endpoints": total_endpoints,
                "healthy_endpoints": healthy_endpoints,
                "failed_endpoints": failed_endpoints,
                "success_rate": (healthy_endpoints / total_endpoints * 100) if total_endpoints > 0 else 0,
                "average_response_time": round(avg_response_time, 3),
                "check_timestamp": datetime.now().isoformat()
            },
            "performance": {
                "fastest_endpoint": {
                    "name": fastest_endpoint.endpoint_name if fastest_endpoint else None,
                    "response_time": fastest_endpoint.response_time if fastest_endpoint else None
                },
                "slowest_endpoint": {
                    "name": slowest_endpoint.endpoint_name if slowest_endpoint else None,
                    "response_time": slowest_endpoint.response_time if slowest_endpoint else None
                }
            },
            "status_codes": status_codes,
            "detailed_results": [
                {
                    "name": r.endpoint_name,
                    "url": r.url,
                    "method": r.method,
                    "status_code": r.status_code,
                    "response_time": round(r.response_time, 3),
                    "is_healthy": r.is_healthy,
                    "error_message": r.error_message,
                    "response_size": r.response_size,
                    "timestamp": r.timestamp.isoformat()
                }
                for r in self.results
            ]
        }
    
    def save_results_to_json(self, filename: str = None) -> str:
        """Sonuçları JSON dosyasına kaydet"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"api_health_check_{timestamp}.json"
        
        report = self.generate_report()
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Health check raporu kaydedildi: {filename}")
        return filename
    
    def save_results_to_pdf(self, filename: str = None) -> str:
        """Sonuçları PDF dosyasına kaydet"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"api_health_check_{timestamp}.pdf"
        
        report = self.generate_report()
        
        # PDF oluştur
        doc = SimpleDocTemplate(filename, pagesize=A4)
        story = []
        
        # Stil tanımlamaları - basit yaklaşım
        styles = getSampleStyleSheet()
        
        # Başlık stili
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        )
        
        # Alt başlık stili
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            spaceBefore=20,
            textColor=colors.darkblue
        )
        
        # Normal metin stili
        normal_style = styles['Normal']
        
        # Başlık
        title = Paragraph("API Health Check Report", title_style)
        story.append(title)
        story.append(Spacer(1, 20))
        
        # Özet bilgiler
        summary = report['summary']
        summary_data = [
            ["Total Endpoints", str(summary['total_endpoints'])],
            ["Healthy Endpoints", str(summary['healthy_endpoints'])],
            ["Failed Endpoints", str(summary['failed_endpoints'])],
            ["Success Rate", f"%{summary['success_rate']:.1f}"],
            ["Average Response Time", f"{summary['average_response_time']} seconds"],
            ["Check Date", summary['check_timestamp'][:19].replace('T', ' ')]
        ]
        
        summary_table = Table(summary_data, colWidths=[2*inch, 3*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        story.append(Paragraph("Summary Information", heading_style))
        story.append(summary_table)
        story.append(Spacer(1, 20))
        
        # Performans bilgileri
        if report['performance']['fastest_endpoint']['name']:
            performance_data = [
                ["Fastest Endpoint", report['performance']['fastest_endpoint']['name']],
                ["Response Time", f"{report['performance']['fastest_endpoint']['response_time']:.3f} seconds"],
                ["Slowest Endpoint", report['performance']['slowest_endpoint']['name']],
                ["Response Time", f"{report['performance']['slowest_endpoint']['response_time']:.3f} seconds"]
            ]
            
            perf_table = Table(performance_data, colWidths=[2*inch, 3*inch])
            perf_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkgreen),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightgreen),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            
            story.append(Paragraph("Performance Information", heading_style))
            story.append(perf_table)
            story.append(Spacer(1, 20))
        
        # Detaylı sonuçlar
        story.append(Paragraph("Detailed Results", heading_style))
        
        # Tablo başlıkları
        detailed_results = report['detailed_results']
        if detailed_results:
            table_data = [["Endpoint", "URL", "Method", "Status", "Time (s)", "Status"]]
            
            # Endpoint adlarının maksimum uzunluğunu bul
            max_name_length = max(len(result['name']) for result in detailed_results) if detailed_results else 20
            max_name_length = min(max_name_length, 25)  # Maksimum 25 karakter
            
            for result in detailed_results:
                status_text = "Healthy" if result['is_healthy'] else "Failed"
                
                # Endpoint adını kısalt
                endpoint_name = result['name']
                if len(endpoint_name) > max_name_length:
                    endpoint_name = endpoint_name[:max_name_length-3] + "..."
                
                # URL'yi kısalt
                url = result['url']
                if len(url) > 35:
                    url = url[:32] + "..."
                
                table_data.append([
                    endpoint_name,
                    url,
                    result['method'],
                    str(result['status_code']) if result['status_code'] else "N/A",
                    f"{result['response_time']:.3f}",
                    status_text
                ])
            
            # Dinamik sütun genişlikleri hesapla
            page_width = A4[0] - 2*inch  # Sayfa genişliği - kenar boşlukları
            col_widths = [
                min(1.5*inch, max_name_length * 0.1*inch),  # Endpoint - dinamik
                2.2*inch,  # URL
                0.7*inch,  # Method
                0.7*inch,  # Status
                0.8*inch,  # Time
                0.8*inch   # Status
            ]
            
            # Toplam genişliği kontrol et ve ayarla
            total_width = sum(col_widths)
            if total_width > page_width:
                # Orantılı olarak küçült
                scale_factor = page_width / total_width
                col_widths = [w * scale_factor for w in col_widths]
            
            # Tablo stilini ayarla
            table = Table(table_data, colWidths=col_widths)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
                ('WORDWRAP', (0, 0), (-1, -1), True),  # Kelime kaydırma
                ('LEFTPADDING', (0, 0), (-1, -1), 3),  # Sol padding
                ('RIGHTPADDING', (0, 0), (-1, -1), 3),  # Sağ padding
            ]))
            
            story.append(table)
            story.append(Spacer(1, 20))
        
        # Hata mesajları (varsa)
        error_results = [r for r in detailed_results if not r['is_healthy'] and r['error_message']]
        if error_results:
            story.append(Paragraph("Error Details", heading_style))
            
            for result in error_results:
                error_text = f"<b>{result['name']}</b> ({result['url']}): {result['error_message']}"
                story.append(Paragraph(error_text, normal_style))
                story.append(Spacer(1, 6))
        
        # PDF'i oluştur
        doc.build(story)
        logger.info(f"PDF raporu kaydedildi: {filename}")
        return filename
    
    def get_sample_json_template(self) -> str:
        """Örnek JSON template döndür"""
        template = [
            {
                "name": "User API Health",
                "url": "https://api.example.com/users",
                "method": "GET",
                "headers": {
                    "Authorization": "Bearer your-token-here",
                    "Content-Type": "application/json"
                },
                "expected_status": 200,
                "timeout": 30,
                "description": "Kullanıcı listesi endpoint'i"
            },
            {
                "name": "Login API",
                "url": "https://api.example.com/auth/login",
                "method": "POST",
                "headers": {
                    "Content-Type": "application/json"
                },
                "body": {
                    "email": "test@example.com",
                    "password": "test123"
                },
                "expected_status": 200,
                "timeout": 30,
                "description": "Kullanıcı girişi endpoint'i"
            },
            {
                "name": "Database Health",
                "url": "https://api.example.com/health/db",
                "method": "GET",
                "expected_status": 200,
                "timeout": 10,
                "description": "Veritabanı sağlık kontrolü"
            }
        ]
        
        return json.dumps(template, indent=2, ensure_ascii=False)

# Test fonksiyonu
async def test_health_checker():
    """Health checker'ı test et"""
    checker = APIHealthChecker()
    
    # Örnek endpoint'ler
    sample_json = """
    [
        {
            "name": "Google Homepage",
            "url": "https://www.google.com",
            "method": "GET",
            "expected_status": 200,
            "timeout": 10,
            "description": "Google ana sayfası"
        },
        {
            "name": "GitHub API",
            "url": "https://api.github.com",
            "method": "GET",
            "expected_status": 200,
            "timeout": 15,
            "description": "GitHub API root endpoint"
        }
    ]
    """
    
    # Endpoint'leri yükle
    endpoints = checker.load_endpoints_from_json(sample_json)
    print(f"Yüklenen endpoint sayısı: {len(endpoints)}")
    
    # Health check yap
    results = await checker.check_all_endpoints()
    
    # Rapor oluştur
    report = checker.generate_report()
    print(f"Sağlıklı endpoint sayısı: {report['summary']['healthy_endpoints']}/{report['summary']['total_endpoints']}")
    
    # JSON'a kaydet
    filename = checker.save_results_to_json()
    print(f"Rapor kaydedildi: {filename}")
    
    return results

if __name__ == "__main__":
    asyncio.run(test_health_checker()) 