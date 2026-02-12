# Fix Landing Page Not Showing

## Issue
The landing page is not showing at `http://localhost:3003` - instead showing the app interface.

## Solutions

### Solution 1: Clear Docker Build Cache and Rebuild (Recommended)

```powershell
cd frontend

# Stop and remove existing container
docker stop frontend
docker rm frontend

# Remove the image
docker rmi context-engineering-frontend

# Rebuild without cache
docker build --no-cache --build-arg NEXT_PUBLIC_API_URL=http://localhost:8003 -t context-engineering-frontend .

# Run again
docker run -d --name frontend -p 3003:80 -e NEXT_PUBLIC_API_URL=http://localhost:8003 context-engineering-frontend
```

### Solution 2: Clear Browser Cache

1. Open browser DevTools (F12)
2. Right-click the refresh button
3. Select "Empty Cache and Hard Reload"
4. Or use Ctrl+Shift+Delete to clear cache

### Solution 3: Access Root Route Directly

Make sure you're accessing:
- ✅ `http://localhost:3003/` (root - should show landing page)
- ❌ NOT `http://localhost:3003/app` (app route - shows app interface)

### Solution 4: Check if Running Locally

If running locally (not Docker), clear Next.js cache:

```powershell
cd frontend
rm -rf .next
npm run dev
```

Or on Windows:
```powershell
cd frontend
Remove-Item -Recurse -Force .next
npm run dev
```

## Verify the Fix

After rebuilding:
1. Go to `http://localhost:3003/` (root route)
2. You should see the landing page with:
   - "Context Engineering Research Assistant" title
   - "Start Researching" button
   - Features section
   - Technology stack section

3. Click "Start Researching" button to navigate to `/app` route
