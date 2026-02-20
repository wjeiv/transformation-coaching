#!/usr/bin/env python3
"""
Auto-deployment script that updates version and date before redeploying
"""
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

def update_version():
    """Update version number and build date automatically"""
    version_file = Path("frontend/src/version.ts")
    
    if not version_file.exists():
        print("❌ version.ts file not found!")
        return False
    
    # Read current version
    content = version_file.read_text()
    
    # Extract current version
    version_match = re.search(r'APP_VERSION = "(\d+\.\d+\.\d+)"', content)
    if not version_match:
        print("❌ Could not find current version!")
        return False
    
    current_version = version_match.group(1)
    major, minor, patch = current_version.split('.')
    
    # Increment patch version
    new_patch = int(patch) + 1
    new_version = f"{major}.{minor}.{new_patch}"
    
    # Get current date/time with local timezone
    now = datetime.now()
    # Format with local time, ensuring AM/PM is correct
    build_date = now.strftime("%B %d, %Y at %I:%M %p")
    
    # Update content
    content = re.sub(
        r'APP_VERSION = "\d+\.\d+\.\d+"',
        f'APP_VERSION = "{new_version}"',
        content
    )
    content = re.sub(
        r'BUILD_DATE = "[^"]*"',
        f'BUILD_DATE = "{build_date}"',
        content
    )
    
    # Write updated content
    version_file.write_text(content)
    
    print(f"✅ Version updated: {current_version} → {new_version}")
    print(f"✅ Build date updated: {build_date}")
    
    return True

def deploy_production():
    """Deploy to production with updated version"""
    print("🚀 Starting production deployment...")
    
    # Update version first
    if not update_version():
        print("❌ Failed to update version!")
        return False
    
    # Run docker-compose production deployment
    try:
        print("🔨 Building and deploying containers...")
        result = subprocess.run(
            ["docker-compose", "-f", "docker-compose.prod.yml", "up", "-d", "--build"],
            check=True,
            capture_output=True,
            text=True
        )
        print("✅ Docker deployment completed successfully!")
        
        # Test mobile authentication after deployment
        print("📱 Testing mobile authentication...")
        test_result = subprocess.run(
            ["python", "test_prod_mobile.py"],
            capture_output=True,
            text=True
        )
        
        if test_result.returncode == 0:
            print("✅ Mobile authentication test passed!")
            print(test_result.stdout)
        else:
            print("⚠️ Mobile authentication test failed:")
            print(test_result.stderr)
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Deployment failed: {e}")
        print(f"Error output: {e.stderr}")
        return False
    except FileNotFoundError:
        print("❌ docker-compose command not found!")
        return False

def deploy_development():
    """Deploy to development with updated version"""
    print("🚀 Starting development deployment...")
    
    # Update version first
    if not update_version():
        print("❌ Failed to update version!")
        return False
    
    # Run docker-compose development deployment
    try:
        print("🔨 Building and deploying containers...")
        result = subprocess.run(
            ["docker-compose", "up", "-d", "--build"],
            check=True,
            capture_output=True,
            text=True
        )
        print("✅ Docker deployment completed successfully!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Deployment failed: {e}")
        print(f"Error output: {e.stderr}")
        return False
    except FileNotFoundError:
        print("❌ docker-compose command not found!")
        return False

def main():
    """Main deployment function"""
    if len(sys.argv) < 2:
        print("Usage: python deploy.py [prod|dev]")
        print("  prod - Deploy to production (docker-compose.prod.yml)")
        print("  dev  - Deploy to development (docker-compose.yml)")
        return
    
    env = sys.argv[1].lower()
    
    if env == "prod" or env == "production":
        success = deploy_production()
    elif env == "dev" or env == "development":
        success = deploy_development()
    else:
        print("❌ Invalid environment! Use 'prod' or 'dev'")
        return
    
    if success:
        print("🎉 Deployment completed successfully!")
    else:
        print("💥 Deployment failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
