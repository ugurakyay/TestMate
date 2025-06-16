"""
AI Test Tool - FastAPI Application
Main web interface for the AI-powered test automation tool
"""

import os
import json
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, HttpUrl
import uvicorn
from dotenv import load_dotenv

# Import our modules
from ai_engine.test_case_generator import TestCaseGenerator, TestCase
from ai_engine.locator_analyzer import LocatorAnalyzer, LocatorSuggestion
from test_runner.run_tests import TestRunner
from test_runner.result_parser import ResultParser

load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="AI Test Tool",
    description="AI-powered test automation tool for web, mobile, and API testing",
    version="1.0.0"
)

# Create necessary directories
os.makedirs("static", exist_ok=True)
os.makedirs("templates", exist_ok=True)
os.makedirs("uploads", exist_ok=True)
os.makedirs("reports", exist_ok=True)
os.makedirs("screenshots", exist_ok=True)

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Initialize AI components
test_generator = TestCaseGenerator()
locator_analyzer = LocatorAnalyzer()
test_runner = TestRunner()
result_parser = ResultParser()

# Pydantic models for API requests/responses
class WebTestRequest(BaseModel):
    url: HttpUrl
    page_content: Optional[str] = ""
    target_elements: Optional[List[str]] = None

class MobileTestRequest(BaseModel):
    app_name: str
    platform: str = "android"
    features: List[str] = []

class APITestRequest(BaseModel):
    base_url: HttpUrl
    endpoints: List[str] = []
    methods: List[str] = ["GET", "POST"]

class LocatorAnalysisRequest(BaseModel):
    html_content: str
    target_elements: Optional[List[str]] = None

class TestExecutionRequest(BaseModel):
    test_type: str  # 'web', 'mobile', 'api'
    test_files: List[str]
    config: Optional[Dict[str, Any]] = None

# HTML Templates
@app.get("/", response_class=HTMLResponse)
async def home(request):
    """Main dashboard page"""
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/generate", response_class=HTMLResponse)
async def generate_page(request):
    """Test case generation page"""
    return templates.TemplateResponse("generate.html", {"request": request})

@app.get("/analyze", response_class=HTMLResponse)
async def analyze_page(request):
    """Locator analysis page"""
    return templates.TemplateResponse("analyze.html", {"request": request})

@app.get("/run", response_class=HTMLResponse)
async def run_page(request):
    """Test execution page"""
    return templates.TemplateResponse("run.html", {"request": request})

@app.get("/reports", response_class=HTMLResponse)
async def reports_page(request):
    """Test reports page"""
    return templates.TemplateResponse("reports.html", {"request": request})

# API Endpoints

