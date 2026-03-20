"""
Parser de anexos para analise de cesta.

Converte anexos textuais da sessao em payload estruturado para:
- itens de cesta/carrinho
- transacoes de market basket
"""

from __future__ import annotations

import csv
import io
import json
import re
import unicodedata
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


ITEM_COLUMN_ALIASES = {
    "sku": {"sku", "codigo", "cod", "produto_id", "product_id", "item_id", "id_produto"},
    "nome": {"nome", "name", "produto", "descricao", "description", "item", "produto_nome"},
    "quantidade": {"quantidade", "qtd", "qty", "quantity", "volume", "unidades"},
    "preco_unitario": {
        "preco",
        "preco_unitario",
        "preco_unit",
        "price",
        "unit_price",
        "valor",
        "valor_unitario",
        "preco_venda",
    },
    "custo_unitario": {
        "custo",
        "custo_unitario",
        "cost",
        "unit_cost",
        "cmv",
        "custo_medio",
        "custo_compra",
    },
    "desconto_pct": {"desconto_pct", "discount_pct", "desconto_percentual", "perc_desconto"},
    "desconto_valor": {"desconto_valor", "discount_value", "desconto", "valor_desconto"},
    "imposto_pct": {"imposto_pct", "tax_pct", "aliquota_imposto", "imposto_percentual", "tributo_pct"},
    "imposto_valor": {"imposto_valor", "tax_value", "valor_imposto", "tributo_valor"},
    "frete_valor": {"frete", "frete_valor", "freight_value", "valor_frete"},
    "despesa_variavel_pct": {
        "despesa_variavel_pct",
        "variable_expense_pct",
        "comissao_pct",
        "taxa_pct",
        "despesa_pct",
    },
    "despesa_variavel_valor": {
        "despesa_variavel_valor",
        "variable_expense_value",
        "comissao_valor",
        "taxa_valor",
        "despesa_valor",
    },
    "custo_fixo_rateado": {"custo_fixo_rateado", "fixed_cost_alloc", "overhead", "rateio_fixo"},
}

TRANSACTION_ID_ALIASES = {
    "pedido",
    "pedido_id",
    "order",
    "order_id",
    "transacao",
    "transacao_id",
    "transaction",
    "transaction_id",
    "cesta_id",
    "basket_id",
    "cupom",
    "ticket",
    "nota",
    "nota_id",
}

TRANSACTION_ITEM_ALIASES = {
    "sku",
    "nome",
    "produto",
    "item",
    "descricao",
    "produto_nome",
    "item_nome",
}

TRANSACTION_LIST_ALIASES = {
    "itens",
    "items",
    "produtos",
    "basket",
    "cesta",
    "carrinho",
}

LIST_SPLIT_PATTERN = re.compile(r"\s*(?:,|;|\||/)\s*")


