from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Request, Depends, Response, status
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import uvicorn
import os
import json
from typing import List, Optional, Dict, Any
import asyncio
import numpy as np
import pandas as pd
import shutil
import zipfile
from pathlib import Path
from starlette.middleware.sessions import SessionMiddleware
import hashlib
from datetime import datetime

# Import AI modules
from ai_modules.test_generator import TestCaseGenerator
from ai_modules.locator_analyzer import LocatorAnalyzer
from ai_modules.excel_processor import ExcelProcessor
from ai_modules.code_generator import CodeGenerator
from ai_modules.license_manager import LicenseManager
from ai_modules.contact_manager import ContactManager
from ai_modules.website_analyzer import WebsiteAnalyzer
from ai_modules.api_health_checker import APIHealthChecker
from ai_modules.workspace_manager import workspace_manager

# Import Database and Auth modules
from database.models import db_manager
from auth.middleware import AuthMiddleware, get_current_user, require_admin, check_feature_access

app = FastAPI(
    title="TestMate Studio",
    description="AI-Powered Test Automation Platform",
    version="1.0.0"
)

# Mount static files and templates
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# Initialize AI modules
test_generator = TestCaseGenerator()
locator_analyzer = LocatorAnalyzer()
excel_processor = ExcelProcessor()
code_generator = CodeGenerator()
website_analyzer = WebsiteAnalyzer()
api_health_checker = APIHealthChecker()

# Initialize license manager
license_manager = LicenseManager()

# Add session middleware with proper configuration
app.add_middleware(
    SessionMiddleware, 
    secret_key=os.environ.get('SESSION_SECRET_KEY', 'supersecretkey'),
    max_age=3600  # 1 hour session
)

# Pydantic models
class TestGenerationRequest(BaseModel):
    feature_description: str
    test_type: str
    framework: str = None
    additional_context: str = None
    use_ai: bool = False  # AI kullanım tercihi

class LocatorAnalysisRequest(BaseModel):
    page_source: str
    element_description: str
    preferred_locator_type: Optional[str] = None

class TestExecutionRequest(BaseModel):
    test_type: str
    execution_mode: str = "sequential"

class ProjectGenerationRequest(BaseModel):
    project_name: str
    scenarios: List[Dict[str, Any]]
    framework: Optional[str] = "selenium"
    project_type: Optional[str] = "python"

class LicenseRequest(BaseModel):
    license_key: str

class TrialRequest(BaseModel):
    email: str
    company: Optional[str] = None

class AdminLoginRequest(BaseModel):
    email: str
    password: str

class CreateUserLicenseRequest(BaseModel):
    user_email: str
    license_type: str
    duration_days: int = 30
    custom_features: Optional[Dict[str, Any]] = None

class UpdateUserLicenseRequest(BaseModel):
    user_email: str
    license_type: Optional[str] = None
    duration_days: Optional[int] = None
    status: Optional[str] = None

class AddAdminRequest(BaseModel):
    email: str
    password: str
    role: str = "admin"

class WebsiteAnalysisRequest(BaseModel):
    html_source: str
    url: str = ""
    analysis_type: str = "quick"  # "quick", "detailed", "full"

class DynamicWebsiteAnalysisRequest(BaseModel):
    url: str
    wait_time: int = 10
    login_credentials: Optional[Dict[str, str]] = None

class APIHealthCheckRequest(BaseModel):
    endpoints_json: str

# Authentication models
class LoginRequest(BaseModel):
    email: str
    password: str
    remember: bool = False

class RegisterRequest(BaseModel):
    full_name: str
    email: str
    company: Optional[str] = None
    password: str

class LogoutRequest(BaseModel):
    session_token: str

# Custom JSON encoder for numpy/pandas objects
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif pd.isna(obj):
            return None
        return super(CustomJSONEncoder, self).default(obj)

# Override default JSON encoder
app.json_encoder = CustomJSONEncoder

