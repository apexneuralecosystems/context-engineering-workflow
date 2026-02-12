#!/bin/bash
# Quick diagnostic script for backend 502 errors

echo "=== Backend Diagnostic Check ==="
echo ""

# Check if container exists
echo "1. Checking if container exists..."
if docker ps -a | grep -q context-engineering-backend; then
    echo "   ✓ Container exists"
    CONTAINER_EXISTS=true
else
    echo "   ✗ Container does not exist"
    CONTAINER_EXISTS=false
fi

# Check if container is running
echo ""
echo "2. Checking if container is running..."
if docker ps | grep -q context-engineering-backend; then
    echo "   ✓ Container is running"
    CONTAINER_RUNNING=true
else
    echo "   ✗ Container is NOT running"
    CONTAINER_RUNNING=false
    if [ "$CONTAINER_EXISTS" = true ]; then
        echo "   → Container exists but is stopped. Check logs: docker logs context-engineering-backend"
    fi
fi

# Check environment variables
echo ""
echo "3. Checking environment variables..."
if [ "$CONTAINER_RUNNING" = true ]; then
    API_PORT=$(docker exec context-engineering-backend sh -c 'echo $API_PORT' 2>/dev/null)
    FRONTEND_PORT=$(docker exec context-engineering-backend sh -c 'echo $FRONTEND_PORT' 2>/dev/null)
    OPENROUTER_KEY=$(docker exec context-engineering-backend sh -c 'echo $OPENROUTER_API_KEY' 2>/dev/null)
    
    if [ -n "$API_PORT" ]; then
        echo "   ✓ API_PORT: $API_PORT"
    else
        echo "   ✗ API_PORT: NOT SET (required)"
    fi
    
    if [ -n "$FRONTEND_PORT" ]; then
        echo "   ✓ FRONTEND_PORT: $FRONTEND_PORT"
    else
        echo "   ✗ FRONTEND_PORT: NOT SET (required)"
    fi
    
    if [ -n "$OPENROUTER_KEY" ]; then
        echo "   ✓ OPENROUTER_API_KEY: SET (${#OPENROUTER_KEY} chars)"
    else
        echo "   ✗ OPENROUTER_API_KEY: NOT SET (required)"
    fi
else
    echo "   → Skipping (container not running)"
fi

# Check health endpoint
echo ""
echo "4. Testing health endpoint..."
if [ "$CONTAINER_RUNNING" = true ] && [ -n "$API_PORT" ]; then
    HEALTH_RESPONSE=$(docker exec context-engineering-backend curl -s -o /dev/null -w "%{http_code}" http://localhost:${API_PORT}/health 2>/dev/null)
    if [ "$HEALTH_RESPONSE" = "200" ]; then
        echo "   ✓ Health endpoint responding (HTTP $HEALTH_RESPONSE)"
    else
        echo "   ✗ Health endpoint not responding (HTTP $HEALTH_RESPONSE)"
    fi
else
    echo "   → Skipping (container not running or API_PORT not set)"
fi

# Check recent logs for errors
echo ""
echo "5. Checking recent logs for errors..."
if [ "$CONTAINER_EXISTS" = true ]; then
    ERROR_COUNT=$(docker logs context-engineering-backend 2>&1 | tail -50 | grep -i "error\|exception\|traceback\|valueerror" | wc -l)
    if [ "$ERROR_COUNT" -gt 0 ]; then
        echo "   ⚠ Found $ERROR_COUNT potential errors in recent logs"
        echo "   → Run 'docker logs context-engineering-backend --tail 50' to see details"
    else
        echo "   ✓ No obvious errors in recent logs"
    fi
fi

# Summary
echo ""
echo "=== Summary ==="
if [ "$CONTAINER_RUNNING" = true ]; then
    echo "Container is running. If you're still getting 502 errors:"
    echo "  1. Check Nginx configuration matches API_PORT"
    echo "  2. Verify Nginx can reach the backend container"
    echo "  3. Check network connectivity"
else
    echo "Container is not running. Start it with:"
    echo "  docker start context-engineering-backend"
    echo "  or"
    echo "  docker-compose up -d"
fi
