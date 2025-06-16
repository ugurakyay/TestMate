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
    test_type: str  # "web", "mobile", "api"
    framework: Optional[str] = None
    additional_context: Optional[str] = None

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
    framework: Optional[str] = None

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

class DynamicWebsiteAnalysisRequest(BaseModel):
    url: str
    wait_time: int = 10
    login_credentials: Optional[Dict[str, str]] = None

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

# Page Routes
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse('index.html', {'request': request})

@app.get("/generate", response_class=HTMLResponse)
async def generate_page(request: Request):
    """Test generation page"""
    return templates.TemplateResponse("generate.html", {"request": request})

@app.get("/analyze", response_class=HTMLResponse)
async def analyze_page(request: Request):
    """Locator analysis page"""
    return templates.TemplateResponse("analyze.html", {"request": request})

@app.get("/execute", response_class=HTMLResponse)
async def execute_page(request: Request):
    """Test execution page"""
    return templates.TemplateResponse("execute.html", {"request": request})

@app.get("/excel", response_class=HTMLResponse)
async def excel_page(request: Request):
    """Excel processing page"""
    return templates.TemplateResponse("excel.html", {"request": request})

@app.get("/website-analyzer", response_class=HTMLResponse)
async def website_analyzer_page(request: Request):
    """Website analyzer page"""
    return templates.TemplateResponse("website_analyzer.html", {"request": request})

@app.get("/license", response_class=HTMLResponse)
async def license_page(request: Request):
    """License management page"""
    return templates.TemplateResponse("license.html", {"request": request})

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
async def generate_test(request: TestGenerationRequest):
    """Generate test cases using AI"""
    try:
        # Lisans kontrolü
        license_check = license_manager.check_feature_access("test_generation")
        if not license_check["access"]:
            raise HTTPException(status_code=403, detail=f"License error: {license_check['error']}")
        
        # Generate test cases
        test_cases = await test_generator.generate_test_cases(
            feature_description=request.feature_description,
            test_type=request.test_type,
            framework=request.framework,
            additional_context=request.additional_context
        )
        
        # Kullanım sayısını artır
        license_manager.increment_usage_dev("test_generation")
        
        return JSONResponse({
            "success": True,
            "test_cases": test_cases,
            "message": f"Generated {len(test_cases)} test cases for {request.test_type} testing"
        })
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating tests: {str(e)}")

@app.post("/api/analyze-locators")
async def analyze_locators(request: LocatorAnalysisRequest):
    """Analyze page source and suggest locators"""
    try:
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
        
        return JSONResponse({
            "success": True,
            "locators": locators,
            "message": f"Found {len(locators)} potential locators"
        })
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in analyze_locators: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error analyzing locators: {str(e)}")

@app.post("/api/execute-tests")
async def execute_tests(request: TestExecutionRequest):
    """Execute test cases"""
    try:
        from test_runner.runner import TestRunner
        runner = TestRunner()
        
        # Determine test path based on test_type
        if request.test_type == "web":
            test_path = "tests/web"
        elif request.test_type == "mobile":
            test_path = "tests/mobile"
        elif request.test_type == "api":
            test_path = "tests/api"
        else:
            raise HTTPException(status_code=400, detail=f"Unknown test type: {request.test_type}")
        
        # Check if test directory exists
        if not os.path.exists(test_path):
            raise HTTPException(status_code=404, detail=f"Test directory not found: {test_path}")
        
        # Prepare parameters
        parameters = {"execution_mode": request.execution_mode}
        
        # Run tests
        results = await runner.run_tests(
            test_path=test_path,
            test_type=request.test_type,
            parameters=parameters
        )
        
        return JSONResponse({
            "success": True,
            "results": results,
            "message": f"Executed tests with {results.get('passed', 0)} passed, {results.get('failed', 0)} failed"
        })
        
    except ImportError as e:
        raise HTTPException(status_code=500, detail=f"Test runner module not found: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error executing tests: {str(e)}")

@app.get("/api/download-template")
async def download_template():
    """Download Excel template for test scenarios"""
    try:
        template_path = excel_processor.create_test_scenario_template()
        return FileResponse(
            path=template_path,
            filename="test_scenarios_template.xlsx",
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating template: {str(e)}")

@app.post("/api/upload-excel")
async def upload_excel(file: UploadFile = File(...)):
    """Upload and process Excel file with test scenarios"""
    try:
        # Geçici dosya oluştur
        temp_path = f"temp_{file.filename}"
        with open(temp_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Excel dosyasını oku
        scenarios = excel_processor.read_test_scenarios(temp_path)
        
        # Doğrulama yap
        validation = excel_processor.validate_test_scenarios(scenarios)
        
        # Geçici dosyayı sil
        os.remove(temp_path)
        
        # JSON serileştirme için numpy değerlerini temizle
        def clean_for_json(obj):
            if isinstance(obj, dict):
                return {k: clean_for_json(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [clean_for_json(item) for item in obj]
            elif isinstance(obj, (np.integer, np.floating)):
                return obj.item()
            elif pd.isna(obj):
                return None
            else:
                return obj
        
        scenarios = clean_for_json(scenarios)
        validation = clean_for_json(validation)
        
        return JSONResponse({
            "success": True,
            "scenarios": scenarios,
            "validation": validation,
            "message": f"Processed {len(scenarios)} test scenarios"
        })
    
    except Exception as e:
        # Geçici dosyayı temizle
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise HTTPException(status_code=500, detail=f"Error processing Excel file: {str(e)}")

@app.post("/api/generate-project")
async def generate_project(request: ProjectGenerationRequest):
    """Generate automation project from Excel scenarios"""
    try:
        # Lisans kontrolü
        license_check = license_manager.check_feature_access("project_generation")
        if not license_check["access"]:
            raise HTTPException(status_code=403, detail=f"License error: {license_check['error']}")
        
        # Proje oluştur
        project_structure = code_generator.generate_test_project(
            scenarios=request.scenarios,
            project_name=request.project_name
        )
        
        # Kullanım sayısını artır
        license_manager.increment_usage_dev("project_generation")
        
        return JSONResponse({
            "success": True,
            "files": project_structure.get("files_created", []),
            "project_path": project_structure.get("project_path", ""),
            "message": f"Generated automation project: {project_structure.get('project_path', '')}"
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
async def analyze_website(request: WebsiteAnalysisRequest):
    """Analyze website HTML source and identify clickable elements"""
    try:
        # Lisans kontrolü
        license_check = license_manager.check_feature_access("website_analysis")
        if not license_check["access"]:
            raise HTTPException(status_code=403, detail=f"License error: {license_check['error']}")
        
        # Analyze website
        analysis_results = website_analyzer.analyze_html_source(
            html_source=request.html_source,
            url=request.url
        )
        
        if "error" in analysis_results:
            raise HTTPException(status_code=400, detail=analysis_results["error"])
        
        return JSONResponse({
            "success": True,
            "message": "Website analysis completed successfully",
            "data": analysis_results
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
            url=request.url
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
                "analysis_summary": analysis_results.get("summary", {})
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

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 