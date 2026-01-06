# Ngrok Setup - TikTok Dashboard

## ✅ Ngrok Successfully Installed!

Ngrok is now installed and configured in your project directory.

---

## 🚀 Quick Start

### Recommended: Simple Setup (One Tunnel)
```bash
# Double-click this file:
start-ngrok-simple.bat
```

This starts:
1. Backend API (port 5000)
2. Frontend with API proxy (port 3000)
3. ONE ngrok tunnel for the frontend

**How it works:** The frontend proxies all API requests to the backend through Vite's dev server. This means you only need ONE public URL!

---

## 🌐 Current Setup

### Public URL
**https://micah-silverlike-unsatiably.ngrok-free.dev**

### Local URLs
- Frontend: http://localhost:3000
- Backend: http://localhost:5000

### How Requests Flow
```
Public User
    ↓
https://your-domain.ngrok-free.dev (ngrok tunnel)
    ↓
http://localhost:3000 (Vite dev server with proxy)
    ↓ (API requests: /api/*, /videos, /sentiment, etc.)
http://localhost:5000 (Flask backend)
```

---

## 📝 No Password Required!

Unlike localtunnel, ngrok **does NOT require passwords**.

You may see a warning page on first visit:
- **Message:** "You are about to visit [domain]. This site is served for free..."
- **Action:** Just click **"Visit Site"** button
- This is ngrok's free tier notice, NOT a password prompt

---

## 🎯 Advantages Over Localtunnel

| Feature | Ngrok | Localtunnel |
|---------|-------|-------------|
| Password | ❌ No | ✅ Yes (annoying) |
| Stability | ✅ Excellent | ⚠️ Fair |
| Speed | ✅ Fast | ⚠️ Slower |
| Session Duration | ✅ Stable | ⚠️ Drops often |
| Custom Subdomains | ✅ Yes (paid) | ✅ Yes (free) |

---

## 📁 Available Scripts

### Main Scripts

1. **start-ngrok-simple.bat** ⭐ RECOMMENDED
   - Single ngrok tunnel
   - Frontend proxies to backend
   - Easiest setup

2. **start-with-ngrok.bat** (OLD - requires paid plan)
   - Tries to run two separate tunnels
   - Needs ngrok paid account for multiple tunnels

3. **stop-all-services.bat**
   - Stops all Python and Node processes
   - Use this to clean up

---

## ⚙️ Configuration Files

### ngrok.yml
Location: `C:\Users\Dataverse\AppData\Local\ngrok\ngrok.yml`

```yaml
version: "2"
authtoken: 34iZixcIHFQLPD21B4bPF9EwL4u_2RtiaxGQzfunAFymMSm75

tunnels:
  frontend:
    proto: http
    addr: 3000
  backend:
    proto: http
    addr: 5000
```

### vite.config.js
The frontend is configured to proxy API requests:

```javascript
server: {
  port: 3000,
  proxy: {
    '/api': {
      target: 'http://localhost:5000',
      changeOrigin: true,
    },
    '/videos': {
      target: 'http://localhost:5000',
      changeOrigin: true,
    },
    // ... etc
  }
}
```

### frontend/.env
```bash
# Empty means use Vite proxy (recommended)
VITE_API_URL=
```

---

## 🔧 Manual Commands

### Start Services Manually

```bash
# 1. Start backend
cd backend
python run_api.py

# 2. Start frontend (in new terminal)
cd frontend
npm run dev

# 3. Start ngrok (in new terminal)
ngrok http 3000
```

### View Ngrok Dashboard
Open in browser: http://localhost:4040

This shows:
- All active tunnels
- Request/response logs
- Traffic statistics

### Get Public URL Programmatically
```bash
curl http://localhost:4040/api/tunnels
```

---

## 🎓 Ngrok Free vs Paid

### Free Tier (Current)
✅ Random URLs (e.g., `https://xxxx-xxxx.ngrok-free.dev`)
✅ HTTPS support
✅ Unlimited bandwidth
✅ Basic inspection
⚠️ URLs change on restart
⚠️ Warning page for visitors
⚠️ Limited to 1 agent (2 tunnels max simultaneously)

### Paid Tier ($8-10/month)
✅ Custom subdomains (`https://my-dashboard.ngrok.io`)
✅ No warning page
✅ Reserved domains (URLs don't change)
✅ Multiple agents
✅ IP whitelisting
✅ Password protection

### Upgrade
Visit: https://dashboard.ngrok.com/billing/plan

---

## 🐛 Troubleshooting

### "ERR_NGROK_334: Endpoint already online"
**Problem:** Trying to run multiple tunnels with same URL
**Solution:**
```bash
# Stop all ngrok processes
taskkill /F /IM ngrok.exe

# Use the simple setup
start-ngrok-simple.bat
```

### "Can't connect to backend"
**Problem:** Frontend can't reach backend
**Solution:**
1. Check backend is running: http://localhost:5000/health
2. Verify frontend proxy config in `vite.config.js`
3. Check `.env` file is empty or not set

### "Connection reset" or "Tunnel closed"
**Problem:** Ngrok session expired (rare on free tier)
**Solution:** Restart ngrok tunnel

### "Port 3000 already in use"
**Solution:**
```bash
# Windows
netstat -ano | findstr :3000
taskkill /PID <pid> /F

# Then restart
```

---

## 📚 Additional Resources

- Ngrok Docs: https://ngrok.com/docs
- Ngrok Dashboard: https://dashboard.ngrok.com
- Vite Proxy Docs: https://vitejs.dev/config/server-options.html#server-proxy

---

## ✨ Tips

1. **Bookmark your ngrok URL** while it's running
2. **Share only the public URL** - don't expose localhost
3. **Monitor requests** at http://localhost:4040
4. **Restart ngrok** if you get a new URL (happens on restart)
5. **Use HTTPS** - ngrok provides free SSL

---

Last Updated: 2025-12-29
