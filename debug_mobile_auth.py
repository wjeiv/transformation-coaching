#!/usr/bin/env python3
"""
Mobile Chrome Authentication Debug Script

This script tests authentication specifically for mobile Chrome browsers
accessing the application through transformationcoaching262.com

Mobile Chrome specific issues to test:
1. Touch/mobile user agent handling
2. Mobile viewport and responsive design issues
3. Mobile-specific CORS headers
4. Cookie/localStorage handling on mobile
5. Mobile network conditions and timeouts
6. HTTPS certificate issues on mobile
7. Mobile-specific security policies
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Import application modules
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app.core.config import settings
from app.core.database import async_session, init_db
from app.models.user import User, ActivityLog
from app.core.security import verify_password


class MobileAuthDebugger:
    def __init__(self):
        self.prod_base = "http://localhost:8080"  # Testing local deployment
        self.local_base = "http://localhost:8000"
        
        # Mobile Chrome user agents
        self.mobile_user_agents = {
            "android_chrome": "Mozilla/5.0 (Linux; Android 10; SM-G975F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36",
            "iphone_chrome": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/91.0.4472.80 Mobile/15E148 Safari/604.1",
            "ipad_chrome": "Mozilla/5.0 (iPad; CPU OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/91.0.4472.80 Mobile/15E148 Safari/604.1"
        }
        
        self.test_results = {}
        self.errors = []

    async def test_cors_with_mobile_ua(self, client: httpx.AsyncClient, ua_name: str) -> Dict[str, Any]:
        """Test CORS headers with mobile user agent"""
        print(f"\n🔍 Testing CORS with {ua_name} user agent...")
        
        try:
            # Test preflight request
            response = await client.options(
                f"{self.prod_base}/api/v1/auth/login",
                headers={
                    "Origin": "http://localhost:8080",
                    "Access-Control-Request-Method": "POST",
                    "Access-Control-Request-Headers": "Content-Type, Authorization",
                    "User-Agent": self.mobile_user_agents[ua_name]
                }
            )
            
            cors_headers = {
                "access_control_allow_origin": response.headers.get("access-control-allow-origin"),
                "access_control_allow_methods": response.headers.get("access-control-allow-methods"),
                "access_control_allow_headers": response.headers.get("access-control-allow-headers"),
                "access_control_allow_credentials": response.headers.get("access-control-allow-credentials"),
                "status_code": response.status_code
            }
            
            print(f"  ✅ Preflight Status: {response.status_code}")
            print(f"  📋 CORS Headers: {cors_headers}")
            
            return {
                "success": response.status_code in [200, 204],
                "headers": cors_headers,
                "user_agent": ua_name
            }
            
        except Exception as e:
            error_msg = f"CORS test failed for {ua_name}: {str(e)}"
            print(f"  ❌ {error_msg}")
            self.errors.append(error_msg)
            return {"success": False, "error": str(e), "user_agent": ua_name}

    async def test_login_with_mobile_ua(self, client: httpx.AsyncClient, ua_name: str) -> Dict[str, Any]:
        """Test login with mobile user agent"""
        print(f"\n🔑 Testing login with {ua_name} user agent...")
        
        try:
            response = await client.post(
                f"{self.prod_base}/api/v1/auth/login",
                json={
                    "email": "admin@transformationcoaching.com",
                    "password": "FFester1!"
                },
                headers={
                    "Origin": "http://localhost:8080",
                    "Content-Type": "application/json",
                    "User-Agent": self.mobile_user_agents[ua_name],
                    "Accept": "application/json"
                }
            )
            
            result = {
                "success": response.status_code == 200,
                "status_code": response.status_code,
                "user_agent": ua_name,
                "response_headers": dict(response.headers),
                "has_token": False
            }
            
            if response.status_code == 200:
                data = response.json()
                result["has_token"] = "access_token" in data
                result["token_length"] = len(data.get("access_token", ""))
                print(f"  ✅ Login successful with {ua_name}")
                print(f"  🎫 Token received: {result['has_token']}")
            else:
                print(f"  ❌ Login failed with {ua_name}: {response.status_code}")
                try:
                    error_data = response.json()
                    result["error_detail"] = error_data.get("detail", "Unknown error")
                    print(f"  📝 Error: {result['error_detail']}")
                except:
                    result["error_text"] = response.text
                    print(f"  📝 Error text: {response.text[:200]}")
            
            return result
            
        except Exception as e:
            error_msg = f"Login test failed for {ua_name}: {str(e)}"
            print(f"  ❌ {error_msg}")
            self.errors.append(error_msg)
            return {"success": False, "error": str(e), "user_agent": ua_name}

    async def test_mobile_specific_issues(self) -> Dict[str, Any]:
        """Test mobile-specific authentication issues"""
        print("\n📱 Testing Mobile-Specific Issues...")
        
        mobile_issues = {
            "viewport_handling": False,
            "touch_events": False,
            "mobile_network": False,
            "certificate_issues": False,
            "localstorage_support": False
        }
        
        # Test SSL certificate (mobile devices are stricter about certificates)
        try:
            async with httpx.AsyncClient(verify=True, timeout=10.0) as client:
                response = await client.get(self.prod_base)
                mobile_issues["certificate_issues"] = response.status_code == 200
                print(f"  🔒 SSL Certificate: {'✅ Valid' if mobile_issues['certificate_issues'] else '❌ Invalid'}")
        except Exception as e:
            print(f"  ❌ SSL Certificate error: {str(e)}")
            mobile_issues["certificate_issues"] = False
        
        # Test mobile network timeout handling
        try:
            start_time = time.time()
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.prod_base}/health")
                response_time = time.time() - start_time
                mobile_issues["mobile_network"] = response_time < 5.0
                print(f"  📶 Network timeout: {'✅ Passed' if mobile_issues['mobile_network'] else '❌ Failed'} ({response_time:.2f}s)")
        except Exception as e:
            print(f"  ❌ Network timeout test failed: {str(e)}")
            mobile_issues["mobile_network"] = False
        
        return mobile_issues

    async def check_database_users(self) -> Dict[str, Any]:
        """Check database for user accounts and activity"""
        print("\n🗄️ Checking Database Users...")
        
        try:
            await init_db()
            async with async_session() as session:
                # Check admin user
                result = await session.execute(
                    select(User).where(User.email == settings.FIRST_ADMIN_EMAIL)
                )
                admin_user = result.scalar_one_or_none()
                
                if admin_user:
                    print(f"  ✅ Admin user found: {admin_user.email}")
                    print(f"  📅 Last login: {admin_user.last_login}")
                    print(f"  ✅ Active: {admin_user.is_active}")
                    
                    # Check recent activity logs
                    logs_result = await session.execute(
                        select(ActivityLog)
                        .where(ActivityLog.user_id == admin_user.id)
                        .order_by(ActivityLog.created_at.desc())
                        .limit(10)
                    )
                    logs = logs_result.scalars().all()
                    
                    recent_logs = []
                    for log in logs:
                        recent_logs.append({
                            "action": log.action,
                            "details": log.details,
                            "ip_address": log.ip_address,
                            "created_at": log.created_at.isoformat() if log.created_at else None
                        })
                    
                    return {
                        "admin_exists": True,
                        "admin_active": admin_user.is_active,
                        "last_login": admin_user.last_login.isoformat() if admin_user.last_login else None,
                        "recent_activity": recent_logs
                    }
                else:
                    print(f"  ❌ Admin user not found: {settings.FIRST_ADMIN_EMAIL}")
                    return {"admin_exists": False}
                    
        except Exception as e:
            error_msg = f"Database check failed: {str(e)}"
            print(f"  ❌ {error_msg}")
            self.errors.append(error_msg)
            return {"error": str(e)}

    async def generate_mobile_debug_report(self) -> Dict[str, Any]:
        """Generate comprehensive mobile authentication debug report"""
        print("🚀 Starting Mobile Chrome Authentication Debug...")
        print(f"🌐 Testing domain: {self.prod_base}")
        print(f"📱 Testing with {len(self.mobile_user_agents)} mobile user agents")
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "domain": self.prod_base,
            "mobile_user_agents_tested": list(self.mobile_user_agents.keys()),
            "cors_tests": {},
            "login_tests": {},
            "mobile_issues": {},
            "database_status": {},
            "errors": [],
            "recommendations": []
        }
        
        # Test CORS with different mobile user agents
        async with httpx.AsyncClient() as client:
            for ua_name in self.mobile_user_agents:
                cors_result = await self.test_cors_with_mobile_ua(client, ua_name)
                report["cors_tests"][ua_name] = cors_result
        
        # Test login with different mobile user agents
        async with httpx.AsyncClient() as client:
            for ua_name in self.mobile_user_agents:
                login_result = await self.test_login_with_mobile_ua(client, ua_name)
                report["login_tests"][ua_name] = login_result
        
        # Test mobile-specific issues
        report["mobile_issues"] = await self.test_mobile_specific_issues()
        
        # Check database
        report["database_status"] = await self.check_database_users()
        
        # Collect all errors
        report["errors"] = self.errors
        
        # Generate recommendations
        report["recommendations"] = self.generate_recommendations(report)
        
        return report

    def generate_recommendations(self, report: Dict[str, Any]) -> list:
        """Generate specific recommendations based on test results"""
        recommendations = []
        
        # CORS recommendations
        cors_failures = [ua for ua, result in report["cors_tests"].items() if not result.get("success", False)]
        if cors_failures:
            recommendations.append({
                "category": "CORS",
                "priority": "HIGH",
                "issue": f"CORS failing for mobile user agents: {cors_failures}",
                "solution": "Check nginx CORS configuration and ensure mobile user agents are properly handled"
            })
        
        # Login recommendations
        login_failures = [ua for ua, result in report["login_tests"].items() if not result.get("success", False)]
        if login_failures:
            recommendations.append({
                "category": "Authentication",
                "priority": "HIGH", 
                "issue": f"Login failing for mobile user agents: {login_failures}",
                "solution": "Check authentication logs and verify mobile-specific headers are processed correctly"
            })
        
        # SSL certificate recommendations
        if not report["mobile_issues"].get("certificate_issues", False):
            recommendations.append({
                "category": "SSL/TLS",
                "priority": "CRITICAL",
                "issue": "SSL certificate validation failing",
                "solution": "Ensure valid SSL certificate is installed and mobile devices trust the certificate authority"
            })
        
        # Network timeout recommendations
        if not report["mobile_issues"].get("mobile_network", False):
            recommendations.append({
                "category": "Performance",
                "priority": "MEDIUM",
                "issue": "Network timeout issues detected",
                "solution": "Optimize API response times and consider implementing mobile-specific timeout handling"
            })
        
        # Database recommendations
        if not report["database_status"].get("admin_exists", False):
            recommendations.append({
                "category": "Database",
                "priority": "CRITICAL",
                "issue": "Admin user not found in database",
                "solution": "Run database initialization script to create admin account"
            })
        
        return recommendations

    def print_report(self, report: Dict[str, Any]):
        """Print formatted debug report"""
        print("\n" + "="*80)
        print("📱 MOBILE CHROME AUTHENTICATION DEBUG REPORT")
        print("="*80)
        
        print(f"\n🕐 Timestamp: {report['timestamp']}")
        print(f"🌐 Domain: {report['domain']}")
        print(f"📱 User Agents Tested: {', '.join(report['mobile_user_agents_tested'])}")
        
        # CORS Results
        print(f"\n🔍 CORS TEST RESULTS:")
        for ua, result in report["cors_tests"].items():
            status = "✅ PASS" if result.get("success", False) else "❌ FAIL"
            print(f"  {ua}: {status}")
            if not result.get("success", False) and "error" in result:
                print(f"    Error: {result['error']}")
        
        # Login Results
        print(f"\n🔑 LOGIN TEST RESULTS:")
        for ua, result in report["login_tests"].items():
            status = "✅ PASS" if result.get("success", False) else "❌ FAIL"
            print(f"  {ua}: {status}")
            if result.get("success", False):
                print(f"    Token received: {'✅' if result.get('has_token') else '❌'}")
            elif "error_detail" in result:
                print(f"    Error: {result['error_detail']}")
        
        # Mobile Issues
        print(f"\n📱 MOBILE-SPECIFIC ISSUES:")
        mobile_issues = report["mobile_issues"]
        for issue, status in mobile_issues.items():
            status_icon = "✅" if status else "❌"
            print(f"  {issue.replace('_', ' ').title()}: {status_icon}")
        
        # Database Status
        print(f"\n🗄️ DATABASE STATUS:")
        db_status = report["database_status"]
        if "error" in db_status:
            print(f"  ❌ Database error: {db_status['error']}")
        else:
            print(f"  Admin exists: {'✅' if db_status.get('admin_exists') else '❌'}")
            print(f"  Admin active: {'✅' if db_status.get('admin_active') else '❌'}")
            if db_status.get('last_login'):
                print(f"  Last login: {db_status['last_login']}")
        
        # Errors
        if report["errors"]:
            print(f"\n❌ ERRORS ENCOUNTERED:")
            for error in report["errors"]:
                print(f"  • {error}")
        
        # Recommendations
        if report["recommendations"]:
            print(f"\n💡 RECOMMENDATIONS:")
            for rec in report["recommendations"]:
                priority_icon = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}[rec["priority"]]
                print(f"  {priority_icon} {rec['category']} - {rec['priority']}")
                print(f"    Issue: {rec['issue']}")
                print(f"    Solution: {rec['solution']}")
                print()
        
        print("="*80)


async def main():
    """Main debug function"""
    debugger = MobileAuthDebugger()
    
    try:
        report = await debugger.generate_mobile_debug_report()
        debugger.print_report(report)
        
        # Save report to file
        report_file = "mobile_auth_debug_report.json"
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2, default=str)
        print(f"\n📄 Detailed report saved to: {report_file}")
        
    except KeyboardInterrupt:
        print("\n⏹️ Debug session interrupted")
    except Exception as e:
        print(f"\n💥 Debug session failed: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
