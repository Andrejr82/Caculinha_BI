/**
 * Sistema de Logging para Frontend
 * Gerencia logs no browser e envia logs importantes para o backend
 */

export enum LogLevel {
  DEBUG = 0,
  INFO = 1,
  WARN = 2,
  ERROR = 3,
  CRITICAL = 4,
}

export interface LogEntry {
  timestamp: string;
  level: LogLevel;
  levelName: string;
  message: string;
  context?: Record<string, any>;
  error?: {
    name: string;
    message: string;
    stack?: string;
  };
  user?: {
    id?: string;
    email?: string;
  };
  session?: {
    id?: string;
    duration?: number;
  };
  page?: {
    url: string;
    referrer?: string;
    title?: string;
  };
  browser?: {
    userAgent: string;
    language: string;
    platform: string;
  };
}

export interface LoggerConfig {
  minLevel: LogLevel;
  enableConsole: boolean;
  enableRemote: boolean;
  remoteEndpoint?: string;
  maxBufferSize: number;
  flushInterval: number;
  includeStackTrace: boolean;
  sanitizeData: boolean;
}

/**
 * Classe principal do Logger
 */
class Logger {
  private config: LoggerConfig = {
    minLevel: LogLevel.DEBUG,
    enableConsole: true,
    enableRemote: true,
    remoteEndpoint: '/api/v1/logs',
    maxBufferSize: 50,
    flushInterval: 10000, // 10 segundos
    includeStackTrace: true,
    sanitizeData: true,
  };

  private buffer: LogEntry[] = [];
  private flushTimer: number | null = null;
  private sessionId: string;
  private sessionStart: number;

  constructor(config?: Partial<LoggerConfig>) {
    if (config) {
      this.config = { ...this.config, ...config };
    }

    this.sessionId = this.generateSessionId();
    this.sessionStart = Date.now();

    // Inicia o timer de flush
    this.startFlushTimer();

    // Captura erros globais não tratados
    this.setupGlobalErrorHandlers();

    // Flush antes de sair da página
    if (typeof window !== 'undefined') {
      window.addEventListener('beforeunload', () => {
        this.flush();
      });
    }
  }

  /**
   * Configura o logger
   */
  public configure(config: Partial<LoggerConfig>): void {
    this.config = { ...this.config, ...config };
  }

