
import os
import sys
from pathlib import Path

# Testes não devem depender de provedor LLM externo.
os.environ.setdefault("LLM_PROVIDER", "mock")
os.environ.setdefault("LLM_FALLBACK_PROVIDERS", "mock")
os.environ.setdefault("GROQ_API_KEY", "")
os.environ.setdefault("GEMINI_API_KEY", "")

# Injeta o diretório 'backend' no sys.path para permitir "import app..."
# Isso é necessário porque o código legada e a maioria dos módulos assumem que 'app' é importável diretamente.
BACKEND_ROOT = Path(__file__).parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

# Injeta a raiz do projeto também, se necessário
PROJECT_ROOT = BACKEND_ROOT.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))
