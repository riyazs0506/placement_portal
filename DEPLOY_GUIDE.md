# 🚀 Placement Portal — Fix Guide + Free Hosting

---

## ❌ WHY "API endpoint not found: /api/campus-drive/drives/1/rounds"

**Root cause:** Your server was running the **old code** from memory.
The route `/api/campus-drive/drives/1/rounds` is **correct** — but the server 
had the old code (which used `/api/campus-drive/api/1/rounds`) still in memory.

**Every time you replace a Python file, you MUST restart the server.**

---

## ✅ FIX — Do This Right Now (3 steps)

### Step 1: Replace the files
Copy these files into your project:
```
campus_drive.py  → placement_portal/routes/campus_drive.py
drive_detail.html → placement_portal/templates/campus_drive/drive_detail.html
drive_list.html  → placement_portal/templates/campus_drive/drive_list.html
notifications.html → placement_portal/templates/community/notifications.html
```

### Step 2: Stop the old server
In your terminal, press **Ctrl + C** to stop the running server.

### Step 3: Use the start script (clears cache automatically)
```bash
# On Mac/Linux:
chmod +x start.sh
./start.sh

# On Windows:
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**OR** manually clear cache then start:
```bash
# Clear Python cache first (IMPORTANT)
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} +

# Then start
uvicorn main:app --reload --port 8000
```

### ✅ After restart, test it:
1. Go to http://127.0.0.1:8000/campus-drives/1
2. Make sure Response is **Closed** (Summary panel shows "Closed")
3. Click **Add Round** → fill the form → click **Add Round** button
4. Round should appear ✅

---

## 🌐 FREE HOSTING OPTIONS

### Option 1: Render.com (Recommended — Easiest)
**Free tier:** 750 hours/month (enough for always-on)

1. Create account at https://render.com
2. Connect your GitHub account
3. Push project to GitHub:
   ```bash
   git init
   git add .
   git commit -m "Placement Portal v2"
   git remote add origin https://github.com/YOUR_USERNAME/placement-portal.git
   git push -u origin main
   ```
4. On Render dashboard → **New Web Service** → Connect repo
5. Settings:
   - **Build command:** `pip install -r requirements.txt`
   - **Start command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Environment:** Python 3
6. Add environment variables (Render dashboard → Environment):
   ```
   SECRET_KEY          = any_random_string_here
   STAFF_SECRET_KEY    = STAFF@2024
   OFFICER_SECRET_KEY  = OFFICER@2024
   ADMIN_SECRET_KEY    = ADMIN@SUPER2024
   COMPANY_SECRET_KEY  = COMPANY@2024
   ```
7. Click **Deploy** — live in ~3 minutes at `https://placement-portal.onrender.com`

---

### Option 2: Railway.app (Also free, very fast)
**Free tier:** $5 free credits/month

1. Go to https://railway.app
2. Click **Deploy from GitHub**
3. Connect repo → Select project
4. Add environment variables (same as above)
5. Railway auto-detects Python and uses the `Procfile`
6. Done — live in ~2 minutes

---

### Option 3: PythonAnywhere (Free forever, beginner-friendly)
**Free tier:** Always free (limited CPU)

1. Create account at https://www.pythonanywhere.com
2. Go to **Files** tab → Upload all project files
3. Go to **Bash console**:
   ```bash
   pip install -r requirements.txt --user
   ```
4. Go to **Web** tab → **Add new web app**
5. Select **Manual configuration** → Python 3.10
6. Set WSGI file path → edit the WSGI file:
   ```python
   import sys
   sys.path.insert(0, '/home/YOUR_USERNAME/placement_portal')
   from main import app as application
   ```
7. Click **Reload** → Live at `YOUR_USERNAME.pythonanywhere.com`

---

### Option 4: Fly.io (Best performance on free tier)
**Free tier:** 3 shared VMs free

```bash
# Install flyctl
curl -L https://fly.io/install.sh | sh

# Login
fly auth login

# Deploy
fly launch
fly deploy
```

---

## 📝 DATABASE NOTE FOR HOSTING

The default SQLite database (`placement_portal.db`) resets every time the 
server restarts on free hosting. To persist data, use a free PostgreSQL:

### Free PostgreSQL options:
- **Render** → New → PostgreSQL (free tier, 1GB)
- **Supabase** → https://supabase.com (2 free projects)
- **ElephantSQL** → https://elephantsql.com (tiny turtle — free)
- **Neon.tech** → https://neon.tech (free PostgreSQL)

### How to connect (change DATABASE_URL):
```bash
# In environment variables on your hosting platform:
DATABASE_URL=postgresql://user:password@host:5432/dbname
```

The app uses SQLAlchemy so it works with PostgreSQL without any code changes.

---

## 🔑 Login Credentials (after seeding)
| Role | Email | Password |
|------|-------|----------|
| Head Admin | admin@college.edu | Admin@123 |
| Placement Officer | officer@college.edu | Officer@123 |
| Staff | staff1@college.edu | Staff@123 |
| TCS HR | hr@tcs.com | TCS@123 |
| Student | arun@student.edu | Student@123 |

---

## 📂 Project Structure
```
placement_portal/
├── main.py                 ← FastAPI app entry
├── models.py               ← All database models
├── database.py             ← DB connection
├── auth.py                 ← JWT + secret keys
├── requirements.txt        ← Dependencies
├── start.sh                ← One-click start (Mac/Linux)
├── render.yaml             ← Render.com config
├── Procfile                ← Railway/Heroku config
├── routes/
│   ├── campus_drive.py     ← FIXED ✅
│   ├── exam.py
│   ├── users.py
│   ├── questions.py
│   ├── dashboard.py
│   └── compiler.py
├── templates/
│   ├── campus_drive/
│   │   ├── drive_detail.html  ← FIXED ✅
│   │   └── drive_list.html    ← FIXED ✅
│   └── community/
│       └── notifications.html ← FIXED ✅
└── static/js/app.js
```

---

## ❓ Common Issues

| Error | Fix |
|-------|-----|
| "API endpoint not found" | **Restart the server** after replacing files |
| "Table not found" | Run `python seed_data.py --create-tables` |
| "Invalid or expired token" | Clear localStorage in browser (F12 → Application → Clear) |
| Port 8000 already in use | `kill $(lsof -t -i:8000)` or change port to 8001 |
| "Response is closed" error on rounds | This is correct behavior — rounds can only be added when Response=Closed |
