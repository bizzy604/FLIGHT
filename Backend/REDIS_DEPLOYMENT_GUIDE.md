# Redis Deployment Guide for Flight Backend

## Current Status
The backend has been updated to handle Redis unavailability gracefully. The application will:
- ✅ Start successfully even without Redis
- ✅ Log warnings when Redis operations are attempted without connection
- ✅ Return appropriate responses indicating cache unavailability
- ✅ Continue to function for flight search, pricing, and booking operations

## Deployment Options

### Option 1: Deploy Without Redis (Immediate Solution)
The application will work without Redis, but without caching benefits:
- Flight search data won't be cached between requests
- Users will need to re-search flights for pricing/booking
- No session persistence across requests

**To deploy immediately:**
1. The current code changes allow deployment without Redis
2. Simply deploy with the updated requirements.txt and Redis fallback logic

### Option 2: Use Redis Cloud (Recommended for Production)
1. **Sign up for Redis Cloud** (free tier available):
   - Go to https://redis.com/try-free/
   - Create a free account
   - Create a new database

2. **Get connection details:**
   - Redis endpoint (host:port)
   - Password
   - Or Redis URL format: `redis://username:password@host:port/db`

3. **Update Render environment variables:**
   ```yaml
   envVars:
     - key: REDIS_URL
       value: redis://default:your-password@your-host:port/0
   ```

### Option 3: Use Render Redis Add-on
1. **Add Redis service to render.yaml:**
   ```yaml
   services:
     - type: redis
       name: flight-redis
       plan: starter  # Free tier
       
     - type: web
       name: flight-backend
       # ... existing config
       envVars:
         - key: REDIS_URL
           fromService:
             type: redis
             name: flight-redis
             property: connectionString
   ```

### Option 4: Use Upstash Redis (Serverless)
1. **Sign up at https://upstash.com/**
2. **Create a Redis database**
3. **Get the Redis URL**
4. **Add to Render environment variables**

## Environment Variables

The application supports these Redis configuration options:

```bash
# Individual connection parameters
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=your-password

# Or single URL (takes precedence)
REDIS_URL=redis://username:password@host:port/db
```

## Testing Redis Connection

After deployment, check the logs for:
- ✅ `Redis connection established successfully` - Redis is working
- ⚠️ `Redis connection failed: ... Running without Redis cache` - No Redis, but app works

## Benefits of Using Redis

With Redis enabled, the application provides:
- **Session persistence**: Flight search results cached for 30 minutes
- **Better performance**: Reduced API calls to flight providers
- **Improved UX**: Users can navigate between search → pricing → booking seamlessly
- **Data compression**: Efficient storage of large flight response data

## Next Steps

1. **Immediate**: Deploy with current changes (works without Redis)
2. **Short-term**: Set up Redis Cloud or Upstash for caching benefits
3. **Long-term**: Consider Redis clustering for high availability

## Troubleshooting

If deployment still fails:
1. Check that `redis>=4.5.0` is in requirements.txt
2. Verify the Redis connection logic handles exceptions
3. Check Render logs for specific error messages
4. Ensure environment variables are properly set
