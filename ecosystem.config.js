/**
 * PM2 ecosystem file to manage Frontend (Next.js) and Backend (Quart/ASGI via Uvicorn)
 *
 * Frontend: runs `npm start` from the `Frontend` directory (Next.js production server).
 * Backend: runs `python3 -m uvicorn Backend.wsgi:app` from the `Backend` directory.
 *
 * Adjust `instances`, `PORT`, `python` path or `args` if you use a virtualenv.
 */
module.exports = {
  apps: [
    {
      name: 'frontend',
      cwd: './Frontend',
      script: 'npm',
      args: 'run start',
  instances: 1,
  exec_mode: 'fork',
  // Run the script as a native executable (no Node/V8 interpreter).
  // Without this PM2 may try to run the binary with Node which causes
  // "SyntaxError: Unexpected identifier 'uvicorn'" because Node attempts
  // to parse a Python executable.
  exec_interpreter: 'none',
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      env: {
        NODE_ENV: 'production',
        PORT: 3000
      }
    },
    {
      name: 'backend',
      cwd: './Backend',
      // Use the project's virtualenv python binary so PM2 runs the uvicorn
      // installed in the venv. Create a venv at `Backend/venv` and install
      // requirements.txt before starting PM2.
      // If you prefer system python, change this back to 'python3'.
  // Use the venv's uvicorn binary directly so PM2 executes the exact
  // program that has uvicorn installed. This avoids `python` resolving
  // to the system interpreter.
  script: '/var/www/rea-travel/FLIGHT/Backend/venv/bin/uvicorn',
  args: 'Backend.wsgi:app --host 0.0.0.0 --port 8000',
      instances: 1,
      exec_mode: 'fork',
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      env: {
        PYTHONUNBUFFERED: '1',
        ENV: 'production',
        PORT: 8000
      }
    }
  ]
};