# Authentication Routes
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Login sayfası"""
    return templates.TemplateResponse('login.html', {'request': request})

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """Register sayfası"""
    return templates.TemplateResponse('register.html', {'request': request})

@app.post("/api/auth/login")
async def login(request: LoginRequest):
    """Kullanıcı girişi"""
    try:
        # Kullanıcı doğrulama
        user_data = db_manager.authenticate_user(request.email, request.password)
        
        if not user_data:
            raise HTTPException(status_code=401, detail="Geçersiz email veya şifre")
        
        # Cookie ayarları
        max_age = 86400 * 30 if request.remember else 86400  # 30 gün veya 1 gün
        response = JSONResponse({
            "success": True,
            "message": "Giriş başarılı",
            "user": {
                "email": user_data["email"],
                "full_name": user_data["full_name"],
                "role": user_data["role"]
            },
            "redirect_url": "/admin" if user_data["role"] == "admin" else "/dashboard"
        })
        response.set_cookie(
            key="session_token",
            value=user_data["session_token"],
            max_age=max_age,
            httponly=True,
            secure=False,  # HTTPS için True yapın
            samesite="lax"
        )
        return response
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Giriş hatası: {str(e)}")

@app.post("/api/auth/register")
async def register(request: RegisterRequest):
    """Kullanıcı kaydı"""
    try:
        # Input validation
        if not request.email or not request.password or not request.full_name:
            raise HTTPException(status_code=400, detail="Email, şifre ve ad soyad alanları zorunludur")
        
        if len(request.password) < 8:
            raise HTTPException(status_code=400, detail="Şifre en az 8 karakter olmalıdır")
        
        # Email format kontrolü
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, request.email):
            raise HTTPException(status_code=400, detail="Geçerli bir email adresi giriniz")
        
        # Kullanıcı oluştur
        result = db_manager.create_user(
            email=request.email,
            password=request.password,
            full_name=request.full_name,
            company=request.company
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return JSONResponse({
            "success": True,
            "message": "Hesap başarıyla oluşturuldu",
            "user_id": result["user_id"],
            "license": result["license"]
        })
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Register error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Kayıt hatası: {str(e)}")

@app.post("/api/auth/logout")
async def logout():
    """Kullanıcı çıkışı"""
    response = JSONResponse({"success": True, "message": "Başarıyla çıkış yapıldı"})
    response.delete_cookie("session_token")
    return response

@app.get("/api/auth/me")
async def get_current_user_info(request: Request):
    """Mevcut kullanıcı bilgileri"""
    try:
        user = get_current_user(request)
        license_data = db_manager.get_user_license(user["user_id"])
        
        return JSONResponse({
            "user": user,
            "license": license_data
        })
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Kullanıcı bilgisi alınamadı: {str(e)}")

# Page Routes (Authentication required)
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse('index.html', {'request': request})

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    """Dashboard page"""
    # Login kontrolü
    try:
        user = get_current_user(request)
        workspace_stats = {}
        experience_stats = {}
        return templates.TemplateResponse("dashboard.html", {"request": request, "user": user, "workspace_stats": workspace_stats, "experience_stats": experience_stats})
    except HTTPException:
        return RedirectResponse('/login', status_code=status.HTTP_302_FOUND)

@app.get("/projects", response_class=HTMLResponse)
async def projects_page(request: Request):
    """Projects page"""
    user = await get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    return templates.TemplateResponse("projects.html", {"request": request, "user": user})

@app.get("/generate", response_class=HTMLResponse)
async def generate_page(request: Request):
    """Test generation page"""
    # Login kontrolü
    try:
        user = get_current_user(request)
        return templates.TemplateResponse("generate.html", {"request": request})
    except HTTPException:
        return RedirectResponse('/login', status_code=status.HTTP_302_FOUND)

@app.get("/analyze", response_class=HTMLResponse)
async def analyze_page(request: Request):
    """Locator analysis page"""
    # Login kontrolü
    try:
        user = get_current_user(request)
        return templates.TemplateResponse("analyze.html", {"request": request})
    except HTTPException:
        return RedirectResponse('/login', status_code=status.HTTP_302_FOUND)

@app.get("/execute", response_class=HTMLResponse)
async def execute_page(request: Request):
    """Test execution page"""
    # Login kontrolü
    try:
        user = get_current_user(request)
        return templates.TemplateResponse("execute.html", {"request": request})
    except HTTPException:
        return RedirectResponse('/login', status_code=status.HTTP_302_FOUND)

@app.get("/excel", response_class=HTMLResponse)
async def excel_page(request: Request):
    """Excel processing page"""
    # Login kontrolü
    try:
        user = get_current_user(request)
        return templates.TemplateResponse("excel.html", {"request": request})
    except HTTPException:
        return RedirectResponse('/login', status_code=status.HTTP_302_FOUND)

@app.get("/website-analyzer", response_class=HTMLResponse)
async def website_analyzer_page(request: Request):
    """Website analyzer page"""
    # Login kontrolü
    try:
        user = get_current_user(request)
        return templates.TemplateResponse("website_analyzer.html", {"request": request})
    except HTTPException:
        return RedirectResponse('/login', status_code=status.HTTP_302_FOUND)

@app.get("/license", response_class=HTMLResponse)
async def license_page(request: Request):
    """License management page"""
    # Login kontrolü
    try:
        user = get_current_user(request)
        return templates.TemplateResponse("license.html", {"request": request})
    except HTTPException:
        return RedirectResponse('/login', status_code=status.HTTP_302_FOUND)

@app.get("/api-health-check", response_class=HTMLResponse)
async def api_health_check_page(request: Request):
    """API Health Check page"""
    # Login kontrolü
    try:
        user = get_current_user(request)
        return templates.TemplateResponse("api_health_check.html", {"request": request})
    except HTTPException:
        return RedirectResponse('/login', status_code=status.HTTP_302_FOUND)

@app.get("/admin/login", response_class=HTMLResponse)
async def admin_login_page(request: Request):
    return templates.TemplateResponse('admin_login.html', {'request': request, 'error': None})

@app.post("/api/admin/login")
async def admin_login(request: AdminLoginRequest, http_request: Request):
    """Admin girişi"""
    try:
        is_valid = license_manager.verify_admin_credentials(request.email, request.password)
        
        if is_valid:
            # Session oluştur
            http_request.session["admin_logged_in"] = True
            http_request.session["admin_email"] = request.email
            
            return JSONResponse({
                "success": True,
                "message": "Login successful"
            })
        else:
            raise HTTPException(status_code=401, detail="Invalid credentials")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during login: {str(e)}")

@app.get("/admin/logout")
async def admin_logout(request: Request):
    """Admin çıkışı"""
    request.session.clear()
    return RedirectResponse('/admin/login', status_code=status.HTTP_302_FOUND)

@app.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request):
    # Require login
    if not request.session.get("admin_logged_in"):
        return RedirectResponse('/admin/login', status_code=status.HTTP_302_FOUND)
    
    return templates.TemplateResponse('admin.html', {'request': request})

@app.post("/api/generate-test")
async def generate_test(request: TestGenerationRequest, http_request: Request):
    """Generate test cases using hybrid approach"""
    try:
        # Authentication ve feature access kontrolü
        access_check = check_feature_access(http_request, "test_generation")
        user = access_check["user"]
        
        # AI kullanım kontrolü (premium özellik)
        if request.use_ai:
            # Premium kullanıcı kontrolü
            if user["role"] != "admin":
                ai_access = db_manager.check_feature_access(user["user_id"], "ai_enhancement")
                if not ai_access["access"]:
                    return JSONResponse({
                        "success": True,
                        "message": "AI enhancement requires premium license. Using template-based generation.",
                        "use_ai": False,
                        "test_cases": await test_generator.generate_test_cases(
                            feature_description=request.feature_description,
                            test_type=request.test_type,
                            framework=request.framework,
                            additional_context=request.additional_context,
                            use_ai=False
                        )
                    })
        
        # Generate test cases
        test_cases = await test_generator.generate_test_cases(
            feature_description=request.feature_description,
            test_type=request.test_type,
            framework=request.framework,
            additional_context=request.additional_context,
            use_ai=request.use_ai
        )
        
        # Kullanım sayısını artır (admin değilse)
        if user["role"] != "admin":
            db_manager.increment_usage(user["user_id"], "test_generation")
        
        return JSONResponse({
            "success": True,
            "test_cases": test_cases,
            "use_ai": request.use_ai,
            "message": f"Generated {len(test_cases)} test cases for {request.test_type} testing using {'AI-enhanced' if request.use_ai else 'template-based'} approach"
        })
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating tests: {str(e)}")

@app.post("/api/analyze-locators")
async def analyze_locators(request: LocatorAnalysisRequest, http_request: Request):
    """Analyze page source and suggest locators"""
    try:
        # Authentication ve feature access kontrolü
        access_check = check_feature_access(http_request, "locator_analysis")
        user = access_check["user"]
        
        # Validate input
        if not request.page_source or not request.page_source.strip():
            raise HTTPException(status_code=400, detail="Page source cannot be empty")
        
        if not request.element_description or not request.element_description.strip():
            raise HTTPException(status_code=400, detail="Element description cannot be empty")
        
        # Analyze locators
        locators = await locator_analyzer.analyze_locators(
            page_source=request.page_source,
            element_description=request.element_description,
            preferred_locator_type=request.preferred_locator_type
        )
        
        # Kullanım sayısını artır (admin değilse)
        if user["role"] != "admin":
            db_manager.increment_usage(user["user_id"], "locator_analysis")
        
        return JSONResponse({
            "success": True,
            "locators": locators,
            "message": f"Found {len(locators)} locator suggestions"
        })
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing locators: {str(e)}")

@app.post("/api/execute-tests")
async def execute_tests(request: TestExecutionRequest, http_request: Request):
    """Execute test cases"""
    try:
        # Authentication ve feature access kontrolü
        access_check = check_feature_access(http_request, "test_execution")
        user = access_check["user"]
        
        # Test execution logic
        execution_results = await code_generator.execute_tests(
            test_type=request.test_type,
            execution_mode=request.execution_mode
        )
        
        # Kullanım sayısını artır (admin değilse)
        if user["role"] != "admin":
            db_manager.increment_usage(user["user_id"], "test_execution")
        
        return JSONResponse({
            "success": True,
            "results": execution_results,
            "message": f"Executed {request.test_type} tests in {request.execution_mode} mode"
        })
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error executing tests: {str(e)}")

@app.get("/api/download-template")
async def download_template():
    """Download Excel template"""
    try:
        template_path = "test_scenario.xlsx"
        if not os.path.exists(template_path):
            raise HTTPException(status_code=404, detail="Template file not found")
        
        return FileResponse(
            path=template_path,
            filename="test_scenario_template.xlsx",
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error downloading template: {str(e)}")

@app.post("/api/upload-excel")
async def upload_excel(file: UploadFile = File(...), http_request: Request = None):
    """Upload and process Excel file"""
    try:
        # Authentication kontrolü (opsiyonel - template indirme için)
        user = None
        if http_request:
            try:
                access_check = check_feature_access(http_request, "excel_processing")
                user = access_check["user"]
            except:
                pass  # Template indirme için authentication gerekli değil
        
        # Validate file
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(status_code=400, detail="Only Excel files are allowed")
        
        # Save file
        upload_dir = "uploads"
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, file.filename)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Process Excel file
        scenarios = excel_processor.read_test_scenarios(file_path)
        
        # Kullanım sayısını artır (admin değilse ve authenticated ise)
        if user and user["role"] != "admin":
            db_manager.increment_usage(user["user_id"], "excel_processing")
        
        # Clean up
        os.remove(file_path)
        
        return JSONResponse({
            "success": True,
            "scenarios": scenarios,
            "message": f"Processed {len(scenarios)} scenarios from Excel file"
        })
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing Excel file: {str(e)}")

@app.post("/api/generate-project")
async def generate_project(request: ProjectGenerationRequest, http_request: Request):
    """Generate complete test project from scenarios"""
    try:
        # Authentication ve feature access kontrolü
        access_check = check_feature_access(http_request, "excel_processing")
        user = access_check["user"]
        
        # Generate project
        project_structure = code_generator.generate_test_project(
            scenarios=request.scenarios,
            project_name=request.project_name,
            framework=request.framework,
            project_type=request.project_type
        )
        
        # Kullanım sayısını artır (admin değilse)
        if user["role"] != "admin":
            db_manager.increment_usage(user["user_id"], "excel_processing")
        
        return JSONResponse({
            "success": True,
            "project_path": project_structure["project_path"],
            "files_created": project_structure["files_created"],
            "test_count": project_structure["test_count"],
            "framework": project_structure["framework"],
            "message": f"Generated project '{request.project_name}' with {len(request.scenarios)} scenarios"
        })
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating project: {str(e)}")

@app.get("/api/test-types")
async def get_test_types():
    """Get available test types"""
    return JSONResponse({
        "test_types": [
            {"id": "web", "name": "Web Testing", "framework": "Selenium"},
            {"id": "mobile", "name": "Mobile Testing", "framework": "Appium"},
            {"id": "api", "name": "API Testing", "framework": "Requests"}
        ]
    })

@app.get("/api/frameworks/{test_type}")
async def get_frameworks(test_type: str):
    """Get available frameworks for a test type"""
    frameworks = {
        "web": ["Selenium", "Playwright", "Cypress"],
        "mobile": ["Appium", "XCUITest", "Espresso"],
        "api": ["Requests", "httpx", "aiohttp"]
    }
    
    return JSONResponse({
        "frameworks": frameworks.get(test_type, [])
    })

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return JSONResponse({
        "status": "healthy",
        "version": "1.0.0",
        "ai_modules": {
            "test_generator": "active",
            "locator_analyzer": "active",
            "excel_processor": "active",
            "code_generator": "active"
        }
    })

@app.get("/api/download-project/{project_name}")
async def download_project(project_name: str):
    """Download generated automation project as zip file"""
    try:
        project_path = os.path.join("generated_tests", project_name)
        
        if not os.path.exists(project_path):
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Zip dosyası oluştur
        zip_filename = f"{project_name}.zip"
        zip_path = os.path.join("exports", zip_filename)
        os.makedirs("exports", exist_ok=True)
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(project_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, project_path)
                    zipf.write(file_path, arcname)
        
        return FileResponse(
            path=zip_path,
            filename=zip_filename,
            media_type="application/zip"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating download: {str(e)}")

# License Management Endpoints
@app.post("/api/license/verify")
async def verify_license(request: dict):
    """Verify license key"""
    license_manager = LicenseManager()
    return license_manager.verify_license(request.get('license_key'))

@app.post("/api/license/trial")
async def start_trial(request: dict):
    """Start trial license"""
    license_manager = LicenseManager()
    return license_manager.generate_trial_license(request.get('email'))

@app.get("/api/license/info")
async def get_license_info():
    """Get current license information"""
    try:
        info = license_manager.get_license_info()
        return JSONResponse(info)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting license info: {str(e)}")

@app.get("/api/license/pricing")
async def get_pricing_plans():
    """Get pricing plans"""
    return license_manager.get_pricing_plans()

@app.get("/api/license/status")
async def get_license_status():
    """Get current license status"""
    return license_manager.get_license_status()

# Admin API Endpoints
@app.post("/api/admin/add-admin")
async def add_admin_user(request: AddAdminRequest):
    """Admin kullanıcı ekle"""
    try:
        result = license_manager.add_admin_user(request.email, request.password, request.role)
        return JSONResponse(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding admin: {str(e)}")

@app.post("/api/admin/create-license")
async def create_user_license(request: CreateUserLicenseRequest):
    """Kullanıcı için lisans oluştur"""
    try:
        result = license_manager.create_user_license(
            email=request.user_email,
            license_type=request.license_type,
            duration=request.duration_days
        )
        return JSONResponse(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating license: {str(e)}")

@app.get("/api/admin/users")
async def get_all_users():
    """Tüm kullanıcıları getir"""
    try:
        users = license_manager.get_users()
        return JSONResponse({
            "success": True,
            "users": users,
            "count": len(users)
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting users: {str(e)}")

@app.get("/api/admin/user/{email}")
async def get_user_by_email(email: str):
    """Email ile kullanıcı bul"""
    try:
        user = license_manager.get_user_by_email(email)
        if user:
            return JSONResponse({
                "success": True,
                "user": user
            })
        else:
            raise HTTPException(status_code=404, detail="User not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting user: {str(e)}")

@app.put("/api/admin/update-license")
async def update_user_license(request: UpdateUserLicenseRequest):
    """Kullanıcı lisansını güncelle"""
    try:
        result = license_manager.update_user_license(
            user_email=request.user_email,
            license_type=request.license_type,
            duration_days=request.duration_days,
            status=request.status
        )
        if result["success"]:
            return JSONResponse(result)
        else:
            raise HTTPException(status_code=404, detail=result["error"])
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating license: {str(e)}")

@app.post("/api/admin/revoke-license/{email}")
async def revoke_user_license(email: str):
    """Kullanıcı lisansını iptal et"""
    try:
        result = license_manager.revoke_user_license(email)
        if result["success"]:
            return JSONResponse(result)
        else:
            raise HTTPException(status_code=404, detail=result["error"])
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error revoking license: {str(e)}")

@app.post("/api/admin/extend-license/{email}/{days}")
async def extend_user_license(email: str, days: int):
    """Kullanıcı lisansını uzat"""
    try:
        result = license_manager.extend_user_license(email, days)
        if result["success"]:
            return JSONResponse(result)
        else:
            raise HTTPException(status_code=404, detail=result["error"])
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error extending license: {str(e)}")

@app.get("/api/admin/statistics")
async def get_license_statistics():
    """Lisans istatistiklerini getir"""
    try:
        stats = license_manager.get_statistics()
        return JSONResponse(stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting statistics: {str(e)}")

@app.get("/api/admin/report")
async def generate_license_report():
    """Lisans raporu oluştur"""
    try:
        report = license_manager.generate_license_report()
        return JSONResponse({
            "success": True,
            "report": report
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating report: {str(e)}")

# Contact endpoints
@app.post("/api/contact/plan-request")
async def submit_plan_request(request: dict):
    """Submit plan request via contact form"""
    try:
        # Validate required fields
        required_fields = ['plan_name', 'name', 'email', 'phone']
        for field in required_fields:
            if not request.get(field):
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
        
        # Save contact request
        contact_manager = ContactManager()
        result = contact_manager.submit_plan_request(request)
        
        if result['success']:
            return {"message": "Talebiniz başarıyla alındı! En kısa sürede size dönüş yapılacaktır."}
        else:
            raise HTTPException(status_code=500, detail=result['error'])
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/api/contact/test")
async def test_contact_connection():
    """Test contact system"""
    try:
        contact_manager = ContactManager()
        stats = contact_manager.get_statistics()
        return {"success": True, "message": "Contact system working", "stats": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Contact system error: {str(e)}")

# Admin contact endpoints
@app.get("/api/admin/contact-requests")
async def get_contact_requests():
    """Get all contact requests for admin"""
    try:
        contact_manager = ContactManager()
        requests = contact_manager.get_all_requests()
        return {"requests": requests}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching contact requests: {str(e)}")

@app.get("/api/admin/contact-statistics")
async def get_contact_statistics():
    """Get contact request statistics for admin"""
    try:
        contact_manager = ContactManager()
        stats = contact_manager.get_statistics()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching contact statistics: {str(e)}")

@app.put("/api/admin/contact-request/{request_id}")
async def update_contact_request(request_id: int, request: dict):
    """Update contact request status"""
    try:
        # Require admin login
        if not request.get("admin_logged_in"):
            raise HTTPException(status_code=401, detail="Admin login required")
        
        contact_manager = ContactManager()
        result = contact_manager.update_request_status(request_id, request.get("status"), request.get("processed"))
        
        return JSONResponse({
            "success": True,
            "message": "Contact request updated successfully",
            "data": result
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating contact request: {str(e)}")

@app.post("/api/admin/resend-license")
async def resend_license(request: dict, http_request: Request):
    """Resend license to user via email"""
    try:
        # Require admin login
        if not http_request.session.get("admin_logged_in"):
            raise HTTPException(status_code=401, detail="Admin login required")
        
        email = request.get("email")
        if not email:
            raise HTTPException(status_code=400, detail="Email is required")
        
        # Get user license info
        user_info = license_manager.get_user_info(email)
        if not user_info:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Send license via email
        success = license_manager.send_license_email(email, user_info)
        
        if success:
            return JSONResponse({
                "success": True,
                "message": "License sent successfully"
            })
        else:
            raise HTTPException(status_code=500, detail="Failed to send license email")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error resending license: {str(e)}")

@app.post("/api/admin/regenerate-license")
async def regenerate_license(request: dict, http_request: Request):
    """Regenerate license for user"""
    try:
        # Require admin login
        if not http_request.session.get("admin_logged_in"):
            raise HTTPException(status_code=401, detail="Admin login required")
        
        email = request.get("email")
        if not email:
            raise HTTPException(status_code=400, detail="Email is required")
        
        # Get current user info
        user_info = license_manager.get_user_info(email)
        if not user_info:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Generate new license key
        new_license_key = license_manager.generate_license_key()
        
        # Update user license
        success = license_manager.update_user_license(
            email=email,
            license_key=new_license_key,
            license_type=user_info.get("license_type"),
            duration_days=user_info.get("duration", 30)
        )
        
        if success:
            # Send new license via email
            updated_user_info = license_manager.get_user_info(email)
            license_manager.send_license_email(email, updated_user_info)
            
            return JSONResponse({
                "success": True,
                "message": "License regenerated and sent successfully",
                "data": {
                    "email": email,
                    "new_license_key": new_license_key
                }
            })
        else:
            raise HTTPException(status_code=500, detail="Failed to regenerate license")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error regenerating license: {str(e)}")

# Website Analysis endpoints
@app.post("/api/analyze-website")
async def analyze_website(request: WebsiteAnalysisRequest, http_request: Request):
    """Analyze website HTML source"""
    try:
        # Authentication ve feature access kontrolü
        access_check = check_feature_access(http_request, "website_analyzer")
        user = access_check["user"]
        
        # Analyze website
        analysis_result = await website_analyzer.analyze_website(
            html_source=request.html_source,
            url=request.url,
            analysis_type=request.analysis_type
        )
        
        # Kullanım sayısını artır (admin değilse)
        if user["role"] != "admin":
            db_manager.increment_usage(user["user_id"], "website_analyzer")
        
        return JSONResponse({
            "success": True,
            "analysis": analysis_result,
            "message": f"Website analysis completed for {request.url or 'provided HTML'}"
        })
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing website: {str(e)}")

@app.post("/api/generate-website-checklist")
async def generate_website_checklist(request: WebsiteAnalysisRequest):
    """Generate Excel checklist for website analysis"""
    try:
        # Lisans kontrolü
        license_check = license_manager.check_feature_access("website_analysis")
        if not license_check["access"]:
            raise HTTPException(status_code=403, detail=f"License error: {license_check['error']}")
        
        # Analyze website first
        analysis_results = website_analyzer.analyze_html_source(
            html_source=request.html_source,
            url=request.url,
            analysis_type=request.analysis_type
        )
        
        if "error" in analysis_results:
            raise HTTPException(status_code=400, detail=analysis_results["error"])
        
        # Generate Excel checklist
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"website_checklist_{timestamp}.xlsx"
        
        excel_path = website_analyzer.generate_excel_checklist(filename)
        
        return JSONResponse({
            "success": True,
            "message": "Excel checklist generated successfully",
            "data": {
                "filename": filename,
                "download_path": f"/api/download-website-checklist/{filename}",
                "analysis_summary": analysis_results.get("summary", {}),
                "analysis_type": request.analysis_type
            }
        })
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating checklist: {str(e)}")

@app.get("/api/download-website-checklist/{filename}")
async def download_website_checklist(filename: str):
    """Download generated website checklist Excel file"""
    try:
        file_path = os.path.join("exports", filename)
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")
        
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error downloading file: {str(e)}")

@app.post("/api/analyze-dynamic-website")
async def analyze_dynamic_website(request: DynamicWebsiteAnalysisRequest):
    """Dinamik web sitesi analizi (JavaScript ile render edilen siteler için)"""
    try:
        # Lisans kontrolü
        license_check = license_manager.check_feature_access("website_analysis")
        if not license_check["access"]:
            raise HTTPException(status_code=403, detail=f"License error: {license_check['error']}")
        
        # Dinamik analiz yap
        analysis_results = website_analyzer.analyze_dynamic_website(
            url=request.url,
            wait_time=request.wait_time,
            login_credentials=request.login_credentials
        )
        
        if "error" in analysis_results:
            raise HTTPException(status_code=400, detail=analysis_results["error"])
        
        return analysis_results
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analiz sırasında hata oluştu: {str(e)}")

@app.post("/api/generate-dynamic-checklist")
async def generate_dynamic_checklist(request: DynamicWebsiteAnalysisRequest):
    """Generate Excel checklist for dynamic website analysis"""
    try:
        # Lisans kontrolü
        license_check = license_manager.check_feature_access("website_analysis")
        if not license_check["access"]:
            raise HTTPException(status_code=403, detail=f"License error: {license_check['error']}")
        
        # Dinamik analiz yap
        analysis_results = website_analyzer.analyze_dynamic_website(
            url=request.url,
            wait_time=request.wait_time,
            login_credentials=request.login_credentials
        )
        
        if "error" in analysis_results:
            raise HTTPException(status_code=400, detail=analysis_results["error"])
        
        # Excel checklist oluştur
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"dynamic_website_checklist_{timestamp}.xlsx"
        
        excel_path = website_analyzer.generate_excel_checklist(filename)
        
        return JSONResponse({
            "success": True,
            "message": "Dinamik Excel checklist oluşturuldu",
            "data": {
                "filename": filename,
                "download_path": f"/api/download-website-checklist/{filename}",
                "analysis_summary": analysis_results.get("summary", {}),
                "login_used": request.login_credentials is not None
            }
        })
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Checklist oluşturma hatası: {str(e)}")

# API Health Check endpoints
@app.post("/api/health-check")
async def perform_health_check(request: APIHealthCheckRequest, http_request: Request):
    """Perform API health check"""
    try:
        # Authentication ve feature access kontrolü
        access_check = check_feature_access(http_request, "api_health_check")
        user = access_check["user"]
        
        # Perform health check
        health_results = await api_health_checker.check_endpoints(request.endpoints_json)
        
        # Kullanım sayısını artır (admin değilse)
        if user["role"] != "admin":
            db_manager.increment_usage(user["user_id"], "api_health_check")
        
        return JSONResponse({
            "success": True,
            "results": health_results,
            "message": f"Health check completed for {len(health_results)} endpoints"
        })
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error performing health check: {str(e)}")

@app.get("/api/health-check/template")
async def get_health_check_template():
    """Get sample JSON template for API health check"""
    try:
        template = api_health_checker.get_sample_json_template()
        
        return JSONResponse({
            "success": True,
            "message": "Health check template retrieved",
            "data": {
                "template": template,
                "description": "Bu template'i kullanarak kendi endpoint'lerinizi tanımlayabilirsiniz."
            }
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Template error: {str(e)}")

@app.get("/api/download-health-check/{filename}")
async def download_health_check_report(filename: str):
    """Health check raporunu indir"""
    try:
        # Dosya yolunu kontrol et
        file_path = Path(filename)
        
        # Güvenlik kontrolü - sadece belirli dizinlerden dosya indirilebilir
        if not file_path.exists() or "api_health_check" not in filename:
            raise HTTPException(status_code=404, detail="Dosya bulunamadı")
        
        # Dosya türünü kontrol et
        if filename.endswith('.json'):
            media_type = "application/json"
        elif filename.endswith('.pdf'):
            media_type = "application/pdf"
        else:
            media_type = "application/octet-stream"
        
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type=media_type
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Dosya indirme hatası: {str(e)}")

@app.get("/api/download-health-check-pdf/{filename}")
async def download_health_check_pdf(filename: str):
    """Health check PDF raporunu indir"""
    try:
        # JSON dosyasını PDF'e çevir
        json_filename = filename.replace('.pdf', '.json')
        json_path = Path(json_filename)
        
        if not json_path.exists():
            raise HTTPException(status_code=404, detail="JSON raporu bulunamadı")
        
        # JSON dosyasını oku
        with open(json_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        
        # PDF dosya adını oluştur
        pdf_filename = filename if filename.endswith('.pdf') else f"{filename}.pdf"
        pdf_path = Path(pdf_filename)
        
        # PDF oluştur
        api_checker = APIHealthChecker()
        api_checker.results = []  # Sonuçları JSON'dan yükle
        
        # JSON'dan sonuçları geri yükle
        for result_data in json_data.get('detailed_results', []):
            # HealthCheckResult objesi oluştur
            from ai_modules.api_health_checker import HealthCheckResult
            result = HealthCheckResult(
                endpoint_name=result_data['name'],
                url=result_data['url'],
                method=result_data['method'],
                status_code=result_data['status_code'],
                response_time=result_data['response_time'],
                is_healthy=result_data['is_healthy'],
                error_message=result_data.get('error_message'),
                response_size=result_data.get('response_size'),
                timestamp=datetime.fromisoformat(result_data['timestamp'])
            )
            api_checker.results.append(result)
        
        # PDF oluştur
        pdf_filename = api_checker.save_results_to_pdf(pdf_filename)
        
        return FileResponse(
            path=pdf_filename,
            filename=pdf_filename,
            media_type="application/pdf"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF oluşturma hatası: {str(e)}")

@app.post("/api/health-check/upload")
async def upload_endpoints_file(file: UploadFile = File(...)):
    """Upload endpoints JSON file and perform health check"""
    try:
        # Dosya türünü kontrol et
        if not file.filename.endswith('.json'):
            raise HTTPException(status_code=400, detail="Only JSON files are allowed")
        
        # Dosyayı oku
        content = await file.read()
        json_content = content.decode('utf-8')
        
        # Endpoint'leri yükle
        endpoints = api_health_checker.load_endpoints_from_json(json_content)
        
        # Health check yap
        results = await api_health_checker.check_all_endpoints()
        
        # Rapor oluştur
        report = api_health_checker.generate_report()
        
        # JSON dosyasına kaydet
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"api_health_check_{timestamp}.json"
        saved_filename = api_health_checker.save_results_to_json(filename)
        
        return JSONResponse({
            "success": True,
            "message": f"Health check completed. {report['summary']['healthy_endpoints']}/{report['summary']['total_endpoints']} endpoints healthy",
            "data": {
                "report": report,
                "filename": saved_filename,
                "download_path": f"/api/download-health-check/{saved_filename}",
                "uploaded_file": file.filename
            }
        })
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload error: {str(e)}")

# Feature detail pages
@app.get("/features/ai-test-generation", response_class=HTMLResponse)
async def ai_test_generation_page(request: Request):
    """AI Test Generation feature page"""
    return templates.TemplateResponse("features/ai-test-generation.html", {"request": request})

@app.get("/features/locator-analysis", response_class=HTMLResponse)
async def locator_analysis_page(request: Request):
    """Locator Analysis feature page"""
    return templates.TemplateResponse("features/locator-analysis.html", {"request": request})

@app.get("/features/excel-integration", response_class=HTMLResponse)
async def excel_integration_page(request: Request):
    """Excel Integration feature page"""
    return templates.TemplateResponse("features/excel-integration.html", {"request": request})

@app.get("/features/test-execution", response_class=HTMLResponse)
async def test_execution_page(request: Request):
    """Test Execution feature page"""
    return templates.TemplateResponse("features/test-execution.html", {"request": request})

@app.get("/features/website-analyzer", response_class=HTMLResponse)
async def website_analyzer_feature_page(request: Request):
    """Website Analyzer feature page"""
    return templates.TemplateResponse("features/website-analyzer.html", {"request": request})

@app.get("/features/api-health-check", response_class=HTMLResponse)
async def api_health_check_feature_page(request: Request):
    """API Health Check feature page"""
    return templates.TemplateResponse("features/api-health-check.html", {"request": request})

@app.get("/profile", response_class=HTMLResponse)
async def profile_page(request: Request):
    """Profil page"""
    # Login kontrolü
    try:
        user = get_current_user(request)
        workspace_stats = {}
        experience_stats = {}
        return templates.TemplateResponse("profile.html", {"request": request, "user": user, "workspace_stats": workspace_stats, "experience_stats": experience_stats})
    except HTTPException:
        return RedirectResponse('/login', status_code=status.HTTP_302_FOUND)

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 