# WSL2 Docker Networking Troubleshooting Guide

## Problem
Docker containers running in WSL2 show as healthy but cannot be accessed from Windows browser:
- `ERR_CONNECTION_REFUSED` when accessing `http://localhost:3000`
- Containers show correct port mappings: `0.0.0.0:3000->80/tcp`

## Root Cause
This is a **WSL2 networking limitation**. WSL2 uses a virtualized network adapter with NAT, and port forwarding between WSL2 and Windows doesn't always work automatically, especially after:
- WSL2 restarts
- Windows network changes
- VPN connections
- Windows updates

## Solution Steps

### Step 1: Run Diagnostics
```bash
# Run the diagnostic script (as regular user)
diagnose-wsl-network.bat
```

This will check:
- Container health and port bindings
- Internal container connectivity
- WSL network configuration
- Windows port listeners

**Expected output:**
- ✅ Containers show `0.0.0.0:80` (frontend) and `0.0.0.0:8000` (backend)
- ✅ `curl` from inside containers works
- ✅ `curl` from WSL works
- ❌ Windows can't connect (this is the issue)

---

### Step 2: Apply Port Forwarding Fix
```bash
# Run as ADMINISTRATOR (Right-click -> Run as Administrator)
fix-wsl-port-forwarding.bat
```

This will:
1. Get the current WSL2 IP address
2. Create Windows port proxy rules
3. Add Windows Firewall exceptions
4. Test the connection

**After this, test:** `http://localhost:3000`

---

### Step 3: Alternative - Rebuild Docker Containers
If Step 2 doesn't work, the issue might be with how Docker bound the ports:

```bash
# Run as regular user
fix-docker-compose-network.bat
```

This will:
1. Stop containers cleanly
2. Rebuild images
3. Restart with proper network bindings

---

### Step 4: Manual Verification

#### Check if containers are listening on 0.0.0.0 (not 127.0.0.1)
```bash
wsl docker exec agent_bi_frontend ss -tlnp | grep :80
wsl docker exec agent_bi_backend ss -tlnp | grep :8000
```

**Expected:** Should show `0.0.0.0:80` and `0.0.0.0:8000`

#### Check WSL IP
```bash
wsl hostname -I
```
Example output: `172.18.240.1`

#### Verify port proxy rules
```bash
netsh interface portproxy show all
```

**Expected output:**
```
Listen on ipv4:             Connect to ipv4:
Address         Port        Address         Port
--------------- ----------  --------------- ----------
0.0.0.0         3000        172.18.240.1    3000
0.0.0.0         8000        172.18.240.1    8000
```

---

## Permanent Fix Options

### Option A: Use WSL IP Directly
Instead of `localhost:3000`, use the WSL IP directly:
```
http://172.18.240.1:3000
```

**Note:** This IP changes when WSL restarts.

### Option B: Create Startup Script
Create a Windows scheduled task that runs on startup:

1. Save this as `C:\Agente_BI\wsl-port-forward.ps1`:
```powershell
# Get WSL IP
$wslIP = (wsl hostname -I).Trim()

# Remove old rules
netsh interface portproxy delete v4tov4 listenport=3000 listenaddress=0.0.0.0
netsh interface portproxy delete v4tov4 listenport=8000 listenaddress=0.0.0.0

# Add new rules
netsh interface portproxy add v4tov4 listenport=3000 listenaddress=0.0.0.0 connectport=3000 connectaddress=$wslIP
netsh interface portproxy add v4tov4 listenport=8000 listenaddress=0.0.0.0 connectport=8000 connectaddress=$wslIP
```

2. Create scheduled task:
```powershell
# Run as Administrator
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-File C:\Agente_BI\wsl-port-forward.ps1"
$trigger = New-ScheduledTaskTrigger -AtStartup
Register-ScheduledTask -TaskName "WSL2 Port Forwarding" -Action $action -Trigger $trigger -RunLevel Highest
```

### Option C: Use .wslconfig (Windows 11 only)
Create/edit `C:\Users\<YourUser>\.wslconfig`:
```ini
[wsl2]
localhostForwarding=true
```

Then restart WSL:
```bash
wsl --shutdown
```

---

## Common Issues

### Issue 1: Port already in use
```bash
# Check what's using port 3000 on Windows
netstat -ano | findstr :3000

# Kill the process (replace PID)
taskkill /PID <PID> /F
```

### Issue 2: Firewall blocking
```bash
# Run as Administrator
netsh advfirewall firewall show rule name="WSL2 Frontend Port 3000"
```

### Issue 3: Docker not binding to 0.0.0.0
Check `docker-compose.light.yml`:
```yaml
ports:
  - "3000:80"  # ✅ Correct - binds to 0.0.0.0:3000
  # NOT: "127.0.0.1:3000:80" - this won't work from Windows
```

### Issue 4: VPN interference
Some VPNs block localhost forwarding. Try:
1. Disconnect VPN
2. Test connection
3. If it works, configure VPN to allow local network access

---

## Quick Test Checklist

- [ ] Containers are running: `wsl docker ps`
- [ ] Frontend healthy inside container: `wsl docker exec agent_bi_frontend curl localhost`
- [ ] Frontend accessible from WSL: `wsl curl localhost:3000`
- [ ] Port proxy rules exist: `netsh interface portproxy show all`
- [ ] Firewall rules exist: `netsh advfirewall firewall show rule name=all | findstr WSL2`
- [ ] No process conflict: `netstat -ano | findstr :3000`
- [ ] Test from Windows: `http://localhost:3000`

---

## Debug Commands

### View container logs
```bash
check-docker-logs.bat
```

### Check nginx config inside container
```bash
wsl docker exec agent_bi_frontend cat /etc/nginx/conf.d/default.conf
```

### Test direct curl from Windows to WSL IP
```bash
# Get WSL IP first
wsl hostname -I

# Then test (replace with actual IP)
curl http://172.18.240.1:3000
```

### Restart Docker in WSL
```bash
wsl docker restart agent_bi_frontend agent_bi_backend
```

---

## Last Resort: Full Reset

```bash
# Stop everything
wsl docker-compose -f docker-compose.light.yml down -v

# Clear port proxy rules
netsh interface portproxy reset

# Restart WSL
wsl --shutdown

# Wait 10 seconds, then start fresh
wsl docker-compose -f docker-compose.light.yml up -d

# Apply port forwarding fix again
# (Run as Administrator)
fix-wsl-port-forwarding.bat
```

---

## Expected Working State

```
✅ Frontend container: Listening on 0.0.0.0:80
✅ Backend container: Listening on 0.0.0.0:8000
✅ Docker port mapping: 0.0.0.0:3000->80/tcp
✅ WSL can curl: http://localhost:3000
✅ Windows port proxy: 0.0.0.0:3000 -> <WSL_IP>:3000
✅ Windows firewall: Rules allow TCP 3000, 8000
✅ Windows browser: http://localhost:3000 works!
```

---

## Additional Resources

- WSL2 Networking Docs: https://learn.microsoft.com/en-us/windows/wsl/networking
- Docker Desktop WSL2 Backend: https://docs.docker.com/desktop/wsl/
- Port Proxy Docs: https://learn.microsoft.com/en-us/windows-server/networking/technologies/netsh/netsh-interface-portproxy