  /**
   * Gera um ID único para a sessão
   */
  private generateSessionId(): string {
    return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Obtém informações do browser
   */
  private getBrowserInfo() {
    if (typeof window === 'undefined') return undefined;

    return {
      userAgent: navigator.userAgent,
      language: navigator.language,
      platform: navigator.platform,
    };
  }

  /**
   * Obtém informações da página atual
   */
  private getPageInfo() {
    if (typeof window === 'undefined') return undefined;

    return {
      url: window.location.href,
      referrer: document.referrer || undefined,
      title: document.title,
    };
  }

  /**
   * Obtém informações da sessão
   */
  private getSessionInfo() {
    return {
      id: this.sessionId,
      duration: Date.now() - this.sessionStart,
    };
  }

  /**
   * Sanitiza dados sensíveis
   */
  private sanitize(data: any): any {
    if (!this.config.sanitizeData) return data;

    const sensitiveKeys = ['password', 'token', 'secret', 'apiKey', 'api_key', 'authorization'];

    if (typeof data !== 'object' || data === null) return data;

    const sanitized = Array.isArray(data) ? [...data] : { ...data };

    for (const key in sanitized) {
      if (sensitiveKeys.some(sk => key.toLowerCase().includes(sk.toLowerCase()))) {
        sanitized[key] = '***REDACTED***';
      } else if (typeof sanitized[key] === 'object' && sanitized[key] !== null) {
        sanitized[key] = this.sanitize(sanitized[key]);
      }
    }

    return sanitized;
  }

  /**
   * Cria uma entrada de log
   */
  private createLogEntry(
    level: LogLevel,
    message: string,
    context?: Record<string, any>,
    error?: Error
  ): LogEntry {
    const entry: LogEntry = {
      timestamp: new Date().toISOString(),
      level,
      levelName: LogLevel[level],
      message,
      context: context ? this.sanitize(context) : undefined,
      browser: this.getBrowserInfo(),
      page: this.getPageInfo(),
      session: this.getSessionInfo(),
    };

    // Adiciona informações de erro se disponível
    if (error) {
      entry.error = {
        name: error.name,
        message: error.message,
        stack: this.config.includeStackTrace ? error.stack : undefined,
      };
    }

    // Adiciona informações do usuário se disponível
    const user = this.getCurrentUser();
    if (user) {
      entry.user = user;
    }

    return entry;
  }

  /**
   * Obtém informações do usuário atual (do localStorage ou store)
   */
  private getCurrentUser(): { id?: string; email?: string } | undefined {
    if (typeof window === 'undefined') return undefined;

    try {
      const userStr = localStorage.getItem('user');
      if (userStr) {
        const user = JSON.parse(userStr);
        return {
          id: user.id,
          email: user.email,
        };
      }
    } catch {
      // Ignora erros ao buscar usuário
    }

    return undefined;
  }

  /**
   * Registra um log
   */
  private log(
    level: LogLevel,
    message: string,
    context?: Record<string, any>,
    error?: Error
  ): void {
    // Verifica se o nível é suficiente
    if (level < this.config.minLevel) return;

    const entry = this.createLogEntry(level, message, context, error);

    // Log no console
    if (this.config.enableConsole) {
      this.logToConsole(entry);
    }

    // Adiciona ao buffer para envio remoto
    if (this.config.enableRemote) {
      this.buffer.push(entry);

      // Se buffer está cheio, faz flush imediatamente
      if (this.buffer.length >= this.config.maxBufferSize) {
        this.flush();
      }
    }
  }

  /**
   * Escreve log no console do browser
   */
  private logToConsole(entry: LogEntry): void {
    const styles = {
      [LogLevel.DEBUG]: 'color: #888; font-weight: normal',
      [LogLevel.INFO]: 'color: #2563eb; font-weight: normal',
      [LogLevel.WARN]: 'color: #d97706; font-weight: bold',
      [LogLevel.ERROR]: 'color: #dc2626; font-weight: bold',
      [LogLevel.CRITICAL]: 'color: #991b1b; font-weight: bold; font-size: 14px',
    };

    const prefix = `[${entry.levelName}] ${entry.timestamp}`;
    const style = styles[entry.level];

    const consoleMethod =
      entry.level >= LogLevel.ERROR ? console.error :
      entry.level === LogLevel.WARN ? console.warn :
      entry.level === LogLevel.INFO ? console.info :
      console.debug;

    consoleMethod(
      `%c${prefix}`,
      style,
      entry.message,
      entry.context || '',
      entry.error || ''
    );
  }

  /**
   * Inicia o timer de flush automático
   */
  private startFlushTimer(): void {
    if (typeof window === 'undefined') return;

    this.flushTimer = window.setInterval(() => {
      if (this.buffer.length > 0) {
        this.flush();
      }
    }, this.config.flushInterval);
  }

  /**
   * Para o timer de flush
   */
  private stopFlushTimer(): void {
    if (this.flushTimer !== null) {
      clearInterval(this.flushTimer);
      this.flushTimer = null;
    }
  }

  /**
   * Envia logs para o backend
   */
  public async flush(): Promise<void> {
    if (this.buffer.length === 0 || !this.config.enableRemote) return;

    const logsToSend = [...this.buffer];
    this.buffer = [];

    try {
      const response = await fetch(this.config.remoteEndpoint!, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ logs: logsToSend }),
        // Não espera resposta em beforeunload
        keepalive: true,
      });

