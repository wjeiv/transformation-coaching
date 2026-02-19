# 🔍 Authentication Debug Guide

## 📊 Current Status
✅ **Admin account exists and is active**
- Email: admin@transformationcoaching.com
- Password: admin123
- Role: ADMIN
- Created: 2026-02-19 17:13:32

## 🎯 Debug Information Sources

### 1. **Backend Server Logs** (Most Important)
**How to access**: The backend server (Command ID: 120) logs all API requests

**What to look for**:
- Login attempts: `POST /api/v1/auth/login`
- Registration attempts: `POST /api/v1/auth/register`
- HTTP status codes (200, 400, 401, 500)
- Error messages and stack traces

**Example log entries**:
```
INFO:     127.0.0.1:58717 - "POST /api/v1/auth/login HTTP/1.1" 200 OK
INFO:     127.0.0.1:58717 - "POST /api/v1/auth/login HTTP/1.1" 401 Unauthorized
```

### 2. **Browser Developer Tools**
**Access**: Press **F12** or **Ctrl+Shift+I** in browser

**Console Tab**: Shows JavaScript errors
```javascript
// Look for errors like:
Failed to load resource: the server responded with status code 401
TypeError: Cannot read property 'token' of undefined
```

**Network Tab**: Shows HTTP requests/responses
- Click on failed requests
- Check Status code (400, 401, 500)
- View Response payload for error messages

### 3. **API Documentation (Interactive Testing)**
**URL**: http://localhost:8000/api/v1/docs

**How to use**:
1. Expand `/auth/login` endpoint
2. Click "Try it out"
3. Enter credentials:
   ```json
   {
     "email": "admin@transformationcoaching.com",
     "password": "admin123"
   }
   ```
4. Click "Execute" - see detailed response

### 4. **Database Debug Script**
**Run anytime**: `python debug_auth.py`

**Shows**:
- All user accounts in database
- Account status (active/inactive)
- Password hash verification
- Admin account verification

## 🔧 Common Issues & Solutions

### Issue: "Invalid credentials" (401 Unauthorized)
**Debug steps**:
1. Check if user exists: `python debug_auth.py`
2. Verify password: Should be `admin123`
3. Check backend logs for login attempts
4. Test via API docs

**Likely causes**:
- Wrong password
- User not found
- Password hashing mismatch

### Issue: CORS errors
**Debug steps**:
1. Check browser console for CORS errors
2. Verify `BACKEND_CORS_ORIGINS` in `dev.env`
3. Check backend logs for OPTIONS requests

**Current CORS settings**:
```
BACKEND_CORS_ORIGINS=["http://localhost:3000","http://localhost:8000","http://127.0.0.1:3000"]
```

### Issue: "User already exists" (400 Bad Request)
**Debug steps**:
1. Check database: `python debug_auth.py`
2. Use different email for registration
3. Or delete existing user from database

### Issue: Frontend not loading
**Debug steps**:
1. Check frontend server: http://localhost:3000
2. Check browser console for JavaScript errors
3. Verify `REACT_APP_API_URL` in frontend environment

## 🚀 Quick Debug Commands

### Check Backend Status
```powershell
# Check if backend is running
Invoke-WebRequest -Uri http://localhost:8000/health -UseBasicParsing

# Check backend logs
# Look at Command ID: 120 output
```

### Check Frontend Status
```powershell
# Check if frontend is running
Invoke-WebRequest -Uri http://localhost:3000 -UseBasicParsing
```

### Debug Users
```powershell
# Run debug script
python debug_auth.py
```

### Test Login via API
```powershell
# Test login directly
$headers = @{
    "Content-Type" = "application/json"
}
$body = @{
    email = "admin@transformationcoaching.com"
    password = "admin123"
} | ConvertTo-Json

Invoke-RestMethod -Uri http://localhost:8000/api/v1/auth/login -Method POST -Headers $headers -Body $body
```

## 📱 Real-time Debugging

### While attempting login:
1. **Watch backend logs** (Command ID: 120)
2. **Watch browser Network tab** (F12 > Network)
3. **Check browser Console** (F12 > Console)

### Expected successful login flow:
1. Frontend sends POST to `/api/v1/auth/login`
2. Backend responds with 200 OK + token
3. Frontend stores token and redirects

### Expected failed login flow:
1. Frontend sends POST to `/api/v1/auth/login`
2. Backend responds with 401 Unauthorized + error message
3. Frontend shows error to user

## 🎯 Next Steps

If you're still having issues:
1. **Check backend logs** for the specific error
2. **Test via API docs** to isolate frontend vs backend issues
3. **Run debug script** to verify user account
4. **Check browser console** for JavaScript errors

The debug information is comprehensive - you should be able to identify any authentication issues quickly!
