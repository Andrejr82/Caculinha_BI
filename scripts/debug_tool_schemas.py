"""Debug script para analisar schemas das ferramentas."""
import sys
sys.path.insert(0, 'backend')

from app.core.agents.caculinha_bi_agent import CaculinhaBIAgent

agent = CaculinhaBIAgent()
tools_dict = agent._convert_tools_for_llm()

print('=== ANÁLISE DE SCHEMAS ===')
print(f"Total de ferramentas: {len(tools_dict['function_declarations'])}")

for fd in tools_dict['function_declarations']:
    print(f"\n{'='*50}")
    print(f"FERRAMENTA: {fd['name']}")
    print(f"{'='*50}")
    
    params = fd.get('parameters', {})
    props = params.get('properties', {})
    
    print(f"Properties: {len(props)}")
    
    for prop_name, prop_schema in props.items():
        prop_type = prop_schema.get('type', 'UNKNOWN')
        has_anyof = 'anyOf' in prop_schema
        print(f"  - {prop_name}: type={prop_type}, anyOf={has_anyof}")
        if has_anyof:
            print(f"    ⚠️ PROBLEMA: anyOf encontrado!")
            print(f"    anyOf value: {prop_schema['anyOf']}")

print("\n=== FIM DA ANÁLISE ===")
