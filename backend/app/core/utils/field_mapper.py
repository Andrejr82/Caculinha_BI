# backend/app/core/utils/field_mapper.py

import json
from typing import Any, Dict, List, Optional

class FieldMapper:
    """
    Maps natural language terms to actual database field names using a catalog.
    Also provides known fields for agents.
    
    UPDATED 2026-01-17: Migrated to use column_mapping.py as Single Source of Truth.
    """
    def __init__(self, catalog_path: str = "data/catalog_focused.json"):
        self.catalog_path = catalog_path
        # Try to load external catalog first, fallback to column_mapping.py
        self.catalog = self._load_catalog(catalog_path)
        self.reverse_catalog = {v: k for k, v in self.catalog.items()} # For mapping back if needed

    def _load_catalog(self, catalog_path: str) -> Dict[str, Any]:
        """
        Loads the catalog from a JSON file.
        If not found, uses column_mapping.py as the authoritative source.
        """
        import os
        from pathlib import Path

        # List of potential paths to check
        possible_paths = [
            Path(catalog_path), # As provided
            Path("data/catalog_focused.json"), # Relative to CWD
            Path("backend/data/catalog_focused.json"), # Inside backend
            Path("../data/catalog_focused.json"), # Parent sibling
            Path(os.getcwd()) / "data" / "catalog_focused.json", # Absolute from CWD
            Path(__file__).parent.parent.parent.parent.parent / "data" / "catalog_focused.json" # Relative to source file
        ]

        found_path = None
        for path in possible_paths:
            if path.exists():
                found_path = path
                break
        
        if not found_path:
            print(f"Info: Catalog file not found. Using column_mapping.py as authoritative source (97 colunas).")
            return self._get_catalog_from_column_mapping()

        try:
            with open(found_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return {k.lower(): v for k, v in data.items()}
                else:
                    print(f"Warning: Catalog file {found_path} has unexpected structure. Using column_mapping.py.")
                    return self._get_catalog_from_column_mapping()
        except Exception as e:
            print(f"Warning: Error loading catalog from {found_path}: {e}. Using column_mapping.py.")
            return self._get_catalog_from_column_mapping()

    def _get_catalog_from_column_mapping(self) -> Dict[str, str]:
        """
        Builds catalog dynamically from column_mapping.py (Single Source of Truth).
        Ensures 100% coverage of all 97 columns.
        """
        try:
            from app.infrastructure.data.config.column_mapping import COLUMN_MAP, COLUMN_INFO
            
            catalog = {}
            
            # 1. Add all mappings from COLUMN_MAP (legacy names -> real names)
            for legacy_name, real_name in COLUMN_MAP.items():
                catalog[legacy_name.lower()] = real_name
            
            # 2. Add all real column names (self-mapping for direct access)
            for real_name in COLUMN_INFO.keys():
                catalog[real_name.lower()] = real_name
            
            # 3. Add semantic aliases from COLUMN_INFO descriptions
            semantic_aliases = {
                # Identificadores
                "unidade de negocio": "UNE",
                "loja": "UNE",
                "id da une": "UNE",
                "id do produto": "PRODUTO",
                "sku": "PRODUTO",
                "codigo": "PRODUTO",
                
                # Nomes
                "nome da loja": "UNE_NOME",
                "nome da une": "UNE_NOME",
                "nome do produto": "NOME",
                "descricao": "NOME",
                
                # Classificação
                "segmento de mercado": "NOMESEGMENTO",
                "marca": "NOMEFABRICANTE",
                
                # Estoque
                "estoque": "ESTOQUE_UNE",
                "estoque atual": "ESTOQUE_UNE",
                "estoque da loja": "ESTOQUE_UNE",
                "estoque centro de distribuicao": "ESTOQUE_CD",
                "linha verde": "ESTOQUE_LV",
                "estoque linha verde": "ESTOQUE_LV",
                "gondola": "ESTOQUE_GONDOLA_LV",
                "ilha": "ESTOQUE_ILHA_LV",
                
                # Vendas
                "vendas": "VENDA_30DD",
                "vendas 30 dias": "VENDA_30DD",
                "venda 30 dias": "VENDA_30DD",
                "ultima venda": "ULTIMA_VENDA_DATA_UNE",
                
                # Vendas Mensais
                "mes atual": "MES_PARCIAL",
                "mes anterior": "MES_01",
                "mes passado": "MES_01",
                
                # Vendas Semanais
                "semana atual": "SEMANA_ATUAL",
                "semana passada": "SEMANA_ANTERIOR_2",
                
                # Preços
                "preco": "LIQUIDO_38",
                "preco venda": "LIQUIDO_38",
                "preco de venda": "LIQUIDO_38",
                "custo": "ULTIMA_ENTRADA_CUSTO_CD",
                "preco custo": "ULTIMA_ENTRADA_CUSTO_CD",
                
                # ABC
                "curva abc": "ABC_UNE_30DD",
                "classificacao abc": "ABC_UNE_30DD",
                
                # Logística
                "codigo de barras": "EAN",
                "em promocao": "PROMOCIONAL",
                "fora de linha": "FORALINHA",
                "pedido pendente": "SOLICITACAO_PENDENTE",
                "quantidade pendente": "SOLICITACAO_PENDENTE_QTDE",
                "nota fiscal": "NOTA",
                "romaneio": "ROMANEIO_SOLICITACAO",
            }
            
            catalog.update(semantic_aliases)
            
            print(f"FieldMapper: Loaded {len(catalog)} mappings from column_mapping.py")
            return catalog
            
        except ImportError as e:
            print(f"CRITICAL: Failed to import column_mapping.py: {e}. Using minimal fallback.")
            return self._get_minimal_fallback_catalog()
    
    def _get_minimal_fallback_catalog(self) -> Dict[str, str]:
        """Minimal fallback if column_mapping.py is not available (should never happen)"""
        return {
            "une": "UNE",
            "produto": "PRODUTO",
            "nome": "NOME",
            "estoque": "ESTOQUE_UNE",
            "vendas": "VENDA_30DD",
        }

    def map_term(self, natural_language_term: str) -> Optional[str]:
        """
        Maps a natural language term to its corresponding database field name.
        Performs a case-insensitive lookup.
        """
        if not isinstance(natural_language_term, str):
            return None
        return self.catalog.get(natural_language_term.lower(), natural_language_term)

    def get_known_fields(self) -> List[str]:
        """
        Returns a list of all known natural language terms in the catalog.
        """
        return list(self.catalog.keys())

    def get_db_fields(self) -> List[str]:
        """
        Returns a list of all known database field names in the catalog.
        """
        return list(self.catalog.values())

    def get_essential_columns(self) -> List[str]:
        """
        Returns a list of essential database columns.
        Delegates to column_mapping.py for Single Source of Truth.
        
        FIX 2026-01-27: Added missing method to prevent AttributeError.
        """
        try:
            from app.infrastructure.data.config.column_mapping import get_essential_columns
            return get_essential_columns()
        except ImportError:
            # Fallback to basic essential columns if column_mapping not available
            return [
                "UNE", "PRODUTO", "VENDA_30DD", "ESTOQUE_UNE", 
                "NOMESEGMENTO", "NOME", "UNE_NOME"
            ]

    def suggest_correction(self, invalid_term: str) -> Optional[str]:
        """
        Suggests a correction for an invalid term based on similarity.
        Placeholder for a more advanced fuzzy matching implementation.
        """
        # Placeholder: return the first known field as a suggestion
        known_fields = self.get_known_fields()
        if known_fields:
            return known_fields[0]
        return None

if __name__ == '__main__':
    # Create a dummy catalog_focused.json for testing
    dummy_catalog_path = "data/catalog_focused.json"
    dummy_catalog_content = {
        "unidade de negocio": "une_id",
        "produto": "produto_id",
        "segmento": "segmento",
        "quantidade estoque": "estoque_origem"
    }
    # Ensure 'data' directory exists for this test
    import os
    if not os.path.exists("data"):
        os.makedirs("data")
    with open(dummy_catalog_path, 'w', encoding='utf-8') as f:
        json.dump(dummy_catalog_content, f, indent=4)

    print("--- Testing FieldMapper ---")
    mapper = FieldMapper()
    
    print(f"Map 'Unidade de Negocio': {mapper.map_term('Unidade de Negocio')}")
    print(f"Map 'PRODUTO': {mapper.map_term('PRODUTO')}")
    print(f"Map 'segmento': {mapper.map_term('segmento')}")
    print(f"Map 'quantidade em estoque': {mapper.map_term('quantidade em estoque')}") # Should map to estoque_origem if it recognizes a close match

    print(f"Known fields: {mapper.get_known_fields()}")
    print(f"DB fields: {mapper.get_db_fields()}")

    print(f"Suggest for 'unidade': {mapper.suggest_correction('unidade')}")
    print(f"Suggest for 'produt': {mapper.suggest_correction('produt')}")
    print(f"Suggest for 'non_existent_field': {mapper.suggest_correction('non_existent_field')}")

    # Clean up dummy file
    os.remove(dummy_catalog_path)
    print(f"Cleaned up dummy catalog: {dummy_catalog_path}")
