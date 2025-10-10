# 🔧 ExternalApp Installation Guide

## ❌ Common Errors

### Error 1: Missing Dependencies
```
Node packages may not be installed. Try installing with 'npm install'.
Error: Could not find the '@angular-devkit/build-angular:dev-server' builder's node package.
```
**Cause**: npm dependencies haven't been installed yet.

### Error 2: Schema Validation Failed
```
Error: Schema validation failed with the following errors:
  Data path "" must have required property 'outputPath'.
```
**Cause**: Angular configuration issues or version conflicts.

## ✅ Solutions

### Quick Fix for Both Errors

Navigate to the ExternalApp WebUI directory and run the fix script:

```bash
cd /Users/siva/projects/UserManagement/ExternalApp/WebUI
chmod +x fix-angular.sh
./fix-angular.sh
```

### Alternative: Manual Fix

#### Step 1: Clean and Reinstall Dependencies

```bash
cd /Users/siva/projects/UserManagement/ExternalApp/WebUI/external-app

# Clean existing installation
rm -rf node_modules
rm -f package-lock.json

# Install dependencies
npm install
```

#### Step 2: If Still Having Issues

```bash
# Try with legacy peer deps flag
npm install --legacy-peer-deps

# Or install Angular CLI globally first
npm install -g @angular/cli@17
npm install
```

### Step 2: Verify Installation

After installation, you should see a `node_modules` directory:

```bash
ls -la
# Should show node_modules/ directory
```

### Step 3: Start the Application

```bash
npm start
```

## 🔄 Alternative: Quick Fix

If you want to quickly fix the issue:

```bash
# Navigate to the ExternalApp frontend directory
cd /Users/siva/projects/UserManagement/ExternalApp/WebUI/external-app

# Install Angular CLI globally (if not already installed)
npm install -g @angular/cli

# Install project dependencies
npm install

# Start the development server
npm start
```

## 🎯 Expected Result

After successful installation and startup, you should see:
```
** Angular Live Development Server is listening on localhost:4202 **
```

And you can access the ExternalApp at: http://localhost:4202

## 🐛 Troubleshooting

### Issue: `ng: command not found`
**Solution**: Install Angular CLI globally
```bash
npm install -g @angular/cli@latest
```

### Issue: Permission denied
**Solution**: Make scripts executable
```bash
chmod +x setup.sh
chmod +x start.sh
```

### Issue: Node version conflicts
**Solution**: Use Node.js version 18 or higher
```bash
node --version  # Should be v18+
```

### Issue: npm cache issues
**Solution**: Clear npm cache
```bash
npm cache clean --force
rm -rf node_modules
npm install
```

## 📋 Prerequisites

Before running ExternalApp, ensure you have:

1. **Node.js 18+** installed
2. **npm** installed  
3. **UserManagement system running**:
   - UserManagement WebUI: http://localhost:4201
   - UserManagement API: http://localhost:8001

## 🚀 Full Startup Sequence

1. **Start UserManagement** (if not already running):
   ```bash
   cd /Users/siva/projects/UserManagement/Api
   ./scripts/start.sh &
   
   cd /Users/siva/projects/UserManagement/WebUI/user-management-app  
   npm start &
   ```

2. **Install ExternalApp dependencies** (one-time setup):
   ```bash
   cd /Users/siva/projects/UserManagement/ExternalApp/WebUI
   ./setup.sh
   ```

3. **Start ExternalApp**:
   ```bash
   # Option 1: Full stack (recommended)
   cd /Users/siva/projects/UserManagement/ExternalApp
   ./start-all.sh
   
   # Option 2: Frontend only
   cd /Users/siva/projects/UserManagement/ExternalApp/WebUI/external-app
   npm start
   ```

4. **Test the integration**:
   - Visit: http://localhost:4202
   - Click "Login via User Management"
   - Complete authentication in UserManagement
   - Return to ExternalApp dashboard

## ✅ Success Indicators

You'll know everything is working when:
- ExternalApp loads at http://localhost:4202
- Login button redirects to UserManagement  
- After authentication, you return to ExternalApp dashboard
- User information is displayed correctly

## 📞 Still Having Issues?

If you continue to have problems:

1. **Check all ports are available**:
   - 4201 (UserManagement WebUI)
   - 4202 (ExternalApp WebUI)  
   - 8001 (UserManagement API)
   - 8002 (ExternalApp API)

2. **Verify UserManagement is working** first by visiting http://localhost:4201

3. **Check console logs** in browser developer tools for errors

4. **Review the startup output** for any error messages