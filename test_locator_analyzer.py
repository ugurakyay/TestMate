#!/usr/bin/env python3
"""
Test script for locator analyzer functionality
"""

import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ai_modules.locator_analyzer import LocatorAnalyzer

async def test_locator_analyzer():
    """Test the locator analyzer with sample HTML"""
    
    # Sample HTML content
    html_content = """
    <!DOCTYPE html>
    <html lang="tr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Test Sayfası</title>
    </head>
    <body>
        <div class="container">
            <h1>Giriş Sayfası</h1>
            
            <form id="loginForm" class="login-form">
                <div class="form-group">
                    <label for="username">Kullanıcı Adı:</label>
                    <input type="text" id="username" name="username" placeholder="Kullanıcı adınızı girin" class="form-control">
                </div>
                
                <div class="form-group">
                    <label for="password">Şifre:</label>
                    <input type="password" id="password" name="password" placeholder="Şifrenizi girin" class="form-control">
                </div>
                
                <button type="submit" id="loginButton" class="btn btn-primary">Giriş Yap</button>
                <button type="button" id="cancelButton" class="btn btn-secondary">İptal</button>
            </form>
            
            <div class="links">
                <a href="/forgot-password" id="forgotLink">Şifremi Unuttum</a>
                <a href="/register" id="registerLink">Yeni Hesap Oluştur</a>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Initialize locator analyzer
    analyzer = LocatorAnalyzer()
    
    # Test cases
    test_cases = [
        "Giriş Yap butonu",
        "Kullanıcı adı input alanı",
        "Şifre input alanı",
        "İptal butonu",
        "Şifremi Unuttum linki"
    ]
    
    print("Testing Locator Analyzer...")
    print("=" * 50)
    
    for element_desc in test_cases:
        print(f"\nTesting element description: '{element_desc}'")
        print("-" * 40)
        
        try:
            # Analyze locators
            locators = await analyzer.analyze_locators(
                page_source=html_content,
                element_description=element_desc
            )
            
            print(f"Found {len(locators)} locators:")
            
            for i, locator in enumerate(locators, 1):
                print(f"\n{i}. Type: {locator.get('type', 'Unknown')}")
                print(f"   Value: {locator.get('value', 'N/A')}")
                print(f"   Confidence: {locator.get('confidence', 'Unknown')}")
                print(f"   Reasoning: {locator.get('reasoning', 'No reasoning provided')}")
                print(f"   Selenium Code: {locator.get('selenium_code', 'N/A')}")
                
        except Exception as e:
            print(f"Error analyzing '{element_desc}': {e}")
    
    print("\n" + "=" * 50)
    print("Test completed!")

if __name__ == "__main__":
    asyncio.run(test_locator_analyzer()) 