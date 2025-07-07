# Token Persistence Guide

## 🔄 **Problem Solved: Token Persistence Across Server Restarts**

### **Previous Behavior (Memory-Only Storage)**
```
Server Start → No token → Generate new token → Use for 11 hours
Server Restart → Token lost → Generate new token → Waste previous token
```

### **New Behavior (Persistent Storage)**
```
Server Start → Check disk → Load valid token OR generate new one → Use for full 11 hours
Server Restart → Load same token from disk → Continue using → No waste!
```

## 🏗️ **How Token Persistence Works**

### **Storage Location**
- **Path**: `{temp_directory}/flight_app_tokens/verteil_token.json`
- **Permissions**: `0o600` (readable only by file owner)
- **Format**: JSON with token data and expiry information

### **Token Lifecycle with Persistence**

1. **First Token Generation**
   ```
   API Call → No token in memory → Check disk → No file → Generate new token → Save to disk + memory
   ```

2. **Subsequent API Calls (Same Session)**
   ```
   API Call → Token in memory → Use cached token
   ```

3. **Server Restart**
   ```
   Server Start → No token in memory → Check disk → Load valid token → Use loaded token
   ```

4. **Token Expiry**
   ```
   API Call → Check token validity → Expired → Delete file → Generate new token → Save to disk
   ```

## 📁 **Token File Structure**

```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9...",
  "token_data": {
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9...",
    "token_type": "Bearer",
    "expires_in": 43199
  },
  "token_expiry": 1704123456,
  "saved_at": 1704080256
}
```

## 🔧 **Configuration Options**

### **Enable/Disable Persistence**
```bash
# Disable token persistence (fallback to memory-only)
export DISABLE_TOKEN_PERSISTENCE=true

# Enable token persistence (default)
export DISABLE_TOKEN_PERSISTENCE=false
```

### **Custom Token File Location**
The system automatically uses a secure temporary directory, but you can customize it by modifying the `_get_token_file_path()` method.

## 🛡️ **Security Features**

### **File Permissions**
- Token files are created with `0o600` permissions (owner read/write only)
- Token directory is created with `0o700` permissions (owner access only)

### **Automatic Cleanup**
- Expired tokens are automatically deleted from disk
- Token files are removed when `clear_token()` is called
- Invalid token files are cleaned up on load

### **Error Handling**
- If disk operations fail, system falls back to memory-only storage
- No crashes or service interruptions due to persistence issues

## 📊 **Benefits**

### **Performance Improvements**
- ✅ **Reduced API calls**: No unnecessary token generation on restart
- ✅ **Faster startup**: Skip token generation if valid token exists
- ✅ **Better resource usage**: Full utilization of 11-hour token lifetime

### **Reliability Improvements**
- ✅ **Graceful restarts**: Maintain authentication across deployments
- ✅ **Development efficiency**: No re-authentication during development restarts
- ✅ **Production stability**: Consistent authentication state

## 🧪 **Testing Token Persistence**

### **Run Persistence Tests**
```bash
cd Backend
python test_token_persistence.py
```

### **Manual Testing Steps**

1. **Start server and make API call**
   ```bash
   # Start server
   python app.py

   # Make API call (generates token)
   curl http://localhost:5000/api/debug/token
   ```

2. **Check token file exists**
   ```bash
   # Find token file location
   ls /tmp/flight_app_tokens/
   
   # View token file (be careful with sensitive data)
   cat /tmp/flight_app_tokens/verteil_token.json
   ```

3. **Restart server**
   ```bash
   # Stop server (Ctrl+C)
   # Start server again
   python app.py
   ```

4. **Verify token loaded from disk**
   ```bash
   # Check debug endpoint - should show same token
   curl http://localhost:5000/api/debug/token
   ```

## 🔍 **Monitoring Token Persistence**

### **Log Messages to Watch**
```
INFO:utils.auth:Token persistence enabled. File: /tmp/flight_app_tokens/verteil_token.json
INFO:utils.auth:Loaded valid token from disk. Expires in 39540 seconds (11.0 hours)
INFO:utils.auth:Successfully obtained new token. Expires in 43199 seconds (12.0 hours).
```

### **Debug Endpoint**
```bash
curl http://localhost:5000/api/debug/token
```

**Response includes persistence info:**
```json
{
  "status": "success",
  "token_available": true,
  "token_info": {
    "has_token": true,
    "is_valid": true,
    "expires_in": 39540,
    "expiry_time": 1704123456
  }
}
```

## 🚨 **Troubleshooting**

### **Token Not Persisting**
1. Check file permissions on temp directory
2. Verify `DISABLE_TOKEN_PERSISTENCE` is not set to `true`
3. Check logs for persistence errors

### **Token File Corruption**
- System automatically detects and cleans up invalid files
- Falls back to generating new token

### **Security Concerns**
- Token files are stored in secure temp directory with restricted permissions
- Files are automatically cleaned up on token expiry or clear

## 🎯 **Expected Behavior After Implementation**

### **Development**
- ✅ Server restarts during development don't require new token generation
- ✅ Faster development cycle with persistent authentication

### **Production**
- ✅ Deployment restarts maintain authentication state
- ✅ Rolling updates don't waste tokens
- ✅ Better resource utilization and API rate limiting compliance

### **Monitoring**
- ✅ Token generation metrics show actual usage (not restart artifacts)
- ✅ Clear visibility into token lifecycle and reuse patterns
