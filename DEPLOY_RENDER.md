# How to Deploy on Render — Step by Step

---

## STEP 1 — Push to GitHub

Open your terminal (Command Prompt / Git Bash):

```bash
cd placement_portal        # go into your project folder
git init                   # only needed first time
git add .
git commit -m "v2.2 deploy"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/placement-portal.git
git push -u origin main
```

If you already pushed before, just run:
```bash
git add .
git commit -m "fix deploy"
git push
```

---

## STEP 2 — Create Web Service on Render

1. Go to **https://render.com** and sign in
2. Click **"New +"** (top right)
3. Click **"Web Service"**
4. Click **"Connect a repository"**
5. Select your **placement-portal** GitHub repo
6. Click **"Connect"**

---

## STEP 3 — Configure the Service

Fill in these fields exactly:

| Field | Value |
|---|---|
| **Name** | placement-portal |
| **Region** | Singapore (closest to India) |
| **Branch** | main |
| **Runtime** | **Docker** ← very important |
| **Dockerfile Path** | ./Dockerfile |
| **Instance Type** | Free |

> ⚠️ Make sure **Runtime = Docker** — NOT Python. This is why your deploy was failing before. Python runtime ignores `runtime.txt` and defaults to Python 3.14 which breaks pydantic.

Click **"Create Web Service"**

---

## STEP 4 — Set Environment Variables

After creating the service, go to:
**Dashboard → placement-portal → Environment → Add Environment Variable**

Add these one by one (copy from your `.env` file):

```
DATABASE_URL      = mysql+pymysql://avnadmin:AVNS_...@placementportal...aiven.com:17148/defaultdb
REDIS_URL         = redis://default:z0MEMM...@redis-17296...redislabs.com:17296
SECRET_KEY        = placementportal_secret_key_2026
ALGORITHM         = HS256
ACCESS_TOKEN_EXPIRE_MINUTES = 1440
STAFF_SECRET_KEY  = STAFF@2024
OFFICER_SECRET_KEY = OFFICER@2024
ADMIN_SECRET_KEY  = ADMIN@SUPER2024
COMPANY_SECRET_KEY = COMPANY@2024
APP_ENV           = production
LOG_LEVEL         = INFO
```

Click **"Save Changes"**

---

## STEP 5 — Wait for Deploy

Render will now build using Docker. The build log should show:

```
==> Building with Dockerfile
Step 1/6: FROM python:3.11.9-slim      ← ✅ CORRECT Python version
Step 2/6: RUN apt-get install...
Step 3/6: COPY requirements.txt
Step 4/6: RUN pip install...           ← No Rust, no compilation errors
Step 5/6: COPY . .
Step 6/6: CMD uvicorn main:app...
==> Build successful 🎉
==> Your service is live at https://placement-portal-xxxx.onrender.com
```

Total build time: ~3–5 minutes.

---

## STEP 6 — Test Your App

Open your Render URL, e.g.:  
`https://placementportal-rdv7.onrender.com`

Test these:
- `/register` — Student registration (should work, no 500 error)
- `/login` — Login
- `/dashboard` — Dashboard
- `/campus-drives` — Campus drives
- `/exams` — Exams

---

## If Deploy Still Fails

### Error: "pydantic-core" / Rust / metadata-generation-failed
→ Make sure `render.yaml` has `env: docker` not `env: python`

### Error: "Cannot connect to database"  
→ Check `DATABASE_URL` in Environment tab — copy it exactly from Aiven

### Error: "Module not found"
→ Run `git add . && git commit -m "fix" && git push` — make sure all files are pushed

### Error: Port already in use / health check failed
→ The `Dockerfile` uses `${PORT:-8000}` which reads the port Render assigns automatically

---

## Redeploying After Changes

Every time you change code:
```bash
git add .
git commit -m "your change description"
git push
```
Render auto-detects the push and rebuilds automatically.

---

## Free Tier Limitations on Render

- App **sleeps after 15 minutes** of no traffic
- First request after sleep takes ~30 seconds (cold start)
- To keep it awake: use UptimeRobot (free) to ping your URL every 10 minutes
  - Go to **uptimerobot.com** → New Monitor → HTTP → paste your Render URL → every 10 mins
