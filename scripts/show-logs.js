/**
 * Script para visualizar logs agregados em tempo real
 * Monitora múltiplos arquivos de log e exibe com cores
 */

const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');

// Cores ANSI
const colors = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  dim: '\x1b[2m',

  // Foreground colors
  black: '\x1b[30m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  magenta: '\x1b[35m',
  cyan: '\x1b[36m',
  white: '\x1b[37m',

  // Background colors
  bgBlack: '\x1b[40m',
  bgRed: '\x1b[41m',
  bgGreen: '\x1b[42m',
  bgYellow: '\x1b[43m',
  bgBlue: '\x1b[44m',
  bgMagenta: '\x1b[45m',
  bgCyan: '\x1b[46m',
  bgWhite: '\x1b[47m',
};

// Configuração dos logs a monitorar
const LOG_CONFIGS = [
  {
    file: 'logs/app/app.log',
    name: 'APP',
    color: colors.cyan,
    bgColor: colors.bgBlack,
  },
  {
    file: 'logs/api/api.log',
    name: 'API',
    color: colors.green,
    bgColor: colors.bgBlack,
  },
  {
    file: 'logs/errors/errors.log',
    name: 'ERROR',
    color: colors.red,
    bgColor: colors.bgBlack,
  },
  {
    file: 'logs/security/security.log',
    name: 'SECURITY',
    color: colors.yellow,
    bgColor: colors.bgBlack,
  },
  {
    file: 'logs/chat/chat.log',
    name: 'CHAT',
    color: colors.magenta,
    bgColor: colors.bgBlack,
  },
];

// Cria diretórios de log se não existirem
LOG_CONFIGS.forEach(config => {
  const dir = path.dirname(config.file);
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
  // Cria arquivo vazio se não existir
  if (!fs.existsSync(config.file)) {
    fs.writeFileSync(config.file, '');
  }
});

console.log(colors.bright + colors.cyan);
console.log('╔════════════════════════════════════════════════════════════╗');
console.log('║                    AGENTBI - LOGS                          ║');
console.log('╚════════════════════════════════════════════════════════════╝');
console.log(colors.reset);
console.log();

// Função para formatar o prefixo
function formatPrefix(config) {
  return `${config.bgColor}${config.color}${colors.bright}[${config.name.padEnd(8)}]${colors.reset}`;
}

// Função para processar linha de log
function processLine(line, config) {
  if (!line.trim()) return;

  const prefix = formatPrefix(config);

  // Tenta parsear como JSON para melhor formatação
  try {
    const logData = JSON.parse(line);
    const timestamp = logData.timestamp || '';
    const level = logData.level || logData.levelName || 'INFO';
    const message = logData.message || line;

    // Colorir level
    let levelColor = colors.white;
    if (level === 'ERROR' || level === 'CRITICAL') levelColor = colors.red;
    else if (level === 'WARNING' || level === 'WARN') levelColor = colors.yellow;
    else if (level === 'INFO') levelColor = colors.green;
    else if (level === 'DEBUG') levelColor = colors.dim;

    console.log(
      `${prefix} ${colors.dim}${timestamp}${colors.reset} ${levelColor}${level.padEnd(8)}${colors.reset} ${message}`
    );

    // Mostra contexto adicional se existir
    if (logData.context) {
      console.log(`${' '.repeat(10)}${colors.dim}${JSON.stringify(logData.context)}${colors.reset}`);
    }
    if (logData.error) {
      console.log(`${' '.repeat(10)}${colors.red}${logData.error}${colors.reset}`);
    }
  } catch {
    // Não é JSON, exibe linha normal
    console.log(`${prefix} ${line}`);
  }
}

// Monitora cada arquivo de log
LOG_CONFIGS.forEach(config => {
  if (!fs.existsSync(config.file)) {
    console.log(`${formatPrefix(config)} ${colors.yellow}Aguardando arquivo de log...${colors.reset}`);
    return;
  }

  // No Windows, usamos PowerShell para tail -f
  let tailProcess;

  if (process.platform === 'win32') {
    // PowerShell Get-Content -Wait (equivalente a tail -f)
    tailProcess = spawn('powershell.exe', [
      '-Command',
      `Get-Content -Path "${config.file}" -Wait -Tail 10`
    ]);
  } else {
    // Unix-like systems
    tailProcess = spawn('tail', ['-f', '-n', '10', config.file]);
  }

  tailProcess.stdout.on('data', (data) => {
    const lines = data.toString().split('\n');
    lines.forEach(line => processLine(line, config));
  });

  tailProcess.stderr.on('data', (data) => {
    console.error(`${formatPrefix(config)} ${colors.red}ERRO: ${data}${colors.reset}`);
  });

  tailProcess.on('close', (code) => {
    if (code !== 0) {
      console.log(`${formatPrefix(config)} ${colors.yellow}Processo encerrado (código ${code})${colors.reset}`);
    }
  });

  console.log(`${formatPrefix(config)} ${colors.green}Monitorando...${colors.reset}`);
});

// Tratamento de sinais para encerramento gracioso
process.on('SIGINT', () => {
  console.log('\n\n' + colors.yellow + 'Encerrando monitoramento de logs...' + colors.reset);
  process.exit(0);
});

console.log();
console.log(colors.dim + 'Pressione Ctrl+C para sair' + colors.reset);
console.log();
