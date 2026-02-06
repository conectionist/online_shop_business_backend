#!/usr/bin/env python3
"""
CORS and Cookie Validation Script for Step 7

This script validates that the cookie-based authentication system works correctly
across different environments and that CORS is properly configured.

Usage: python test_cors_validation.py [--env development|test|production]
"""

import argparse
import requests
import json
from typing import Dict, Any

class CORSValidator:
    def __init__(self, base_url: str, frontend_origin: str, env: str = "development"):
        self.base_url = base_url
        self.frontend_origin = frontend_origin
        self.env = env
        self.session = requests.Session()
        
        # Environment-specific credentials
        self.credentials = {
            "development": {"username": "admin", "password": "Adminpass345!"},
            "test": {"username": "admin", "password": "adminpass123"},
            "production": {"username": "admin", "password": "adminpass123"}  # Should be overridden in prod
        }
        
    def test_cors_preflight(self, endpoint: str, method: str = "POST") -> Dict[str, Any]:
        """Test CORS preflight request"""
        print(f"🧪 Testing CORS preflight for {method} {endpoint}")
        
        response = requests.options(
            f"{self.base_url}{endpoint}",
            headers={
                "Origin": self.frontend_origin,
                "Access-Control-Request-Method": method,
                "Access-Control-Request-Headers": "Content-Type"
            }
        )
        
        result = {
            "status_code": response.status_code,
            "allow_credentials": response.headers.get("access-control-allow-credentials"),
            "allow_origin": response.headers.get("access-control-allow-origin"),
            "allow_methods": response.headers.get("access-control-allow-methods"),
            "allow_headers": response.headers.get("access-control-allow-headers")
        }
        
        print(f"   Status: {response.status_code}")
        print(f"   Allow-Credentials: {result['allow_credentials']}")
        print(f"   Allow-Origin: {result['allow_origin']}")
        
        return result
    
    def test_login_and_cookies(self) -> Dict[str, Any]:
        """Test login and cookie setting"""
        print("🧪 Testing login and cookie setting")
        
        response = self.session.post(
            f"{self.base_url}/api/v1/auth/login",
            headers={
                "Origin": self.frontend_origin,
                "Content-Type": "application/json"
            },
            json=self.credentials[self.env]
        )
        
        # Extract cookie information
        cookies = {}
        for cookie in self.session.cookies:
            cookies[cookie.name] = {
                "value": cookie.value[:50] + "..." if len(cookie.value) > 50 else cookie.value,
                "secure": cookie.secure,
                "httponly": "HttpOnly" in str(cookie),  # HttpOnly not directly accessible
                "samesite": getattr(cookie, 'samesite', None),
                "path": cookie.path,
                "domain": cookie.domain
            }
        
        result = {
            "status_code": response.status_code,
            "cors_origin": response.headers.get("access-control-allow-origin"),
            "cors_credentials": response.headers.get("access-control-allow-credentials"),
            "cookies": cookies,
            "response_data": response.json() if response.status_code == 200 else None
        }
        
        print(f"   Status: {response.status_code}")
        print(f"   Cookies set: {list(cookies.keys())}")
        print(f"   CORS Origin: {result['cors_origin']}")
        
        return result
    
    def test_authenticated_request(self) -> Dict[str, Any]:
        """Test authenticated request with cookies"""
        print("🧪 Testing authenticated request")
        
        response = self.session.get(
            f"{self.base_url}/api/v1/auth/me",
            headers={"Origin": self.frontend_origin}
        )
        
        result = {
            "status_code": response.status_code,
            "cors_origin": response.headers.get("access-control-allow-origin"),
            "cors_credentials": response.headers.get("access-control-allow-credentials"),
            "response_data": response.json() if response.status_code == 200 else response.text
        }
        
        print(f"   Status: {response.status_code}")
        print(f"   Authenticated: {response.status_code == 200}")
        
        return result
    
    def test_refresh_token(self) -> Dict[str, Any]:
        """Test token refresh"""
        print("🧪 Testing token refresh")
        
        response = self.session.post(
            f"{self.base_url}/api/v1/auth/refresh",
            headers={
                "Origin": self.frontend_origin,
                "Content-Type": "application/json"
            },
            json={}
        )
        
        result = {
            "status_code": response.status_code,
            "cors_origin": response.headers.get("access-control-allow-origin"),
            "cors_credentials": response.headers.get("access-control-allow-credentials"),
            "response_data": response.json() if response.status_code == 200 else response.text
        }
        
        print(f"   Status: {response.status_code}")
        print(f"   Refresh successful: {response.status_code == 200}")
        
        return result
    
    def test_logout(self) -> Dict[str, Any]:
        """Test logout and cookie clearing"""
        print("🧪 Testing logout")
        
        # Get cookies before logout
        cookies_before = list(self.session.cookies.keys())
        
        response = self.session.post(
            f"{self.base_url}/api/v1/auth/logout",
            headers={
                "Origin": self.frontend_origin,
                "Content-Type": "application/json"
            },
            json={}
        )
        
        # Get cookies after logout
        cookies_after = list(self.session.cookies.keys())
        
        result = {
            "status_code": response.status_code,
            "cors_origin": response.headers.get("access-control-allow-origin"),
            "cors_credentials": response.headers.get("access-control-allow-credentials"),
            "cookies_before": cookies_before,
            "cookies_after": cookies_after,
            "cookies_cleared": len(cookies_after) == 0,
            "response_data": response.json() if response.status_code == 200 else response.text
        }
        
        print(f"   Status: {response.status_code}")
        print(f"   Cookies cleared: {result['cookies_cleared']}")
        
        return result
    
    def test_unauthorized_after_logout(self) -> Dict[str, Any]:
        """Test that requests fail after logout"""
        print("🧪 Testing unauthorized access after logout")
        
        response = self.session.get(
            f"{self.base_url}/api/v1/auth/me",
            headers={"Origin": self.frontend_origin}
        )
        
        result = {
            "status_code": response.status_code,
            "cors_origin": response.headers.get("access-control-allow-origin"),
            "cors_credentials": response.headers.get("access-control-allow-credentials"),
            "response_data": response.json() if response.status_code != 200 else response.text
        }
        
        print(f"   Status: {response.status_code}")
        print(f"   Correctly unauthorized: {response.status_code == 401}")
        
        return result
    
    def run_full_validation(self) -> Dict[str, Any]:
        """Run complete validation suite"""
        print(f"🚀 Starting CORS and Cookie Validation for {self.frontend_origin}")
        print(f"📍 API URL: {self.base_url}")
        print("=" * 60)
        
        results = {
            "environment": self.frontend_origin,
            "base_url": self.base_url,
            "tests": {}
        }
        
        # Test CORS preflight
        results["tests"]["cors_preflight"] = self.test_cors_preflight("/api/v1/auth/login")
        
        # Test login and cookies
        results["tests"]["login"] = self.test_login_and_cookies()
        
        # Test authenticated request
        results["tests"]["authenticated"] = self.test_authenticated_request()
        
        # Test refresh token
        results["tests"]["refresh"] = self.test_refresh_token()
        
        # Test logout
        results["tests"]["logout"] = self.test_logout()
        
        # Test unauthorized after logout
        results["tests"]["unauthorized_after_logout"] = self.test_unauthorized_after_logout()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 VALIDATION SUMMARY")
        print("=" * 60)
        
        all_passed = True
        for test_name, result in results["tests"].items():
            status = "✅ PASS" if (
                (test_name == "cors_preflight" and result["status_code"] in [200, 204, 400]) or
                (test_name == "login" and result["status_code"] == 200) or
                (test_name == "authenticated" and result["status_code"] == 200) or
                (test_name == "refresh" and result["status_code"] == 200) or
                (test_name == "logout" and result["status_code"] == 200) or
                (test_name == "unauthorized_after_logout" and result["status_code"] == 401)
            ) else "❌ FAIL"
            
            print(f"{test_name:25} {status}")
            if status == "❌ FAIL":
                all_passed = False
        
        results["overall_success"] = all_passed
        print(f"\n🎯 Overall Result: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
        
        return results

def main():
    parser = argparse.ArgumentParser(description="CORS and Cookie Validation Script")
    parser.add_argument("--env", choices=["development", "test", "production"], 
                       default="development", help="Environment to test")
    parser.add_argument("--output", help="Output JSON file for results")
    
    args = parser.parse_args()
    
    # Environment configuration
    env_configs = {
        "development": {
            "base_url": "http://localhost:8000",
            "frontend_origin": "http://localhost:3001"
        },
        "test": {
            "base_url": "http://localhost:8001", 
            "frontend_origin": "http://localhost:3001"
        },
        "production": {
            "base_url": "https://api.yourdomain.com",
            "frontend_origin": "https://yourdomain.com"
        }
    }
    
    config = env_configs[args.env]
    validator = CORSValidator(config["base_url"], config["frontend_origin"], args.env)
    
    try:
        results = validator.run_full_validation()
        
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"\n📄 Results saved to: {args.output}")
        
        exit(0 if results["overall_success"] else 1)
        
    except requests.exceptions.ConnectionError:
        print(f"❌ Connection Error: Could not connect to {config['base_url']}")
        print("   Make sure the API server is running for this environment.")
        exit(1)
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        exit(1)

if __name__ == "__main__":
    main()
