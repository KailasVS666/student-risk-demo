# 🔧 File Path Updates Required

Since we organized the static assets, you'll need to update references in your templates to use the new paths.

## Changes Made

### Static Folder Structure
```
app/static/
├── css/
│   └── style.css        # Moved from app/static/style.css
├── js/
│   └── script.js        # Moved from app/static/script.js
└── images/              # NEW: Ready for your images
```

## Files That Need Updates

### 1. `app/templates/index.html`
**Current (Line 7):**
```html
<link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
```

**Update to:**
```html
<link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
```

**Current (Line 344):**
```html
<script src="{{ url_for('static', filename='script.js') }}"></script>
```

**Update to:**
```html
<script src="{{ url_for('static', filename='js/script.js') }}"></script>
```

---

### 2. `app/templates/assessment.html`
**Current (Line 260):**
```html
<script src="{{ url_for('static', filename='script.js') }}"></script>
```

**Update to:**
```html
<script src="{{ url_for('static', filename='js/script.js') }}"></script>
```

---

### 3. Check Other Templates
Search all template files for:
- `filename='style.css'` → replace with `filename='css/style.css'`
- `filename='script.js'` → replace with `filename='js/script.js'`

---

## Optional: Remove Old Files

After confirming everything works, you can delete the original files:

```powershell
# PowerShell commands
Remove-Item "student-risk-app\app\static\style.css"
Remove-Item "student-risk-app\app\static\script.js"
```

---

## Adding Images

Place your images in `app/static/images/`:
- `logo.svg` or `logo.png` - Your app logo
- `hero-bg.svg` - Landing page hero background
- `demo-screenshot.png` - Demo screenshot for landing page

**Reference in templates:**
```html
<img src="{{ url_for('static', filename='images/logo.png') }}" alt="Logo">
```

---

## Testing

After making these changes:

1. Restart your Flask server
2. Visit each page:
   - http://127.0.0.1:8501/landing
   - http://127.0.0.1:8501/login
   - http://127.0.0.1:8501/dashboard (after login)
   - http://127.0.0.1:8501/assessment
   - http://127.0.0.1:8501/history
   - http://127.0.0.1:8501/settings
   - http://127.0.0.1:8501/about

3. Check browser console for errors
4. Verify styles are loading correctly
5. Test all JavaScript functionality

---

## Quick Fix Script

Run this PowerShell script to update all template files automatically:

```powershell
# Navigate to templates directory
cd student-risk-app\app\templates

# Replace style.css references
Get-ChildItem -Recurse -Filter *.html | ForEach-Object {
    (Get-Content $_.FullName) -replace "filename='style.css'", "filename='css/style.css'" | Set-Content $_.FullName
}

# Replace script.js references
Get-ChildItem -Recurse -Filter *.html | ForEach-Object {
    (Get-Content $_.FullName) -replace "filename='script.js'", "filename='js/script.js'" | Set-Content $_.FullName
}

Write-Host "✅ All template files updated!" -ForegroundColor Green
```

---

**Status**: 📝 Manual updates required for static file paths  
**Priority**: Medium (pages will load but styles/scripts may not work until updated)  
**Time**: ~5 minutes
