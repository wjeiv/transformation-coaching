# Cloudflare Authentication Debug Guide

## Issue Summary
Login works locally but fails when accessing through Cloudflare domain with nginx proxy.

## Root Causes Identified

### 1. CORS Configuration ✅ FIXED
- **Problem**: Backend only allowed localhost origins
- **Solution**: Added production domain to `BACKEND_CORS_ORIGINS` in `config.py`
- **Files**: `backend/app/core/config.py` lines 20-26, 36-42

### 2. Nginx Proxy Headers ✅ FIXED  
- **Problem**: Missing essential proxy headers for authentication
- **Solution**: Added comprehensive proxy headers and CORS handling
- **Files**: `frontend/nginx.conf` lines 11-37

## Cloudflare-Specific Checklist

### SSL/TLS Settings
- [ ] **SSL/TLS Mode**: Set to "Full (Strict)" not "Flexible"
- [ ] **Origin Certificate**: Use Cloudflare Origin Certificate on your server
- [ ] **HTTPS Redirect**: Ensure "Always Use HTTPS" is enabled

### Security Settings
- [ ] **WAF Rules**: Check if any Web Application Firewall rules block auth requests
- [ ] **Rate Limiting**: Ensure login endpoints aren't being rate-limited
- [ ] **Bot Fight Mode**: May interfere with authentication requests
- [ ] **DDoS Protection**: Check if it's blocking legitimate login attempts

### Network Settings
- [ ] **Argo Smart Routing**: Disable for testing authentication
- [ ] **WebSockets**: Ensure WebSocket connections are allowed if used
- [ ] **IP Geolocation**: May affect request headers

### DNS Settings
- [ ] **DNS Records**: Ensure A/AAAA records point to correct server
- [ ] **CNAME Flattening**: May affect subdomain routing
- [ ] **DNS Cache**: Clear Cloudflare DNS cache after changes

## Diagnostic Steps

### 1. Test with Diagnostic Script
```bash
python debug_auth_proxy.py
```
Update `PROD_BASE` with your actual domain and run the script.

### 2. Check Browser Console
- Open Developer Tools (F12)
- Go to Network tab
- Attempt login
- Look for CORS errors, failed requests, or 401/403 responses

### 3. Check Cloudflare Logs
- Go to Cloudflare Dashboard > Analytics & Logs
- Check HTTP requests to `/api/v1/auth/login`
- Look for blocked requests or unusual response codes

### 4. Test Direct Backend Access
If possible, test backend directly:
```
https://your-server-ip:8000/api/v1/auth/login
```

## Common Solutions

### Environment Variable Override
Set CORS origins via environment variable:
```bash
export BACKEND_CORS_ORIGINS='["https://your-domain.com","https://www.your-domain.com","http://localhost:3000"]'
```

### Cloudflare Page Rules
Create page rule to bypass certain features for auth endpoints:
```
your-domain.com/api/v1/auth/*
- Bypass: Security Level
- Bypass: Apps
```

### Origin Server Configuration
Ensure your origin server (nginx) is properly configured for HTTPS:
```nginx
server {
    listen 443 ssl;
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    # ... rest of config
}
```

## Deployment Steps

1. **Update CORS Origins**: Replace "your-domain.com" with actual domain
2. **Rebuild Docker Images**: `docker-compose build`
3. **Redeploy**: `docker-compose up -d`
4. **Test Authentication**: Use diagnostic script
5. **Check Cloudflare Settings**: Verify SSL/TLS mode is "Full (Strict)"

## Files Modified

- `backend/app/core/config.py` - Added production domain to CORS origins
- `frontend/nginx.conf` - Enhanced proxy headers and CORS handling
- `debug_auth_proxy.py` - Created diagnostic script (new file)

## Next Steps

1. Replace placeholder domains with your actual Cloudflare domain
2. Deploy the updated configuration
3. Test authentication through Cloudflare domain
4. Monitor Cloudflare analytics for any blocked requests