def _normalize_label(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = re.sub(r"[^a-zA-Z0-9]+", "_", text.lower()).strip("_")
    return text


def _clean_value(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    return text


def _map_item_column(label: str) -> Optional[str]:
    normalized = _normalize_label(label)
    for canonical, aliases in ITEM_COLUMN_ALIASES.items():
        if normalized in aliases:
            return canonical
    return None


def _coerce_record_keys(record: Dict[str, Any]) -> Dict[str, Any]:
    coerced: Dict[str, Any] = {}
    for key, value in record.items():
        normalized_key = _normalize_label(key)
        coerced[normalized_key] = value
    return coerced


def _looks_like_number(value: Optional[str]) -> bool:
    if value in (None, ""):
        return False
    candidate = str(value).strip().replace(".", "").replace(",", ".")
    try:
        float(candidate)
        return True
    except ValueError:
        return False


def _build_item_rows(records: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    for record in records:
        normalized = _coerce_record_keys(record)
        item: Dict[str, Any] = {}
        for original_key, value in normalized.items():
            canonical = _map_item_column(original_key)
            if canonical and _clean_value(value) is not None:
                item[canonical] = str(value).strip()
        if item and any(key in item for key in ("preco_unitario", "custo_unitario", "nome", "sku")):
            items.append(item)
    return items


def _parse_transaction_list_value(raw_value: Any) -> List[str]:
    value = _clean_value(raw_value)
    if not value:
        return []
    if value.startswith("[") and value.endswith("]"):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            parsed = None
        if isinstance(parsed, list):
            return [str(item).strip() for item in parsed if str(item).strip()]
    return [item for item in LIST_SPLIT_PATTERN.split(value) if item]


def _build_transactions(records: Iterable[Dict[str, Any]]) -> List[List[str]]:
    grouped: Dict[str, List[str]] = defaultdict(list)
    standalone: List[List[str]] = []

    for record in records:
        normalized = _coerce_record_keys(record)
        tx_id = next((str(normalized[key]).strip() for key in normalized if key in TRANSACTION_ID_ALIASES and _clean_value(normalized[key])), None)
        list_value = next((normalized[key] for key in normalized if key in TRANSACTION_LIST_ALIASES and _clean_value(normalized[key])), None)

        if list_value is not None:
            items = _parse_transaction_list_value(list_value)
            if items:
                if tx_id:
                    grouped[tx_id].extend(items)
                else:
                    standalone.append(items)
            continue

        item_value = next((normalized[key] for key in normalized if key in TRANSACTION_ITEM_ALIASES and _clean_value(normalized[key])), None)
        if item_value is None:
            continue
        item_text = str(item_value).strip()
        if tx_id:
            grouped[tx_id].append(item_text)
        else:
            standalone.append([item_text])

    transactions = [sorted({item for item in items if item}) for items in grouped.values() if items]
    transactions.extend([items for items in standalone if len(items) > 1])
    return [row for row in transactions if row]


def _records_from_delimited_text(content: str, delimiter_hint: Optional[str] = None) -> List[Dict[str, Any]]:
    if not content.strip():
        return []

    sample = "\n".join(content.splitlines()[:10])
    delimiter = delimiter_hint
    if delimiter is None:
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
            delimiter = dialect.delimiter
        except csv.Error:
            delimiter = ","

    try:
        has_header = csv.Sniffer().has_header(sample)
    except csv.Error:
        has_header = True

    stream = io.StringIO(content)
    if has_header:
        reader = csv.DictReader(stream, delimiter=delimiter)
        return [dict(row) for row in reader if any(_clean_value(value) for value in row.values())]

    reader = csv.reader(stream, delimiter=delimiter)
    rows = [row for row in reader if any(_clean_value(value) for value in row)]
    if not rows:
        return []
    headers = [f"coluna_{index + 1}" for index in range(len(rows[0]))]
    return [dict(zip(headers, row)) for row in rows]


def _records_from_xml(content: str) -> List[Dict[str, Any]]:
    try:
        root = ET.fromstring(content)
    except ET.ParseError:
        return []

    candidates: List[Dict[str, Any]] = []
    for parent in root.iter():
        children = [child for child in list(parent) if list(child)]
        if not children:
            continue
        first_tag = children[0].tag
        if not all(child.tag == first_tag for child in children):
            continue
        rows: List[Dict[str, Any]] = []
        for child in children:
            record: Dict[str, Any] = {}
            for field in list(child):
                value = _clean_value(field.text)
                if value is not None:
                    record[field.tag] = value
            if record:
                rows.append(record)
        if rows:
            return rows

    for element in root.iter():
        record = {}
        for field in list(element):
            value = _clean_value(field.text)
            if value is not None:
                record[field.tag] = value
        if record:
            candidates.append(record)
    return candidates


def _transactions_from_plain_text(content: str) -> List[List[str]]:
    transactions: List[List[str]] = []
    for line in content.splitlines():
        stripped = line.strip(" -*\t")
        if not stripped:
            continue
        items = [item.strip() for item in LIST_SPLIT_PATTERN.split(stripped) if item.strip()]
        if len(items) >= 2:
            transactions.append(items)
    return transactions


def _parse_json_payload(content: str) -> Optional[Dict[str, Any]]:
    try:
        payload = json.loads(content)
    except json.JSONDecodeError:
        return None

    if isinstance(payload, dict):
        if isinstance(payload.get("itens"), list):
            return {"kind": "itens", "payload": {"itens": payload["itens"]}, "warnings": []}
        if isinstance(payload.get("items"), list):
            return {"kind": "itens", "payload": {"itens": payload["items"]}, "warnings": []}
        if isinstance(payload.get("transacoes"), list):
            return {"kind": "transacoes", "payload": {"transacoes": payload["transacoes"]}, "warnings": []}
        if isinstance(payload.get("transactions"), list):
            return {"kind": "transacoes", "payload": {"transacoes": payload["transactions"]}, "warnings": []}

    if isinstance(payload, list) and payload:
        if all(isinstance(item, list) for item in payload):
            return {"kind": "transacoes", "payload": {"transacoes": payload}, "warnings": []}
        if all(isinstance(item, dict) for item in payload):
            items = _build_item_rows(payload)
            if items:
                return {"kind": "itens", "payload": {"itens": items}, "warnings": []}
            transactions = _build_transactions(payload)
            if transactions:
                return {"kind": "transacoes", "payload": {"transacoes": transactions}, "warnings": []}
    return None


def parse_single_attachment(content: str, filename: Optional[str] = None) -> Optional[Dict[str, Any]]:
    if not str(content or "").strip():
        return None

    suffix = Path(str(filename or "")).suffix.lower()
    warnings: List[str] = []

    if suffix == ".json" or str(content).lstrip().startswith(("{", "[")):
        parsed_json = _parse_json_payload(content)
        if parsed_json:
            parsed_json["warnings"] = warnings
            return parsed_json

    records: List[Dict[str, Any]] = []
    if suffix == ".xml" or str(content).lstrip().startswith("<"):
        records = _records_from_xml(content)
    else:
        delimiter_hint = "\t" if suffix == ".tsv" else None
        records = _records_from_delimited_text(content, delimiter_hint=delimiter_hint)

    if records:
        items = _build_item_rows(records)
        transactions = _build_transactions(records)

        if items and not transactions:
            return {"kind": "itens", "payload": {"itens": items}, "warnings": warnings}
        if transactions and not items:
            return {"kind": "transacoes", "payload": {"transacoes": transactions}, "warnings": warnings}
        if items and transactions:
            if any("preco_unitario" in item or "custo_unitario" in item for item in items):
                return {"kind": "itens", "payload": {"itens": items}, "warnings": warnings}
            return {"kind": "transacoes", "payload": {"transacoes": transactions}, "warnings": warnings}

    transactions = _transactions_from_plain_text(content)
    if transactions:
        return {"kind": "transacoes", "payload": {"transacoes": transactions}, "warnings": warnings}

    return None


def build_basket_payload_from_documents(
    documents: List[Dict[str, Any]],
    preferred_kind: str = "auto",
) -> Optional[Dict[str, Any]]:
    grouped: Dict[str, Dict[str, Any]] = {}
    for entry in documents:
        document_id = str(entry.get("document_id") or "").strip()
        if not document_id:
            continue
        metadata = entry.get("metadata") if isinstance(entry.get("metadata"), dict) else {}
        group = grouped.setdefault(
            document_id,
            {
                "document_id": document_id,
                "filename": metadata.get("filename") or document_id,
                "content_parts": [],
            },
        )
        content = str(entry.get("content") or "").strip()
        if content:
            group["content_parts"].append(content)

    items: List[Dict[str, Any]] = []
    transactions: List[List[str]] = []
    matched_files: List[str] = []
    warnings: List[str] = []

    for group in grouped.values():
        content = "\n".join(group["content_parts"]).strip()
        parsed = parse_single_attachment(content, filename=group["filename"])
        if not parsed:
            continue
        matched_files.append(str(group["filename"]))
        warnings.extend(parsed.get("warnings") or [])
        if parsed["kind"] == "itens":
            items.extend(parsed["payload"]["itens"])
        elif parsed["kind"] == "transacoes":
            transactions.extend(parsed["payload"]["transacoes"])

    preferred = (preferred_kind or "auto").strip().lower()
    if preferred == "itens" and items:
        return {"kind": "itens", "payload": {"itens": items}, "files": matched_files, "warnings": warnings}
    if preferred == "transacoes" and transactions:
        return {"kind": "transacoes", "payload": {"transacoes": transactions}, "files": matched_files, "warnings": warnings}
    if preferred == "itens":
        return None
    if preferred == "transacoes":
        return None

    if items:
        return {"kind": "itens", "payload": {"itens": items}, "files": matched_files, "warnings": warnings}
    if transactions:
        return {"kind": "transacoes", "payload": {"transacoes": transactions}, "files": matched_files, "warnings": warnings}
    return None
