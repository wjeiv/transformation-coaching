# Mobile Chrome Authentication Debug Guide

## Issue Summary
Mobile web Chrome login is not working through transformationcoaching262.com. This guide helps diagnose and fix mobile-specific authentication issues.

## Mobile Chrome Specific Issues

### 1. User Agent Handling
Mobile Chrome sends different user agents that may not be properly handled:
- **Android Chrome**: `Mozilla/5.0 (Linux; Android 10; SM-G975F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36`
- **iPhone Chrome**: `Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/91.0.4472.80 Mobile/15E148 Safari/604.1`

### 2. Mobile Network Conditions
- Slower network speeds
- Higher latency
- Intermittent connectivity
- Carrier-specific restrictions

### 3. Mobile Browser Security
- Stricter CORS policies
- Different cookie handling
- LocalStorage limitations
- HTTPS certificate validation

### 4. Touch Interface Issues
- Virtual keyboard behavior
- Touch event handling
- Viewport scaling
- Form input focus issues

## Quick Debug Steps

### 1. Run Mobile Debug Script
```bash
python debug_mobile_auth.py
```

This script tests:
- CORS headers with mobile user agents
- Login functionality with mobile user agents
- SSL certificate validation
- Network timeout handling
- Database user status

### 2. Manual Mobile Testing

#### Browser Console Testing
1. Open Chrome on mobile device
2. Navigate to transformationcoaching262.com
3. Press and hold the refresh button → "Inspect" (if available)
4. OR use Chrome DevTools on desktop with mobile device emulation

#### Network Tab Analysis
1. Open DevTools (F12) on desktop Chrome
2. Toggle device emulation (Ctrl+Shift+M)
3. Select mobile device (iPhone 12, Galaxy S20, etc.)
4. Go to Network tab
5. Attempt login
6. Check for:
   - Failed requests (red status codes)
   - CORS errors in console
   - Request/response headers
   - Timing issues

### 3. Common Mobile Issues & Solutions

#### Issue: CORS Errors on Mobile
**Symptoms**: Console shows "Access-Control-Allow-Origin" errors
**Debug Steps**:
1. Check if mobile user agent is in CORS allow list
2. Verify nginx CORS headers include mobile origins
3. Test with mobile device emulation

**Solution**:
```nginx
# In nginx.conf
add_header Access-Control-Allow-Origin $http_origin;
add_header Access-Control-Allow-Credentials true;
```

#### Issue: Login Timeout on Mobile
**Symptoms**: Login request times out or hangs
**Debug Steps**:
1. Check network speed on mobile device
2. Monitor request timing in DevTools
3. Check backend logs for timeout errors

**Solution**:
```python
# In API configuration
TIMEOUT = 30  # Increase timeout for mobile networks
```

#### Issue: SSL Certificate Problems
**Symptoms**: "Your connection is not private" warning
**Debug Steps**:
1. Check certificate validity on mobile device
2. Verify certificate chain is complete
3. Test with different mobile browsers

**Solution**:
- Use Cloudflare Origin Certificate
- Ensure SSL/TLS mode is "Full (Strict)"
- Install intermediate certificates

#### Issue: Virtual Keyboard Interference
**Symptoms**: Form inputs lose focus, layout breaks
**Debug Steps**:
1. Test form interaction on mobile device
2. Check viewport meta tag configuration
3. Monitor CSS layout changes during keyboard display

**Solution**:
```html
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
```

## Advanced Debugging

### 1. Mobile Device Logging
Use Chrome's remote debugging:
1. Connect mobile device to desktop via USB
2. Enable USB debugging on mobile device
3. Open `chrome://inspect` on desktop
4. Select mobile device to inspect

### 2. Network Throttling Testing
In Chrome DevTools:
1. Go to Network tab
2. Select "Throttling" dropdown
3. Choose "Slow 3G" or "Fast 3G"
4. Test login under throttled conditions

### 3. Mobile Browser Emulation
```javascript
// Test mobile user agent detection
navigator.userAgent.includes('Mobile')
navigator.userAgent.includes('Android')
navigator.userAgent.includes('iPhone')
```

## Configuration Files to Check

### Backend Configuration
- `backend/app/core/config.py` - CORS origins
- `backend/app/main.py` - CORS middleware setup
- `frontend/nginx.conf` - Proxy headers and CORS

