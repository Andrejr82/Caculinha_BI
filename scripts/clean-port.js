/**
 * Cross-platform script to kill processes on specific ports
 * Works on Windows, Linux, and macOS
 * Ports: 8000 (Backend), 3000 (Frontend)
 */

const { execSync } = require('child_process');
const os = require('os');

const PORTS = [8000, 3000];
const platform = os.platform();

console.log(`🧹 Limpando portas... (${platform})\n`);

/**
 * Kill process on Windows
 */
function killPortWindows(port) {
  try {
    console.log(`[${port}] Verificando porta ${port}...`);

    // Find PID using the port
    const result = execSync(`netstat -ano | findstr :${port} | findstr LISTENING`, {
      encoding: 'utf-8',
      stdio: ['pipe', 'pipe', 'ignore']
    });

    if (!result) {
      console.log(`[${port}] ✅ Porta livre\n`);
      return;
    }

    // Extract unique PIDs
    const pids = [...new Set(
      result
        .split('\n')
        .filter(line => line.trim())
        .map(line => {
          const parts = line.trim().split(/\s+/);
          return parts[parts.length - 1];
        })
        .filter(pid => pid && pid !== '0')
    )];

    if (pids.length === 0) {
      console.log(`[${port}] ✅ Porta livre\n`);
      return;
    }

    // Kill each process
    pids.forEach(pid => {
      try {
        console.log(`[${port}] 🔪 Encerrando processo ${pid}...`);
        execSync(`taskkill /F /PID ${pid}`, { stdio: 'ignore' });
        console.log(`[${port}] ✅ Processo ${pid} encerrado`);
      } catch (err) {
        console.log(`[${port}] ⚠️  Não foi possível encerrar processo ${pid}`);
      }
    });

    console.log(`[${port}] ✅ Porta ${port} liberada\n`);

  } catch (err) {
    // Port already free
    console.log(`[${port}] ✅ Porta livre\n`);
  }
}

/**
 * Kill process on Unix-like systems (Linux, macOS)
 */
function killPortUnix(port) {
  try {
    console.log(`[${port}] Verificando porta ${port}...`);

    // Find PID using lsof
    let result;
    try {
      result = execSync(`lsof -ti :${port}`, {
        encoding: 'utf-8',
        stdio: ['pipe', 'pipe', 'pipe']
      });
    } catch (err) {
      // No process found (port is free)
      console.log(`[${port}] ✅ Porta livre\n`);
      return;
    }

    if (!result || !result.trim()) {
      console.log(`[${port}] ✅ Porta livre\n`);
      return;
    }

    // Extract PIDs
    const pids = result
      .trim()
      .split('\n')
      .filter(pid => pid && pid.trim());

    if (pids.length === 0) {
      console.log(`[${port}] ✅ Porta livre\n`);
      return;
    }

    // Kill each process
    pids.forEach(pid => {
      try {
        console.log(`[${port}] 🔪 Encerrando processo ${pid}...`);
        execSync(`kill -9 ${pid}`, { stdio: 'ignore' });
        console.log(`[${port}] ✅ Processo ${pid} encerrado`);
      } catch (err) {
        console.log(`[${port}] ⚠️  Não foi possível encerrar processo ${pid}`);
      }
    });

    console.log(`[${port}] ✅ Porta ${port} liberada\n`);

  } catch (err) {
    // Port already free
    console.log(`[${port}] ✅ Porta livre\n`);
  }
}

/**
 * Main execution
 */
PORTS.forEach(port => {
  if (platform === 'win32') {
    killPortWindows(port);
  } else {
    killPortUnix(port);
  }
});

console.log('✅ Limpeza concluída!\n');
