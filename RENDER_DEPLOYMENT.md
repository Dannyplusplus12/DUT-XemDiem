# Render Deployment Guide

## 🚀 Deploy to Render.com

### Step 1: Connect Your GitHub Repository

1. Go to [render.com](https://render.com)
2. Sign in with GitHub
3. Click **New +** → **Web Service**
4. Select repository: `https://github.com/Dannyplusplus12/DUT-XemDiem.git`
5. Click **Connect**

### Step 2: Configure Service

**Basic Settings:**
- **Name:** `dut-exam-portal`
- **Environment:** `Python 3.11`
- **Build Command:** `cd backend && pip install -r requirements.txt && pip install gunicorn`
- **Start Command:** `cd backend && gunicorn -w 4 -b 0.0.0.0:$PORT app.main:app`
- **Instance Type:** Free or Starter (depending on traffic)

### Step 3: Environment Variables

Click **Environment** and add:

| Key | Value |
|-----|-------|
| `DATABASE_URL` | `sqlite:///./backend/contest.db` |
| `FLASK_ENV` | `production` |
| `FLASK_APP` | `app.main:app` |
| `PYTHONUNBUFFERED` | `1` |

### Step 4: Deploy

1. Click **Deploy**
2. Wait for build to complete (5-10 minutes)
3. Your URL: `https://dut-exam-portal.onrender.com`

## ✅ Verify Deployment

After deployment, test:

```bash
# Check health
curl https://dut-exam-portal.onrender.com/health

# Get contests
curl https://dut-exam-portal.onrender.com/contests
```

## 🗄️ Upgrade to PostgreSQL (Optional)

For production data storage:

### 1. Create PostgreSQL Database on Render

1. Go to Render Dashboard
2. Click **New +** → **PostgreSQL**
3. Configure:
   - **Name:** `dut-exam-portal-db`
   - **Database:** `exam_results`
   - **User:** `admin`
4. Copy **Internal Database URL**

### 2. Update Environment Variable

In your web service, set:
```
DATABASE_URL=your-postgresql-url-from-render
```

Example:
```
postgresql://admin:password@dpg-xxxxx.render.internal:5432/exam_results
```

### 3. Update requirements.txt

Already includes `psycopg2-binary` for PostgreSQL support.

### 4. Redeploy

Push a new commit or manually trigger redeploy from Render dashboard.

## 📁 Persistent Storage (SQLite Limitation)

**⚠️ Important:** Render's free tier doesn't support persistent file storage. SQLite databases reset on redeploy.

**Solutions:**
1. **Use PostgreSQL** (Recommended for production)
2. **Use Render Disk** (Paid, persistent storage)
3. **Use AWS S3** for database backups

## 🔄 Auto-Deploy on Git Push

Render automatically redeploys when you push to `main` branch:

```bash
git add .
git commit -m "Update feature"
git push origin main
# Render will automatically build and deploy
```

## 🛠️ Troubleshooting

### Build fails
- Check build logs in Render dashboard
- Ensure `render.yaml` is in root directory
- Verify `requirements.txt` has all dependencies

### Database not found
- First deploy creates database
- If redeployed, use PostgreSQL for persistence

### Port issues
- Always use `$PORT` environment variable (Render sets this)
- Don't hardcode port 8000

### Application errors
- View live logs in Render dashboard
- Check error messages in deployment logs

## 📊 Monitoring

Render provides:
- **Metrics:** CPU, memory, disk usage
- **Logs:** Real-time application logs
- **Analytics:** Request volume and response times

Access from dashboard: **Logs** tab

## 💰 Pricing

**Render Free Tier:**
- 750 free hours/month per web service
- PostgreSQL: 90 days free, then paid

**Paid Plans:**
- Starter: $7/month (always on)
- Standard: $12/month
- Premium: Custom pricing

---

**Quick Links:**
- Render Dashboard: https://dashboard.render.com
- Deployed App: https://dut-exam-portal.onrender.com (after deployment)
- GitHub Repo: https://github.com/Dannyplusplus12/DUT-XemDiem