### Frontend Configuration  
- `frontend/src/services/api.ts` - API base URL and timeouts
- `frontend/src/context/AuthContext.tsx` - Token handling
- `frontend/src/pages/LoginPage.tsx` - Form submission

### Environment Variables
```bash
# Should include production domain
BACKEND_CORS_ORIGINS=["https://transformationcoaching262.com","https://www.transformationcoaching262.com"]

# API URL for frontend
REACT_APP_API_URL=https://transformationcoaching262.com/api/v1
```

## Specific Tests to Run

### Test 1: CORS Preflight
```bash
# Test OPTIONS request with mobile user agent
curl -X OPTIONS https://transformationcoaching262.com/api/v1/auth/login \
  -H "Origin: https://transformationcoaching262.com" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type, Authorization" \
  -H "User-Agent: Mozilla/5.0 (Linux; Android 10; SM-G975F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36"
```

### Test 2: Login with Mobile Headers
```bash
# Test login with mobile user agent
curl -X POST http://localhost:8080/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -H "Origin: https://transformationcoaching262.com" \
  -H "User-Agent: Mozilla/5.0 (Linux; Android 10; SM-G975F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36" \
  -d '{"email":"admin@transformationcoaching.com","password":"FFester1!"}'
```

### Test 3: Certificate Validation
```bash
# Check SSL certificate
openssl s_client -connect transformationcoaching262.com:443 -servername transformationcoaching262.com
```

## Monitoring and Logging

### Backend Logs
Monitor these logs for mobile authentication attempts:
```bash
# Docker logs
docker-compose logs -f backend

# Look for entries like:
INFO: 172.68.133.123 - "POST /api/v1/auth/login HTTP/1.1" 200 OK
INFO: 172.68.133.123 - "POST /api/v1/auth/login HTTP/1.1" 401 Unauthorized
```

### Cloudflare Analytics
1. Go to Cloudflare Dashboard
2. Analytics & Logs > HTTP Requests
3. Filter by `/api/v1/auth/login`
4. Check for blocked requests or unusual response codes

## Common Fixes

### Fix 1: Update CORS Configuration
```python
# In backend/app/core/config.py
BACKEND_CORS_ORIGINS: List[str] = [
    "http://localhost:3000",
    "http://localhost:8000", 
    "http://127.0.0.1:3000",
    "https://transformationcoaching262.com",
    "https://www.transformationcoaching262.com",
    "https://transformationcoaching.wjeiv.com",
    "https://www.transformationcoaching.wjeiv.com",
]
```

### Fix 2: Add Mobile-Specific Headers
```nginx
# In frontend/nginx.conf
location /api/ {
    proxy_pass http://backend:8000;
    proxy_set_header User-Agent $http_user_agent;
    
    # Mobile-specific headers
    proxy_set_header X-Mobile-User-Agent $http_user_agent;
    proxy_set_header X-Mobile-Request "true";
    
    # Extended timeouts for mobile
    proxy_connect_timeout 60s;
    proxy_send_timeout 60s;
    proxy_read_timeout 60s;
}
```

### Fix 3: Frontend Mobile Detection
```typescript
// In frontend/src/services/api.ts
const isMobile = () => {
  return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
};

const api = axios.create({
  baseURL: API_URL,
  timeout: isMobile() ? 30000 : 10000, // Longer timeout for mobile
  headers: { 
    "Content-Type": "application/json",
    "X-Mobile-Client": isMobile().toString()
  }
});
```

## Next Steps

1. **Run the debug script** to identify specific issues
2. **Check CORS configuration** for mobile user agents
3. **Test SSL certificate** validity on mobile devices
4. **Monitor backend logs** for mobile authentication attempts
5. **Verify Cloudflare settings** aren't blocking mobile requests
6. **Test with real mobile devices** in addition to emulation

## Files Created/Modified

- `debug_mobile_auth.py` - Comprehensive mobile authentication testing script
- This guide - `MOBILE_AUTH_DEBUG.md` - Mobile-specific debugging instructions

## Support

If issues persist after following this guide:
1. Check the detailed JSON report from `debug_mobile_auth.py`
2. Review backend logs for specific error messages
3. Test with multiple mobile devices and browsers
4. Consider mobile-specific network conditions and constraints