@app.post("/api/generate/web-tests")
async def generate_web_tests(request: WebTestRequest):
    """Generate web test cases using AI"""
    try:
        test_cases = test_generator.generate_web_test_cases(
            str(request.url), 
            request.page_content
        )
        
        # Save generated test cases
        filename = f"reports/web_tests_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        test_generator.save_test_cases(test_cases, filename)
        
        return {
            "success": True,
            "message": f"Generated {len(test_cases)} web test cases",
            "test_cases": [tc.__dict__ for tc in test_cases],
            "filename": filename
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate/mobile-tests")
async def generate_mobile_tests(request: MobileTestRequest):
    """Generate mobile test cases using AI"""
    try:
        app_info = {
            "name": request.app_name,
            "platform": request.platform,
            "features": request.features
        }
        
        test_cases = test_generator.generate_mobile_test_cases(app_info)
        
        # Save generated test cases
        filename = f"reports/mobile_tests_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        test_generator.save_test_cases(test_cases, filename)
        
        return {
            "success": True,
            "message": f"Generated {len(test_cases)} mobile test cases",
            "test_cases": [tc.__dict__ for tc in test_cases],
            "filename": filename
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate/api-tests")
async def generate_api_tests(request: APITestRequest):
    """Generate API test cases using AI"""
    try:
        api_spec = {
            "base_url": str(request.base_url),
            "endpoints": request.endpoints,
            "methods": request.methods
        }
        
        test_cases = test_generator.generate_api_test_cases(api_spec)
        
        # Save generated test cases
        filename = f"reports/api_tests_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        test_generator.save_test_cases(test_cases, filename)
        
        return {
            "success": True,
            "message": f"Generated {len(test_cases)} API test cases",
            "test_cases": [tc.__dict__ for tc in test_cases],
            "filename": filename
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analyze/locators")
async def analyze_locators(request: LocatorAnalysisRequest):
    """Analyze HTML and suggest optimal locators"""
    try:
        suggestions = locator_analyzer.analyze_page_locators(
            request.html_content,
            request.target_elements
        )
        
        # Save locator suggestions
        filename = f"reports/locators_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        locator_analyzer.save_locator_suggestions(suggestions, filename)
        
        return {
            "success": True,
            "message": f"Analyzed {len(suggestions)} elements",
            "suggestions": {
                element: [s.__dict__ for s in locators] 
                for element, locators in suggestions.items()
            },
            "filename": filename
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/run/tests")
async def run_tests(request: TestExecutionRequest, background_tasks: BackgroundTasks):
    """Execute tests in the background"""
    try:
        # Start test execution in background
        background_tasks.add_task(
            execute_tests_background,
            request.test_type,
            request.test_files,
            request.config
        )
        
        return {
            "success": True,
            "message": f"Started {request.test_type} test execution",
            "job_id": f"test_run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def execute_tests_background(test_type: str, test_files: List[str], config: Optional[Dict[str, Any]] = None):
    """Execute tests in background"""
    try:
        if test_type == "web":
            results = test_runner.run_web_tests(test_files, config.get("browser", "chrome") if config else "chrome")
        elif test_type == "mobile":
            results = test_runner.run_mobile_tests(test_files, config.get("platform", "android") if config else "android")
        elif test_type == "api":
            results = test_runner.run_api_tests(test_files, config.get("base_url", "") if config else "")
        else:
            raise ValueError(f"Unknown test type: {test_type}")
        
        # Save results
        filename = f"reports/{test_type}_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        test_runner.results = results
        test_runner.save_results(filename)
        
        # Generate report
        report_filename = f"reports/{test_type}_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        with open(report_filename, 'w') as f:
            f.write(test_runner.generate_report("html"))
        
        print(f"Test execution completed. Results saved to {filename}")
        
    except Exception as e:
        print(f"Error in background test execution: {e}")

@app.get("/api/reports/list")
async def list_reports():
    """List available test reports"""
    try:
        reports_dir = Path("reports")
        reports = []
        
        for file_path in reports_dir.glob("*"):
            if file_path.is_file():
                reports.append({
                    "name": file_path.name,
                    "size": file_path.stat().st_size,
                    "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
                    "type": file_path.suffix
                })
        
        return {
            "success": True,
            "reports": sorted(reports, key=lambda x: x["modified"], reverse=True)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/reports/{filename}")
async def get_report(filename: str):
    """Download a specific report file"""
    try:
        file_path = Path("reports") / filename
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Report not found")
        
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type="application/octet-stream"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/upload/html")
async def upload_html_file(file: UploadFile = File(...)):
    """Upload HTML file for locator analysis"""
    try:
        if not file.filename.endswith('.html'):
            raise HTTPException(status_code=400, detail="Only HTML files are allowed")
        
        # Save uploaded file
        file_path = Path("uploads") / file.filename
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Read HTML content
        with open(file_path, "r", encoding="utf-8") as f:
            html_content = f.read()
        
        return {
            "success": True,
            "message": "HTML file uploaded successfully",
            "filename": file.filename,
            "content_preview": html_content[:500] + "..." if len(html_content) > 500 else html_content
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/status")
async def get_status():
    """Get application status and health check"""
    try:
        # Check if AI components are available
        ai_status = {
            "test_generator": test_generator.api_key is not None,
            "locator_analyzer": locator_analyzer.api_key is not None
        }
        
        # Check disk space
        import shutil
        total, used, free = shutil.disk_usage(".")
        disk_usage = {
            "total_gb": total // (1024**3),
            "used_gb": used // (1024**3),
            "free_gb": free // (1024**3),
            "usage_percent": (used / total) * 100
        }
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "ai_components": ai_status,
            "disk_usage": disk_usage,
            "version": "1.0.0"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/config")
async def get_config():
    """Get application configuration"""
    try:
        config = {
            "openai_api_key_configured": bool(os.getenv("OPENAI_API_KEY")),
            "supported_browsers": ["chrome", "firefox", "safari"],
            "supported_platforms": ["android", "ios"],
            "max_file_size_mb": 10,
            "supported_file_types": [".html", ".json", ".py"]
        }
        
        return {
            "success": True,
            "config": config
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"error": "Resource not found", "detail": str(exc)}
    )

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)}
    )

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    # Create basic HTML templates if they don't exist
    create_basic_templates()
    
    # Run the application
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

def create_basic_templates():
    """Create basic HTML templates if they don't exist"""
    templates_dir = Path("templates")
    templates_dir.mkdir(exist_ok=True)
    
    # Dashboard template
    dashboard_html = """
<!DOCTYPE html>
<html>
<head>
    <title>AI Test Tool - Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .card { border: 1px solid #ddd; padding: 20px; margin: 10px; border-radius: 5px; }
        .button { background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; }
    </style>
</head>
<body>
    <h1>AI Test Tool Dashboard</h1>
    <div class="card">
        <h2>Quick Actions</h2>
        <a href="/generate" class="button">Generate Test Cases</a>
        <a href="/analyze" class="button">Analyze Locators</a>
        <a href="/run" class="button">Run Tests</a>
        <a href="/reports" class="button">View Reports</a>
    </div>
</body>
</html>
    """
    
    (templates_dir / "dashboard.html").write_text(dashboard_html)
    
    # Generate template
    generate_html = """
<!DOCTYPE html>
<html>
<head>
    <title>AI Test Tool - Generate Tests</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .form-group { margin: 10px 0; }
        label { display: block; margin-bottom: 5px; }
        input, textarea, select { width: 100%; padding: 8px; }
        .button { background-color: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 5px; }
    </style>
</head>
<body>
    <h1>Generate Test Cases</h1>
    <div class="form-group">
        <label>Test Type:</label>
        <select id="testType">
            <option value="web">Web Tests</option>
            <option value="mobile">Mobile Tests</option>
            <option value="api">API Tests</option>
        </select>
    </div>
    <div id="webForm" class="form-group">
        <label>URL:</label>
        <input type="url" id="url" placeholder="https://example.com">
        <label>Page Content (optional):</label>
        <textarea id="pageContent" rows="5"></textarea>
    </div>
    <button class="button" onclick="generateTests()">Generate Tests</button>
    <div id="result"></div>
    
    <script>
        async function generateTests() {
            const testType = document.getElementById('testType').value;
            const resultDiv = document.getElementById('result');
            
            try {
                let response;
                if (testType === 'web') {
                    response = await fetch('/api/generate/web-tests', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({
                            url: document.getElementById('url').value,
                            page_content: document.getElementById('pageContent').value
                        })
                    });
                }
                
                const data = await response.json();
                resultDiv.innerHTML = `<pre>${JSON.stringify(data, null, 2)}</pre>`;
            } catch (error) {
                resultDiv.innerHTML = `<p style="color: red;">Error: ${error.message}</p>`;
            }
        }
    </script>
</body>
</html>
    """
    
    (templates_dir / "generate.html").write_text(generate_html)
    
    # Create other basic templates
    for template_name in ["analyze.html", "run.html", "reports.html"]:
        basic_html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>AI Test Tool - {template_name.title()}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .card {{ border: 1px solid #ddd; padding: 20px; margin: 10px; border-radius: 5px; }}
    </style>
</head>
<body>
    <h1>{template_name.title().replace('.html', '')}</h1>
    <div class="card">
        <p>This page is under construction.</p>
        <a href="/">Back to Dashboard</a>
    </div>
</body>
</html>
        """
        (templates_dir / template_name).write_text(basic_html) 