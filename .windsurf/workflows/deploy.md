---
description: Deploy application with automatic version updates
---

# Deployment Workflow

This workflow automatically updates the version number and build date before deploying, ensuring cache invalidation and proper versioning.

## Usage

### Production Deployment
```bash
python deploy.py prod
```

### Development Deployment  
```bash
python deploy.py dev
```

## What it does

1. **Auto-version update**: Increments patch version (e.g., 1.1.2 → 1.1.3)
2. **Build date update**: Sets current date/time in format "February 20, 2026 at 6:17 PM"
3. **Version file update**: Modifies `frontend/src/version.ts` automatically
4. **Docker deployment**: Runs `docker-compose up -d --build`
5. **Production testing**: Runs mobile authentication tests after production deployment

## Version Format

- **Pattern**: `MAJOR.MINOR.PATCH`
- **Auto-increment**: Only PATCH version is incremented automatically
- **Location**: `frontend/src/version.ts`

## Benefits

- **Cache busting**: New version forces browsers to download fresh assets
- **Version tracking**: Clear history of deployments
- **Mobile compatibility**: Ensures mobile users get latest fixes
- **Automation**: No manual version management required

## Files Modified

- `frontend/src/version.ts` - Version and build date
- Docker containers rebuilt and deployed

## Testing

After production deployment, the script automatically runs mobile authentication tests to verify the deployment was successful.
