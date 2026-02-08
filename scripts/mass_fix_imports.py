import os
import re

def fix_imports(directory):
    patterns = [
        (re.compile(r'from app(\.|\s)'), r'from backend.app\1'),
        (re.compile(r'import app(\.|\s)'), r'import backend.app\1'),
        (re.compile(r'from api(\.|\s)'), r'from backend.api\1'),
        (re.compile(r'import api(\.|\s)'), r'import backend.api\1'),
        (re.compile(r'from services(\.|\s)'), r'from backend.services\1'),
        (re.compile(r'import services(\.|\s)'), r'import backend.services\1'),
        (re.compile(r'from core(\.|\s)'), r'from backend.core\1'),
        (re.compile(r'import core(\.|\s)'), r'import backend.core\1'),
        (re.compile(r'from application(\.|\s)'), r'from backend.application\1'),
        (re.compile(r'import application(\.|\s)'), r'import backend.application\1'),
        (re.compile(r'from infrastructure(\.|\s)'), r'from backend.infrastructure\1'),
        (re.compile(r'import infrastructure(\.|\s)'), r'import backend.infrastructure\1'),
        (re.compile(r'from domain(\.|\s)'), r'from backend.domain\1'),
        (re.compile(r'import domain(\.|\s)'), r'import backend.domain\1'),
        (re.compile(r'from utils(\.|\s)'), r'from backend.utils\1'),
        (re.compile(r'import utils(\.|\s)'), r'import backend.utils\1'),
        (re.compile(r'from database(\.|\s)'), r'from backend.database\1'),
        (re.compile(r'import database(\.|\s)'), r'import backend.database\1'),
    ]

    for root, dirs, files in os.walk(directory):
        if '.venv' in root or '__pycache__' in root or '.git' in root:
            continue
            
        for file in files:
            if file.endswith('.py'):
                path = os.path.join(root, file)
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                new_content = content
                for pattern, replacement in patterns:
                    # Only replace if it doesn't already have 'backend.' prefix
                    # We use a negative lookbehind if possible, or just check the resulting string
                    # Simple approach: if 'backend.app' already exists, don't replace 'app' in it
                    # The patterns above are broad, let's refine to avoid 'backend.backend.app'
                    
                    # Refinement: only replace if the line starts with 'from ' or 'import ' 
                    # OR if it's ' import ' (inline) but NOT prefixed by 'backend.'
                    pass # We'll do a better regex in the actual loop

                # Better loop with line-by-line processing
                lines = content.splitlines()
                transformed_lines = []
                changed = False
                
                for line in lines:
                    new_line = line
                    # Avoid replacing already fixed imports
                    if 'backend.' in line:
                        transformed_lines.append(line)
                        continue
                        
                    for pattern, replacement in patterns:
                        # Match 'from X' or 'import X' at start of line (possibly with spaces)
                        # or ' import X' (for inline imports)
                        if re.search(r'^\s*(from|import)\s+', line):
                            new_line = pattern.sub(replacement, new_line)
                    
                    if new_line != line:
                        changed = True
                    transformed_lines.append(new_line)
                
                if changed:
                    print(f"Fixed: {path}")
                    with open(path, 'w', encoding='utf-8') as f:
                        f.write('\n'.join(transformed_lines) + '\n')

if __name__ == "__main__":
    backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend'))
    print(f"Starting import fix in: {backend_dir}")
    fix_imports(backend_dir)
    print("Mass import fix completed.")
