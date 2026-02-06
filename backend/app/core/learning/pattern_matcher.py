# backend/app/core/learning/pattern_matcher.py

from typing import Any, Dict, List, Optional

class PatternMatcher:
    """
    Detects known query patterns and provides few-shot examples for code generation.
    """
    def __init__(self, patterns_config_path: str = "data/query_patterns.json"):
        self.patterns = self._load_patterns(patterns_config_path)

    def _load_patterns(self, patterns_config_path: str) -> List[Dict[str, Any]]:
        """
        Loads pre-defined patterns and their associated example code/structure.
        """
        # Placeholder: In a real scenario, load from JSON file
        # Example structure:
        # [
        #   {"name": "SalesBySegment", "keywords": ["vendas por segmento"], "example_code": "df.groupby('segmento')['vendas'].sum().to_dicts()"},
        #   {"name": "TopNProducts", "keywords": ["top n produtos", "n maiores produtos"], "example_code": "df.groupby('produto')['vendas'].sum().sort('vendas', descending=True).head(N).to_dicts()"}
        # ]
        print(f"PatternMatcher placeholder: Loading patterns from {patterns_config_path}")
        return [
            {"name": "SalesBySegment", "keywords": ["vendas por segmento", "quanto vendi por segmento"], "example_code": """
import polars as pl
result = df.group_by('segmento').agg(pl.sum('vendas').alias('total_vendas')).sort('total_vendas', descending=True).to_dicts()
final_output = {'result': result}
"""},
            {"name": "TopNProducts", "keywords": ["top", "maiores", "melhores produtos", "produtos mais vendidos"], "example_code": """
import polars as pl
# Replace N with actual number from query
result = df.group_by('produto_id').agg(pl.sum('vendas').alias('total_vendas')).sort('total_vendas', descending=True).head(N).to_dicts()
final_output = {'result': result}
"""},
            {"name": "MCbyProduct", "keywords": ["margem de contribuicao por produto", "mc por produto"], "example_code": """
import polars as pl
result = df.group_by('produto_id').agg(pl.mean('media_considerada_lv').alias('mc_media')).to_dicts()
final_output = {'result': result}
"""}
        ]

    def match_pattern(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Attempts to match the user query against known patterns.
        Returns the pattern with example code if a match is found.
        """
        query_lower = query.lower()
        for pattern in self.patterns:
            for keyword in pattern["keywords"]:
                if keyword in query_lower:
                    print(f"PatternMatcher: Matched pattern '{pattern['name']}' for query: '{query}'")
                    return pattern
        return None

if __name__ == '__main__':
    print("--- Testing PatternMatcher ---")
    matcher = PatternMatcher()
    
    print(f"Matching 'vendas por segmento': {matcher.match_pattern('Me mostre as vendas por segmento.')}")
    print(f"Matching 'top 5 produtos mais vendidos': {matcher.match_pattern('Quais os top 5 produtos mais vendidos?')}")
    print(f"Matching 'margem de contribuicao por produto': {matcher.match_pattern('Calcule a margem de contribuicao por produto.')}")
    print(f"Matching 'query sem match': {matcher.match_pattern('Qual o clima hoje?')}")
