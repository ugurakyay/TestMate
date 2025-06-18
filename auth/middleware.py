#!/usr/bin/env python3
"""
Authentication Middleware for TestMate Studio
"""

from fastapi import Request, HTTPException, status
from fastapi.responses import RedirectResponse
from typing import Optional, Dict, Any
import sys
import os

# Database modülünü import et
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.models import db_manager

class AuthMiddleware:
    """Authentication middleware"""
    
    def __init__(self):
        self.public_routes = {
            "/",
            "/login",
            "/register", 
            "/static",
            "/favicon.ico",
            "/api/health"
        }
        
        self.admin_routes = {
            "/admin",
            "/api/admin"
        }
    
    async def __call__(self, request: Request, call_next):
        """Middleware işlemi"""
        path = request.url.path
        
        # Public route kontrolü
        if self.is_public_route(path):
            return await call_next(request)
        
        # Session kontrolü
        session_token = self.get_session_token(request)
        if not session_token:
            return self.redirect_to_login(request)
        
        # Kullanıcı doğrulama
        user = db_manager.get_user_by_session(session_token)
        if not user:
            return self.redirect_to_login(request)
        
        # Admin route kontrolü
        if self.is_admin_route(path) and user["role"] != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin yetkisi gerekli"
            )
        
        # Request'e kullanıcı bilgilerini ekle
        request.state.user = user
        request.state.session_token = session_token
        
        response = await call_next(request)
        return response
    
    def is_public_route(self, path: str) -> bool:
        """Public route kontrolü"""
        return any(path.startswith(route) for route in self.public_routes)
    
    def is_admin_route(self, path: str) -> bool:
        """Admin route kontrolü"""
        return any(path.startswith(route) for route in self.admin_routes)
    
    def get_session_token(self, request: Request) -> Optional[str]:
        """Session token'ı al"""
        # Cookie'den al
        session_token = request.cookies.get("session_token")
        if session_token:
            return session_token
        
        # Header'dan al (API istekleri için)
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            return auth_header[7:]  # "Bearer " kısmını çıkar
        
        return None
    
    def redirect_to_login(self, request: Request):
        """Login sayfasına yönlendir"""
        if request.url.path.startswith("/api/"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Oturum açmanız gerekiyor"
            )
        else:
            return RedirectResponse(url="/login", status_code=302)

def get_current_user(request: Request) -> Dict[str, Any]:
    """Mevcut kullanıcıyı al"""
    # Önce request.state'den kontrol et (middleware varsa)
    if hasattr(request.state, 'user'):
        return request.state.user
    
    # Middleware yoksa session token'ı doğrudan kontrol et
    session_token = request.cookies.get("session_token")
    if not session_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Oturum açmanız gerekiyor"
        )
    
    user = db_manager.get_user_by_session(session_token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Geçersiz oturum"
        )
    
    return user

def require_admin(request: Request) -> Dict[str, Any]:
    """Admin kullanıcı kontrolü"""
    user = get_current_user(request)
    if user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin yetkisi gerekli"
        )
    return user

def check_feature_access(request: Request, feature: str) -> Dict[str, Any]:
    """Özellik erişim kontrolü"""
    user = get_current_user(request)
    
    # Admin kullanıcılar her şeye erişebilir
    if user["role"] == "admin":
        return {"access": True, "user": user}
    
    # Lisans kontrolü
    access_check = db_manager.check_feature_access(user["user_id"], feature)
    if not access_check["access"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=access_check["error"]
        )
    
    return {"access": True, "user": user, "license": access_check["license"]} 