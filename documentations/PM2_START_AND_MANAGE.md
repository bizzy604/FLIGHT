# PM2: Start, Manage and Monitor the rea-travel Application

Scope
- How to start the Frontend (Next.js) and Backend (Uvicorn) with PM2
- Common PM2 commands (start/restart/logs/save/startup) with examples used in this repo
- Notes on environment variables, updating envs, and system boot persistence
- Troubleshooting tips (nginx IPv6/localhost quirk, logs to tail)

Checklist (what you should have before using PM2)
- Node.js and npm/pnpm installed for the Frontend build/runtime
- Python 3.11+ and a virtualenv for Backend (Backend/venv)
- PM2 installed globally: `npm i -g pm2`
- The repository root is `/var/www/rea-travel/FLIGHT`
- An `ecosystem.config.js` or `ecosystem.config.cjs` in repo root (this repo uses `/var/www/rea-travel/FLIGHT/ecosystem.config.js`)
- nginx configured to proxy traffic to the PM2-served ports (usually frontend:3000, backend:8000)

Quick start (one-liners)
- Start using the ecosystem file (recommended):
```bash
cd /var/www/rea-travel/FLIGHT
pm2 start ecosystem.config.js --env production
```
- Start individual apps manually (example):
```bash
# Frontend (Next.js) - if using standalone build
pm2 start "node .next/standalone/server.js" --name frontend

# Backend (Uvicorn) from the project venv (no Node interpreter)
pm2 start /var/www/rea-travel/FLIGHT/Backend/venv/bin/uvicorn --name backend --interpreter none -- --app backend.app:app --host 127.0.0.1 --port 8000
```
Notes:
- When starting binaries where PM2 should not use Node as interpreter, use `--interpreter none` (or in `ecosystem.config.js` set `exec_interpreter: 'none'`).
- The `ecosystem.config.js` can embed env vars under `env` and `env_production` — prefer this for reproducible starts.

Essential PM2 commands (what they do)
- List running processes
```bash
pm2 list
```
- Show detailed info (environment, args, cwd, logs locations)
```bash
pm2 show <id|name>
```
- View real-time combined logs for all processes or one process
```bash
pm2 logs            # all
pm2 logs frontend   # only 'frontend'
pm2 logs backend    # only 'backend'
```
- Tail the last N lines (useful for quick inspection)
```bash
pm2 logs --lines 200 frontend
```
- Restart a process
```bash
pm2 restart frontend
pm2 restart backend
# If env vars were changed in your environment or ecosystem file, use:
pm2 restart frontend --update-env
```
- Reload (zero-downtime; only for Node apps with cluster mode)
```bash
pm2 reload frontend
```
- Stop and delete a process
```bash
pm2 stop frontend
pm2 delete frontend
```
- Save the current process list (so `pm2 resurrect` / startup will restore it)
```bash
pm2 save
```
- Generate and enable startup script for system boot (systemd example)
```bash
# Run as root or with sudo. Replace <user> and <home> if needed.
sudo pm2 startup systemd -u $USER --hp $HOME
# The command prints another command to run as root; run it and then:
pm2 save
```
- Inspect CPU/memory and basic metrics
```bash
pm2 monit
```
- Flush logs
```bash
pm2 flush
```

Using an `ecosystem.config.js` (recommended)
- Put your PM2 processes and envs in `ecosystem.config.js` at project root. Example (high level):
  - `apps[0]` = frontend start command (node standalone or `next start`)
  - `apps[1]` = backend uvicorn binary with `exec_interpreter: 'none'`
- Start with `pm2 start ecosystem.config.js --env production` to pick `env_production` values.
- When editing environment variables inside the ecosystem file, reload with
```bash
pm2 restart ecosystem.config.js --update-env
```

Environment variables and updates
- If you change `.env` files used by the Frontend before start, rebuild (`pnpm build`/`next build`) and restart the frontend process with `--update-env` to load changed env vars into PM2-managed process.
- PM2 reads env vars from the environment it was started in and from `env` blocks in the ecosystem file; `--update-env` tells pm2 to re-pull current envs.

Common production flow (step-by-step)
1. On server, from project root:
```bash
# 1. Build frontend
cd /var/www/rea-travel/FLIGHT/Frontend
pnpm install --frozen-lockfile   # or npm i
pnpm build                       # or npm run build

# 2. Activate python venv and install backend deps (if not already)
cd /var/www/rea-travel/FLIGHT/Backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Start via PM2 using repo ecosystem
cd /var/www/rea-travel/FLIGHT
pm2 start ecosystem.config.js --env production
pm2 save
```
2. Confirm processes are online:
```bash
pm2 list
pm2 logs frontend --lines 200
pm2 logs backend --lines 200
```
3. Enable on boot (one-time):
```bash
sudo pm2 startup systemd -u deploy --hp /home/deploy   # example user 'deploy'
# follow pm2 printed instructions, then
pm2 save
```

Troubleshooting and tips
- No logs appearing for a process
  - Use `pm2 show <name>` to see `out_log` and `err_log` paths. Tail those files directly if needed.
  - Run `pm2 flush` to clear noisy old logs.
- Deploys: update code, rebuild, then run `pm2 restart <name> --update-env` (or restart the ecosystem file).
- Nginx upstream resolving to ::1 (IPv6) and connection refused
  - Problem: `proxy_pass http://localhost:8000;` can resolve to `::1` in systems where `localhost` is IPv6-first. If Uvicorn binds only to 127.0.0.1 (IPv4) nginx may try ::1 and fail intermittently.
  - Fix: use an explicit IPv4 address in nginx configs:
```nginx
proxy_pass http://127.0.0.1:8000;
```
- Unexpected `/api/api/...` or double prefixes
  - Root cause often: frontend build or server route code concatenates a base like `/api` and then adds `/api/...` again. Rebuild frontend after fixing the code and `pm2 restart frontend --update-env`.
- If Uvicorn fails to bind on IPv6 and you want IPv6 support, start uvicorn with `--host ::` and ensure systemd / firewall allows it.

Useful commands summary
```bash
# Start all from ecosystem
pm2 start ecosystem.config.js --env production

# List and inspect
pm2 list
pm2 show frontend

# Logs
pm2 logs frontend
pm2 logs backend --lines 200

# Restart with updated environment vars
pm2 restart frontend --update-env

# Make PM2 persistent across reboots
sudo pm2 startup systemd -u $USER --hp $HOME
pm2 save
```

Where to look for logs
- PM2-managed process stdout/stderr paths (see `pm2 show <name>`); usually in `~/.pm2/logs/<name>-out.log` and `~/.pm2/logs/<name>-error.log`.
- nginx: `/var/log/nginx/access.log` and `/var/log/nginx/error.log`

When to use `--interpreter none` / `exec_interpreter: 'none'`
- When starting non-Node executables (python uvicorn binary from a virtualenv), ensure PM2 doesn't try to run them with Node. Example in `ecosystem.config.js`:
```js
{ name: 'backend', script: '/var/www/rea-travel/FLIGHT/Backend/venv/bin/uvicorn', exec_interpreter: 'none', args: 'backend.app:app --host 127.0.0.1 --port 8000' }
```

Follow-ups you may want
- I can: (1) add a ready-to-use `ecosystem.config.js` example tuned to your repo layout; (2) patch `nginx` site config to replace `localhost` with `127.0.0.1` and reload nginx; (3) run a live test (trigger a flight search) and tail logs to confirm `/api/api` errors are gone.

Document created: `documentations/PM2_START_AND_MANAGE.md`
