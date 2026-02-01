# Face Recognition App - Deployment Guide

## Overview
- **Frontend**: Netlify (free, no card)
- **Backend**: Railway.app (free, no card)

---

## Step 1: Push to GitHub

```bash
git add .
git commit -m "Add deployment config"
git push origin main
```

---

## Step 2: Deploy Backend to Railway.app

1. Go to [railway.app](https://railway.app) → Sign up with GitHub

2. Click **New Project** → **Deploy from GitHub repo**

3. Select your `Live-Face-Recognition` repository

4. Railway auto-detects Python. Click **Add Variables**:
   - `JWT_SECRET` = `facerecognition2024secretkey`

5. Go to **Settings** → **Generate Domain** (to get public URL)

6. Copy your URL (e.g., `https://live-face-recognition.up.railway.app`)

---

## Step 3: Deploy Frontend to Netlify

1. Go to [netlify.com](https://netlify.com) → Sign up with GitHub

2. Click **Add new site** → **Import an existing project**

3. Configure:
   - **Base directory**: `frontend`
   - **Build command**: `npm run build`
   - **Publish directory**: `frontend/dist`

4. Add environment variable:
   - `VITE_API_URL` = `https://your-railway-url.up.railway.app/api`

5. Deploy!

---

## Done! 🎉

Test your app at your Netlify URL.
