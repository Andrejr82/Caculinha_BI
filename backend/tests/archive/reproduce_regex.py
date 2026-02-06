import re

def test_regex():
    queries = [
        "gere gráfico de rankig de venddas segmentos na une 2365",
        "gráfico de vendas na une 2365",
        "analisar vendas por loja"
    ]
    
    # New Robust Pattern
    # 1. Keyword (gráfico...)
    # 2. Optional junk + preposition (de/da/do) -> lazy
    # 3. Metric (Group 1)
    # 4. Separator (por/em/nas)
    # 5. Dimension (Group 2)
    p3 = r"(?:gráfico|plotar|ver|analisar).+?(?:de|da|do)?\s+(.+?)\s+(?:por|em|nas)\s+(.+)"
    
    for q in queries:
        print(f"\n--- Query: {q} ---")
        for i, pat in enumerate([p3]):
             print(f"Testing Pattern {i+3}: {pat}")
             match = re.search(pat, q, re.IGNORECASE)
             if match:
                 print(f"✅ MATCH! G1='{match.group(1)}' | G2='{match.group(2)}'")
             else:
                 print("❌ NO MATCH")

if __name__ == "__main__":
    test_regex()
