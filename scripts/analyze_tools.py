"""
Analisa o arquivo de ferramentas para identificar problemas.
"""
import json
from pathlib import Path

# Ler arquivo mais recente
tools_files = sorted(Path("backend/debug_llm_responses").glob("tools_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
if not tools_files:
    print("Nenhum arquivo de ferramentas encontrado!")
    exit(1)

tools_file = tools_files[0]
print(f"Analisando: {tools_file.name}\n")

with open(tools_file, encoding='utf-8') as f:
    data = json.load(f)

print(f"Total de ferramentas: {data['converted_tools_count']}\n")

if data['converted_tools']:
    tool = data['converted_tools'][0]
    print(f"Tipo do Tool: {tool['type']}")
    print(f"Has function_declarations: {tool.get('has_function_declarations', False)}")
    print(f"Function declarations count: {tool.get('function_declarations_count', 0)}\n")
    
    if 'function_declarations' in tool:
        print("="*80)
        print("FUNCTION DECLARATIONS:")
        print("="*80)
        
        for i, fd in enumerate(tool['function_declarations']):
            print(f"\n[{i+1}] {fd.get('name', 'NO NAME')}")
            print(f"    Description: {fd.get('description', 'NO DESC')[:100]}...")
            print(f"    Parameters type: {fd.get('parameters_type', 'NO TYPE')}")
            
            # Tentar mostrar estrutura dos parâmetros
            params_str = fd.get('parameters_str', '')
            if 'properties=' in params_str:
                # Extrair properties
                try:
                    props_start = params_str.find('properties=')
                    props_part = params_str[props_start:props_start+500]
                    print(f"    Parameters (partial): {props_part}")
                except:
                    pass
            
            print(f"    Full str (first 500 chars): {fd.get('str', '')[:500]}")

print("\n" + "="*80)
print("ANÁLISE COMPLETA")
print("="*80)
print(f"\nArquivo completo salvo em: {tools_file}")
print("\nPara ver o JSON completo, execute:")
print(f"  python -m json.tool {tools_file}")
