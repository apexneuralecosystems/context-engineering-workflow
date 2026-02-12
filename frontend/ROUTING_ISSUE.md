# Next.js Routing Issue - Root Page Not Showing

## Problem

The root route (`/`) is incorrectly loading the `/app` route component instead of the landing page. This is a known issue with Next.js standalone mode when there's both a root page and an app subdirectory.

## Current Status

- ✅ Root `app/page.tsx` exists and is correct
- ✅ LandingPage component exists and is correct  
- ❌ Build is incorrectly mapping root route to `/app/app/page.tsx`
- ❌ Browser shows AppPage instead of LandingPage at root URL

## Workaround Solutions

### Solution 1: Use Browser Navigation (Immediate Fix)

The landing page IS accessible, but you need to navigate correctly:

1. **Clear browser cache completely:**
   - Press `Ctrl+Shift+Delete`
   - Select "All time"
   - Clear cached images and files
   - Or use Incognito/Private window

2. **Access the landing page directly:**
   - The landing page should be at: `http://localhost:3003/`
   - If you see the app interface, try hard refresh: `Ctrl+F5`
   - Or open in a new incognito window

### Solution 2: Temporary Redirect Fix

Add a redirect in the root page to ensure correct routing:

```tsx
// frontend/app/page.tsx
'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import LandingPage from '@/components/LandingPage'

export default function Home() {
  const router = useRouter()
  
  useEffect(() => {
    // Force correct route on mount
    if (window.location.pathname !== '/') {
      router.replace('/')
    }
  }, [router])
  
  return <LandingPage />
}
```

### Solution 3: Restructure Routes (Long-term Fix)

Consider restructuring to avoid the conflict:

1. Move app route to a different path (e.g., `/dashboard` instead of `/app`)
2. Or move landing page to a different structure

## Root Cause

Next.js standalone mode is incorrectly resolving routes when both exist:
- `app/page.tsx` (root route `/`)
- `app/app/page.tsx` (app route `/app`)

The build is mapping the root route to the app route file.

## Verification

To verify which page is being served:

```powershell
# Check what HTML is being served
Invoke-WebRequest -Uri http://localhost:3003/ -UseBasicParsing | Select-Object -ExpandProperty Content | Select-String -Pattern "Context Engineering|Start Researching|Loading Research"
```

- "Context Engineering" or "Start Researching" = Landing Page ✅
- "Loading Research Assistant" = App Page ❌

## Next Steps

1. Try Solution 1 (clear cache + incognito)
2. If that doesn't work, implement Solution 2 (redirect fix)
3. Consider Solution 3 (restructure) for production