      if (!response.ok) {
        // Se falhar, recoloca no buffer
        console.warn('Failed to send logs to backend:', response.statusText);
        this.buffer.unshift(...logsToSend);
      }
    } catch (error) {
      // Se falhar, recoloca no buffer
      console.warn('Error sending logs to backend:', error);
      this.buffer.unshift(...logsToSend);
    }
  }

  /**
   * Configura handlers para erros globais
   */
  private setupGlobalErrorHandlers(): void {
    if (typeof window === 'undefined') return;

    // Captura erros não tratados
    window.addEventListener('error', (event) => {
      this.error('Uncaught error', {
        filename: event.filename,
        lineno: event.lineno,
        colno: event.colno,
      }, event.error);
    });

    // Captura promises rejeitadas não tratadas
    window.addEventListener('unhandledrejection', (event) => {
      this.error('Unhandled promise rejection', {
        reason: event.reason,
      });
    });
  }

  // Métodos públicos para cada nível de log

  public debug(message: string, context?: Record<string, any>): void {
    this.log(LogLevel.DEBUG, message, context);
  }

  public info(message: string, context?: Record<string, any>): void {
    this.log(LogLevel.INFO, message, context);
  }

  public warn(message: string, context?: Record<string, any>): void {
    this.log(LogLevel.WARN, message, context);
  }

  public error(message: string, context?: Record<string, any>, error?: Error): void {
    this.log(LogLevel.ERROR, message, context, error);
  }

  public critical(message: string, context?: Record<string, any>, error?: Error): void {
    this.log(LogLevel.CRITICAL, message, context, error);
  }

  /**
   * Métodos para logging de eventos específicos
   */

  public logPageView(pageName: string, metadata?: Record<string, any>): void {
    this.info(`Page view: ${pageName}`, {
      type: 'page_view',
      page: pageName,
      ...metadata,
    });
  }

  public logUserAction(action: string, metadata?: Record<string, any>): void {
    this.info(`User action: ${action}`, {
      type: 'user_action',
      action,
      ...metadata,
    });
  }

  public logApiCall(
    method: string,
    endpoint: string,
    status: number,
    duration: number,
    error?: Error
  ): void {
    const level = status >= 500 ? LogLevel.ERROR : status >= 400 ? LogLevel.WARN : LogLevel.INFO;

    this.log(
      level,
      `API ${method} ${endpoint} - ${status}`,
      {
        type: 'api_call',
        method,
        endpoint,
        status,
        duration,
      },
      error
    );
  }

  public logPerformance(metric: string, value: number, metadata?: Record<string, any>): void {
    this.info(`Performance: ${metric}`, {
      type: 'performance',
      metric,
      value,
      ...metadata,
    });
  }

  /**
   * Limpa o logger e para os timers
   */
  public destroy(): void {
    this.flush();
    this.stopFlushTimer();
  }
}

// Singleton instance
let loggerInstance: Logger | null = null;

/**
 * Obtém a instância singleton do logger
 */
export function getLogger(config?: Partial<LoggerConfig>): Logger {
  if (!loggerInstance) {
    loggerInstance = new Logger(config);
  } else if (config) {
    loggerInstance.configure(config);
  }
  return loggerInstance;
}

/**
 * Exporta uma instância padrão
 */
export const logger = getLogger();

/**
 * Exporta métodos convenientes
 */
export const log = {
  debug: (message: string, context?: Record<string, any>) => logger.debug(message, context),
  info: (message: string, context?: Record<string, any>) => logger.info(message, context),
  warn: (message: string, context?: Record<string, any>) => logger.warn(message, context),
  error: (message: string, context?: Record<string, any>, error?: Error) => logger.error(message, context, error),
  critical: (message: string, context?: Record<string, any>, error?: Error) => logger.critical(message, context, error),
  pageView: (pageName: string, metadata?: Record<string, any>) => logger.logPageView(pageName, metadata),
  userAction: (action: string, metadata?: Record<string, any>) => logger.logUserAction(action, metadata),
  apiCall: (method: string, endpoint: string, status: number, duration: number, error?: Error) =>
    logger.logApiCall(method, endpoint, status, duration, error),
  performance: (metric: string, value: number, metadata?: Record<string, any>) =>
    logger.logPerformance(metric, value, metadata),
};

export default logger;
