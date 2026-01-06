# TikTok Dashboard - Public Tunnel Access

## 🚀 Quick Start Scripts

### Start All Services
- **Windows (Batch)**: Double-click `start-public-dashboard.bat`
- **Windows (PowerShell)**: Right-click `start-public-dashboard.ps1` → Run with PowerShell

### Stop All Services
- **Windows**: Double-click `stop-all-services.bat`

---

## 🌐 Current Public URLs

### Frontend Dashboard
- **URL**: https://free-bees-rule.loca.lt
- **Local**: http://localhost:3000

### Backend API
- **URL**: https://brown-socks-joke.loca.lt
- **Local**: http://localhost:5000

---

## 🔐 About Tunnel Passwords

### What is the tunnel password?
Localtunnel requires a password for security. The password is **generated when you first visit the URL** and is typically one of:
- Your IP address
- A random code shown in the browser
- Sometimes no password (just click "Continue")

### How to find the password:
1. **Visit the URL** in your browser
2. The password will be **displayed on the screen** or in the localtunnel window
3. **Look for**: "your tunnel password is: xxxxx" in the PowerShell/CMD window
4. If not shown, try **your current IP address** as the password

### Getting your IP address:
```bash
curl ifconfig.me
```
Or visit: https://ifconfig.me

---

## 📝 Important Notes

### First-Time Setup
1. Run `start-public-dashboard.bat` or `start-public-dashboard.ps1`
2. Wait for all 4 windows to open:
   - Backend API
   - Frontend Dev Server
   - Backend Tunnel
   - Frontend Tunnel
3. Check each tunnel window for the password message
4. Visit the Frontend URL and enter the password when prompted

### Password Management
- **Password changes** every time you restart the tunnel
- **Same password** for both frontend and backend from the same IP
- **Save the password** if sharing the link with others from the same network

### URL Management
- **URLs change** every time you restart (unless you use custom subdomain)
- Update `frontend/.env` with new backend URL if it changes
- Current backend URL in .env: `https://brown-socks-joke.loca.lt`

---

## 🛠️ Manual Commands

### Start Backend
```bash
cd backend
python run_api.py
```

### Start Frontend
```bash
cd frontend
npm run dev
```

### Create Tunnels
```bash
# Frontend tunnel (port 3000)
npx localtunnel --port 3000

# Backend tunnel (port 5000)
npx localtunnel --port 5000
```

---

## 🔧 Troubleshooting

### "Can't connect to backend"
1. Make sure both tunnels are running
2. Check `frontend/.env` has correct backend URL
3. Restart frontend after changing .env

### "Invalid tunnel password"
1. Check the tunnel window for the actual password
2. Try your IP address: `curl ifconfig.me`
3. Clear browser cookies and try again
4. Restart the tunnel to get a new password

### "Tunnel keeps disconnecting"
- Localtunnel is free and can be unstable
- Restart using the scripts
- Consider alternatives: ngrok, cloudflared, serveo

---

## 📚 Alternative: Custom Subdomain (No Password)

To avoid passwords, you can use a custom subdomain:

```bash
# Requires localtunnel account
npx localtunnel --port 3000 --subdomain my-dashboard
npx localtunnel --port 5000 --subdomain my-dashboard-api
```

Or use **ngrok** (more stable):
```bash
ngrok http 3000
ngrok http 5000
```

---

## ✅ Verification

After starting all services, verify:
- ✅ Backend running: http://localhost:5000/health
- ✅ Frontend running: http://localhost:3000
- ✅ Backend tunnel: Visit the URL, enter password, should see API response
- ✅ Frontend tunnel: Visit the URL, enter password, should see dashboard

---

Last Updated: $(date)
