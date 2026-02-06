import { createSignal, Show } from 'solid-js';
import { Download, FileJson, FileText } from 'lucide-solid';

interface Message {
  id: string;
  role: string;
  text: string;
  timestamp: number;
}

interface ExportMenuProps {
  messages: () => Message[];
  sessionId: string;
}

export function ExportMenu(props: ExportMenuProps) {
  const [showMenu, setShowMenu] = createSignal(false);

  const downloadFile = (content: string, filename: string, type: string) => {
    const blob = new Blob([content], { type });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const exportAsJSON = () => {
    const data = props.messages().map(m => ({
      role: m.role,
      content: m.text,
      timestamp: new Date(m.timestamp).toISOString()
    }));

    const json = JSON.stringify({
      session_id: props.sessionId,
      exported_at: new Date().toISOString(),
      messages: data
    }, null, 2);

    downloadFile(json, `chatbi-${props.sessionId}.json`, 'application/json');
    setShowMenu(false);
  };

  const exportAsMarkdown = () => {
    let markdown = `# Chat BI - Conversa\n\n`;
    markdown += `**Session ID:** ${props.sessionId}\n`;
    markdown += `**Exportado em:** ${new Date().toLocaleString('pt-BR')}\n\n`;
    markdown += `---\n\n`;

    props.messages().forEach((msg, index) => {
      if (msg.role === 'user') {
        markdown += `## 👤 Usuário\n\n${msg.text}\n\n`;
      } else if (msg.role === 'assistant') {
        markdown += `## 🤖 Assistente\n\n${msg.text}\n\n`;
      }

      markdown += `_${new Date(msg.timestamp).toLocaleString('pt-BR')}_\n\n`;

      if (index < props.messages().length - 1) {
        markdown += `---\n\n`;
      }
    });

    downloadFile(markdown, `chatbi-${props.sessionId}.md`, 'text/markdown');
    setShowMenu(false);
  };

  const exportAsText = () => {
    let text = `Chat BI - Conversa\n`;
    text += `Session ID: ${props.sessionId}\n`;
    text += `Exportado em: ${new Date().toLocaleString('pt-BR')}\n`;
    text += `${'='.repeat(50)}\n\n`;

    props.messages().forEach((msg) => {
      const role = msg.role === 'user' ? 'Usuário' : 'Assistente';
      const time = new Date(msg.timestamp).toLocaleString('pt-BR');
      text += `[${role}] - ${time}\n`;
      text += `${msg.text}\n\n`;
      text += `${'-'.repeat(50)}\n\n`;
    });

    downloadFile(text, `chatbi-${props.sessionId}.txt`, 'text/plain');
    setShowMenu(false);
  };

  return (
    <div class="relative">
      <button
        onClick={() => setShowMenu(!showMenu())}
        class="flex items-center gap-2 px-3 py-2 text-sm rounded-lg border hover:bg-muted transition-colors"
        title="Exportar conversa"
      >
        <Download size={16} />
        <span>Exportar</span>
      </button>

      <Show when={showMenu()}>
        <div class="absolute right-0 top-full mt-2 bg-card border rounded-lg shadow-lg p-2 min-w-[200px] z-50">
          <button
            onClick={exportAsJSON}
            class="w-full flex items-center gap-2 px-3 py-2 text-sm rounded hover:bg-muted transition-colors text-left"
          >
            <FileJson size={16} />
            <span>JSON</span>
          </button>
          <button
            onClick={exportAsMarkdown}
            class="w-full flex items-center gap-2 px-3 py-2 text-sm rounded hover:bg-muted transition-colors text-left"
          >
            <FileText size={16} />
            <span>Markdown</span>
          </button>
          <button
            onClick={exportAsText}
            class="w-full flex items-center gap-2 px-3 py-2 text-sm rounded hover:bg-muted transition-colors text-left"
          >
            <FileText size={16} />
            <span>Texto</span>
          </button>
        </div>
      </Show>

      {/* Overlay to close menu */}
      <Show when={showMenu()}>
        <div
          class="fixed inset-0 z-40"
          onClick={() => setShowMenu(false)}
        />
      </Show>
    </div>
  );
}
