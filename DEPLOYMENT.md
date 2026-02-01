# Face Recognition App - Deployment Guide

## Overview
- **Frontend**: Netlify (free tier)
- **Backend**: Render.com (free tier)

---

## Step 1: Push to GitHub

```bash
git add .
git commit -m "Add deployment configuration"
git push origin main
```

---

## Step 2: Deploy Backend to Render.com

1. Go to [render.com](https://render.com) → Sign up with GitHub

2. Click **New +** → **Web Service** → Connect your repo

3. Configure:
   | Setting | Value |
   |---------|-------|
   | Name | `face-recognition-api` |
   | Branch | `main` |
   | Build Command | `pip install -r requirements.txt` |
   | Start Command | `gunicorn api:app --bind 0.0.0.0:$PORT --workers 1 --timeout 120` |

4. Add Environment Variable:
   - `JWT_SECRET` = `your-random-secret-key`

5. Click **Create Web Service** → Wait for deploy

6. **Copy your URL** (e.g., `https://face-recognition-api.onrender.com`)

---

## Step 3: Deploy Frontend to Netlify

1. Go to [netlify.com](https://netlify.com) → Sign up with GitHub

2. Click **Add new site** → **Import an existing project**

3. Select your GitHub repo

4. Configure:
   | Setting | Value |
   |---------|-------|
   | Base directory | `frontend` |
   | Build command | `npm run build` |
   | Publish directory | `frontend/dist` |

5. Click **Site configuration** → **Environment variables** → Add:
   - `VITE_API_URL` = `https://your-render-url.onrender.com/api`

6. Click **Deploy site**

---

## Step 4: Test Your Deployment

1. Open your Netlify URL
2. Register a new account
3. Enroll a face
4. Verify the face

---

## Notes

⚠️ **Free Tier Limitations:**
- Backend takes 30-60 seconds to wake up after inactivity
- SQLite data may be lost on redeploy (use PostgreSQL for production)
