"""
Ferramenta de Pesquisa Concorrencial (consulta externa com fallback controlado).

Objetivo:
- Buscar referências de preço em fontes externas configuradas.
- Priorizar recorte RJ/MG/ES (nicho operacional da Caçula).
- Retornar saída estruturada para síntese executiva pelo agente.
"""

from __future__ import annotations

import json
import logging
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import urlencode, urlparse, urlsplit, parse_qs, unquote
from urllib.request import Request, urlopen

try:
    from langchain_core.tools import tool
except (ImportError, OSError):
    def tool(func):  # type: ignore
        return func

from backend.app.config.settings import settings

logger = logging.getLogger(__name__)

COMPETITOR_ALIASES = {
    "kalunga": ["kalunga"],
    "casa&video": ["casa&video", "casa e video", "casa video", "casaevideo"],
    "le biscuit": ["le biscuit", "lebiscuit"],
    "americanas": ["americanas", "lojas americanas"],
    "amigao": ["amigão", "amigao"],
    "tid's": ["tid's", "tids", "tid"],
    "bellart": ["bellart"],
    "tubarao": ["tubarão", "tubarao"],
    "mercado livre": ["mercado livre", "mercadolivre", "meli"],
    "amazon": ["amazon"],
    "shopee": ["shopee"],
}

COMPETITOR_DOMAINS = {
    "americanas": ["americanas.com.br"],
    "kalunga": ["kalunga.com.br"],
    "bellart": ["bellartdecor.com.br"],
    "casa&video": ["casaevideo.com.br"],
    "le biscuit": ["lebiscuit.com.br"],
    "amazon": ["amazon.com.br"],
    "shopee": ["shopee.com.br"],
    "mercado livre": ["mercadolivre.com.br"],
    # regionais: domínio pode variar por praça; usa busca por marca
    "amigao": ["oamigao.com.br"],
    "tid's": [],
    "tubarao": ["tubaraoatacadao.com.br"],
}

MARKET_COMPETITOR_BY_DOMAIN = {
    "americanas.com.br": "Americanas",
    "kalunga.com.br": "Kalunga",
    "bellartdecor.com.br": "Bellart",
    "casaevideo.com.br": "Casa&Video",
    "lebiscuit.com.br": "Le Biscuit",
    "amazon.com.br": "Amazon",
    "shopee.com.br": "Shopee",
    "mercadolivre.com.br": "Mercado Livre",
}

SOCIAL_COMPETITOR_PROFILES = {
    "amigao": [
        "instagram.com/oamigao",
        "facebook.com/oamigao",
    ],
    "tid's": [
        "instagram.com/tids",
        "facebook.com/tids",
    ],
    "tubarao": [
        "instagram.com/tubaraoatacadao",
        "facebook.com/tubaraoatacadao",
    ],
}


LIKELY_NO_PUBLIC_PRICE = {
    "amigao": "Amigão",
    "tid's": "TID'S",
    "tubarao": "Tubarão",
}


def _target_without_public_price_hint(targets: List[str]) -> List[str]:
    hints: List[str] = []
    for t in targets or []:
        if t in LIKELY_NO_PUBLIC_PRICE and LIKELY_NO_PUBLIC_PRICE[t] not in hints:
            hints.append(LIKELY_NO_PUBLIC_PRICE[t])
    return hints


def _build_sources(items: List[Dict[str, Any]], limit: int = 20) -> List[Dict[str, Any]]:
    sources: List[Dict[str, Any]] = []
    seen: set[str] = set()
    for item in items:
        if len(sources) >= limit:
            break
        if not isinstance(item, dict):
            continue
        url = str(item.get("url") or "").strip()
        domain = str(item.get("dominio") or _extract_domain(url) or "").strip()
        source = str(item.get("fonte") or "").strip()
        competitor = str(item.get("concorrente") or "").strip()
        key = f"{source}|{domain}|{url}"
        if key in seen:
            continue
        seen.add(key)
        sources.append(
            {
                "fonte": source or "desconhecida",
                "dominio": domain or "n/a",
                "url": url or "",
                "concorrente": competitor or "n/a",
            }
        )
    return sources


def _competitor_label(value: Any) -> str:
    label = str(value or "").strip()
    if not label:
        return "desconhecido"
    return label


def _normalize_competitor_display_name(raw_value: Any) -> str:
    value = str(raw_value or "").strip()
    if not value:
        return ""
    compact = _normalize_text(value).replace(" ", "")
    for canonical, aliases in COMPETITOR_ALIASES.items():
        alias_tokens = [a.replace(" ", "") for a in aliases]
        if compact in alias_tokens or compact == canonical.replace(" ", ""):
            return canonical.title() if canonical != "casa&video" else "Casa&Video"
    return value


def _infer_market_competitor(item: Dict[str, Any], url: str) -> str:
    domain = _extract_domain(url)
    for known_domain, display_name in MARKET_COMPETITOR_BY_DOMAIN.items():
        if domain == known_domain or domain.endswith("." + known_domain):
            return display_name

    vendor = _normalize_competitor_display_name(item.get("vendedor"))
    if vendor:
        vendor_low = _normalize_text(vendor)
        if vendor_low not in {"google shopping", "mercado"}:
            return vendor

    if domain:
        return domain
    return "Mercado"


def _diversify_competitor_results(
    items: List[Dict[str, Any]],
    limit: int,
    max_per_competitor: int,
) -> List[Dict[str, Any]]:
    """
    Balanceia saída final para não concentrar em um único concorrente.
    Mantém ordenação por menor preço dentro de cada concorrente.
    """
    if not items or limit <= 0:
        return []

    cap = max(1, int(max_per_competitor or 1))
    buckets: Dict[str, List[Dict[str, Any]]] = {}
    order: List[str] = []
    for item in items:
        comp = _competitor_label(item.get("concorrente"))
        if comp not in buckets:
            buckets[comp] = []
            order.append(comp)
        buckets[comp].append(item)

    used: Dict[str, int] = {comp: 0 for comp in order}
    out: List[Dict[str, Any]] = []
    strict_cap = len(order) > 1

    while len(out) < limit:
        progressed = False
        for comp in order:
            bucket = buckets.get(comp, [])
            if not bucket:
                continue

            if strict_cap and used[comp] >= cap:
                continue

            has_other_available = any(
                other != comp and bool(buckets.get(other))
                for other in order
            )
            if (not strict_cap) and used[comp] >= cap and has_other_available:
                continue

            out.append(bucket.pop(0))
            used[comp] += 1
            progressed = True
            if len(out) >= limit:
                break

        if not progressed:
            break

    return out


def _normalize_text(value: str) -> str:
    return (value or "").strip().lower()


def _brand_tokens(competitor: str) -> List[str]:
    aliases = COMPETITOR_ALIASES.get(competitor, [competitor])
    tokens: List[str] = []
    for a in aliases:
        t = _normalize_text(a).replace("'", "").replace("&", "").replace(" ", "")
        if t and t not in tokens:
            tokens.append(t)
    return tokens


def _allowed_domains() -> List[str]:
    return [d.strip().lower() for d in (settings.COMPETITIVE_DOMAIN_WHITELIST or "").split(",") if d.strip()]


def _extract_domain(url: str) -> str:
    try:
        netloc = urlparse(str(url or "").strip()).netloc.lower()
        return netloc.replace("www.", "")
    except Exception:
        return ""


def _domain_allowed(url: str) -> bool:
    domain = _extract_domain(url)
    if not domain:
        return False
    allow = _allowed_domains()
    if not allow:
        return True
    return any(domain == d or domain.endswith("." + d) for d in allow)


def _price_to_float(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    txt = str(value).strip()
    if not txt:
        return None
    txt = txt.replace("R$", "").replace(" ", "")
    # tenta formato BR
    if "," in txt:
        txt = txt.replace(".", "").replace(",", ".")
    try:
        return float(txt)
    except Exception:
        return None


def _parse_limit(raw_limit: str) -> int:
    default_limit = max(1, int(getattr(settings, "COMPETITIVE_MAX_RESULTS", 20) or 20))
    try:
        parsed = int(str(raw_limit or "").strip())
        return max(1, min(parsed, 50))
    except Exception:
        return default_limit


def _build_location(estado: str, cidade: str) -> str:
    city = (cidade or "").strip()
    st = (estado or "").strip().upper()
    if city and st:
        return f"{city}, {st}, Brazil"
    if st:
        return f"{st}, Brazil"
    return "Brazil"


def _parse_competitors(raw: str) -> List[str]:
    text = _normalize_text(raw)
    if not text:
        return []
    requested = [t.strip() for t in text.split(",") if t.strip()]
    resolved: List[str] = []
    for token in requested:
        matched = False
        for canonical, aliases in COMPETITOR_ALIASES.items():
            if token == canonical or token in aliases:
                resolved.append(canonical)
                matched = True
                break
        if not matched:
            resolved.append(token)
    # unique mantendo ordem
    out: List[str] = []
    for item in resolved:
        if item not in out:
            out.append(item)
    return out


def _all_competitors_requested(text: str) -> bool:
    q = _normalize_text(text)
    return bool(
        re.search(r"\bem\s+tod[oa]s?\s+os?\s+concorrentes?\b", q)
        or re.search(r"\btod[oa]s?\s+os?\s+concorrentes?\b", q)
    )


def _default_scan_competitors(all_mode: bool) -> List[str]:
    if all_mode:
        return ["americanas", "kalunga", "bellart", "amazon", "shopee", "mercado livre", "casa&video", "le biscuit"]
    # Default não pode ser estreito demais; amplia cobertura para reduzir "sem resultado"
    return ["americanas", "kalunga", "bellart", "amazon", "shopee", "mercado livre"]


def _optimize_strategy_for_query(
    priority: List[str],
    target_competitors: List[str],
    timeout: int,
    total_timeout: int,
    default_competitors: List[str],
) -> tuple[List[str], int, int, List[str]]:
    """
    Ajusta estratégia para evitar timeouts em consultas genéricas de mercado.
    """
    if target_competitors:
        preferred = ["websearch", "crawler", "mercadolivre", "google_shopping", "serpapi", "playwright", "social", "bellart", "manual"]
        adjusted_priority = [p for p in preferred if p in priority] + [p for p in priority if p not in preferred]
        adjusted_timeout = min(timeout, 8)
        adjusted_total_timeout = min(total_timeout, 40)
        return adjusted_priority, adjusted_timeout, adjusted_total_timeout, default_competitors

    fast_first = ["websearch", "crawler", "mercadolivre", "google_shopping", "serpapi", "bellart", "playwright", "social", "manual"]
    adjusted_priority = [p for p in fast_first if p in priority] + [p for p in priority if p not in fast_first]
    adjusted_timeout = min(timeout, 8)
    adjusted_total_timeout = min(total_timeout, 35)
    adjusted_competitors = default_competitors[:6] if len(default_competitors) > 6 else default_competitors
    return adjusted_priority, adjusted_timeout, adjusted_total_timeout, adjusted_competitors


def _build_competitor_search_queries(
    product_query: str,
    competitor: str,
    domains: List[str],
    estado: str,
    cidade: str,
) -> List[str]:
    """
    Monta variações de consulta para ampliar cobertura sem perder foco.
    """
    base = (product_query or "").strip()
    if not base:
        return []

    queries: List[str] = []
    location_tokens: List[str] = []
    if cidade:
        location_tokens.append(str(cidade).strip())
    if estado:
        location_tokens.append(str(estado).strip().upper())
    location_hint = " ".join([t for t in location_tokens if t]).strip()

    def _add(value: str) -> None:
        q = re.sub(r"\s+", " ", str(value or "")).strip()
        if q and q not in queries:
            queries.append(q)

    for domain in (domains or [])[:2]:
        _add(f"{base} preço site:{domain}")
        _add(f"{base} site:{domain}")
        if location_hint:
            _add(f"{base} {location_hint} site:{domain}")

    _add(f"{base} preço {competitor}")
    _add(f"{base} {competitor}")
    if location_hint:
        _add(f"{base} {location_hint} {competitor}")

    return queries[:5]


def _extract_product_query(raw: str) -> str:
    """Tenta reduzir pergunta livre para termo de produto pesquisável."""
    q = (raw or "").strip()
    if not q:
        return ""
    q_low = _normalize_text(q)
    # Remove prefixos comuns de comando
    q_low = re.sub(
        r"^(faca|faça|faz|fazer)\s+(uma\s+)?(pesquisa|cotacao|cotação|benchmark)\s+",
        "",
        q_low,
    )
    q_low = re.sub(
        r"^(realize|realizar|realiza)\s+(uma\s+)?(pesquisa|cotacao|cotação|benchmark)\s+",
        "",
        q_low,
    )
    q_low = re.sub(
        r"^(pesquise|pesquisa|compare|comparar|cotação|cotacao|me traga|traga|benchmark)\s+",
        "",
        q_low,
    )
    q_low = re.sub(
        r"^(preço|preco|benchmark de preço|benchmark de preco|cotação de|cotacao de)\s+",
        "",
        q_low,
    )
    q_low = re.sub(
        r"^(do|da|de|o|a)?\s*produto\s+",
        "",
        q_low,
    )
    q_low = re.sub(
        r"^(de\s+mercado|do\s+mercado)\s+(do|da|de|o|a)?\s*produto\s+",
        "",
        q_low,
    )
    q_low = re.sub(
        r"^(pesquisa\s+de\s+mercado|benchmark\s+de\s+mercado)\s+(do|da|de|o|a)?\s*produto\s+",
        "",
        q_low,
    )
    q_low = re.sub(
        r"^(pesquisa\s+de\s+mercado|benchmark\s+de\s+mercado)\s+",
        "",
        q_low,
    )
    # Mantém parte antes de " para ..." (normalmente onde está o concorrente-alvo)
    if " para " in q_low:
        q_low = q_low.split(" para ", 1)[0].strip()
    # Remove sufixos que poluem a descrição do item.
    q_low = re.sub(r"\bem\s+tod[oa]s?\s+os?\s+concorrentes?\b", "", q_low)
    q_low = re.sub(r"\bnos?\s+concorrentes?\b", "", q_low)
    q_low = re.sub(r"\bconcorrentes?\b", "", q_low)
    # Remove recortes geográficos curtos da frase de produto
    q_low = re.sub(r"\b(no|na|em)\s+(rj|mg|es)\b", "", q_low)
    q_low = re.sub(r"\b(rio de janeiro|minas gerais|espírito santo|espirito santo)\b", "", q_low)
    # Remove conectivos finais
    q_low = re.sub(r"\s+", " ", q_low).strip(" .,-")
    return q_low or q


def _item_matches_competitor(item: Dict[str, Any], competitors: List[str]) -> bool:
    if not competitors:
        return True
    source = _normalize_text(str(item.get("concorrente") or ""))
    title = _normalize_text(str(item.get("produto") or ""))
    haystack = f"{source} {title}"
    for comp in competitors:
        aliases = COMPETITOR_ALIASES.get(comp, [comp])
        if any(alias in haystack for alias in aliases):
            return True
    return False


def _quality_gate_item(item: Dict[str, Any]) -> tuple[bool, str, Dict[str, Any]]:
    """
    Regra de qualidade/evidência:
    - produto e preço obrigatórios
    - para fontes externas, URL válida e domínio whitelist obrigatório
    - exceção: fontes de Google Shopping aceitam URL+preço sem restringir domínio do lojista
    - para base manual, URL é opcional (somente quando manual estiver habilitado)
    """
    source = _normalize_text(str(item.get("fonte") or ""))
    product = str(item.get("produto") or "").strip()
    price_num = _price_to_float(item.get("preco"))
    url = str(item.get("url") or "").strip()
    domain = _extract_domain(url)

    if not product:
        return False, "produto_ausente", item
    if price_num is None:
        return False, "preco_ausente_ou_invalido", item

    is_manual = source in {"base_manual_concorrencial", "csv_compras", "coleta_manual_compras"}
    if is_manual and not bool(getattr(settings, "COMPETITIVE_ALLOW_MANUAL", False)):
        return False, "manual_desabilitado", item

    if not is_manual:
        if not url:
            return False, "url_ausente", item
        if source in {"serpapi_google_shopping", "google_shopping_web"}:
            if not domain:
                return False, "dominio_ausente_google_shopping", item
            normalized = dict(item)
            normalized["preco"] = price_num
            normalized["dominio"] = domain
            normalized["disponibilidade"] = normalized.get("disponibilidade") or "nao_validada"
            return True, "ok", normalized

        target_comp = _normalize_text(str(item.get("target_competitor") or ""))
        tokens = _brand_tokens(target_comp) if target_comp else []
        compact_domain = domain.replace(".", "")
        brand_ok = any(t in compact_domain for t in tokens if t)

        if not (_domain_allowed(url) or brand_ok):
            reason = "dominio_nao_whitelist"
            if target_comp:
                reason = "dominio_nao_confere_competidor"
            return False, f"{reason}:{domain or 'desconhecido'}", item

    normalized = dict(item)
    normalized["preco"] = price_num
    normalized["dominio"] = domain if domain else ("manual" if is_manual else "")
    normalized["disponibilidade"] = normalized.get("disponibilidade") or "nao_validada"
    return True, "ok", normalized


# --- Headers realistas para scraping (Google, DuckDuckGo) ---
_BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "identity",
    "DNT": "1",
    "Connection": "keep-alive",
}

# --- Headers leves para chamadas de API REST (Mercado Livre, SerpAPI) ---
_API_HEADERS = {
    "User-Agent": "CaculinhaBI/2.0 (market-research)",
    "Accept": "application/json,text/plain,*/*",
}


def _http_get_json(url: str, params: Dict[str, Any], timeout: int) -> Dict[str, Any]:
    """GET JSON usando headers leves de API (compatível com Mercado Livre, SerpAPI)."""
    encoded = urlencode(params, doseq=True)
    full_url = f"{url}?{encoded}" if encoded else url
    req = Request(full_url, headers=dict(_API_HEADERS))
    with urlopen(req, timeout=timeout) as resp:  # nosec B310 - URL controlado por código
        body = resp.read().decode("utf-8", errors="ignore")
    try:
        return json.loads(body)
    except Exception:
        return {}


def _http_get_text(url: str, timeout: int) -> str:
    """GET HTML usando headers realistas de browser (para scraping Google/DDG)."""
    headers = dict(_BROWSER_HEADERS)
    headers["Accept"] = "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    req = Request(url, headers=headers)
    with urlopen(req, timeout=timeout) as resp:  # nosec B310 - destino controlado
        return resp.read().decode("utf-8", errors="ignore")


def _extract_price_from_text(text: str) -> float | None:
    if not text:
        return None
    match = re.search(r"R\$\s*([0-9]{1,3}(?:\.[0-9]{3})*(?:,[0-9]{2})|[0-9]+(?:,[0-9]{2})?)", text)
    if not match:
        return None
    return _price_to_float(match.group(1))


def _search_social_competitor(
    competitor: str,
    product_query: str,
    limit: int,
    timeout: int,
    estado: str,
    cidade: str,
) -> List[Dict[str, Any]]:
    """
    Busca preço em menções públicas de Instagram/Facebook via snippet de busca.
    Mantém validação por evidência: preço explícito + URL.
    """
    profiles = SOCIAL_COMPETITOR_PROFILES.get(competitor, [])
    if not profiles:
        return []

    results: List[Dict[str, Any]] = []
    seen: set[str] = set()
    started_at = time.monotonic()
    soft_deadline = max(3.0, float(timeout) * 2.0)
    for profile in profiles:
        if (time.monotonic() - started_at) > soft_deadline:
            break
        if len(results) >= limit:
            break
        query = f"{product_query} R$ site:{profile}"
        ddg_url = f"https://duckduckgo.com/html/?{urlencode({'q': query})}"
        try:
            html = _http_get_text(ddg_url, timeout=timeout)
        except Exception:
            continue

        blocks = re.findall(
            r'(<div[^>]+class="[^"]*result[^"]*"[^>]*>.*?</div>\s*</div>)',
            html,
            flags=re.IGNORECASE | re.DOTALL,
        )
        if not blocks:
            blocks = [html]

        for block in blocks:
            if (time.monotonic() - started_at) > soft_deadline:
                break
            if len(results) >= limit:
                break
            link_match = re.search(r'href="(https?://[^"]+)"', block, flags=re.IGNORECASE)
            if not link_match:
                continue
            link = link_match.group(1).strip()
            if link in seen:
                continue
            seen.add(link)

            snippet = re.sub(r"<[^>]+>", " ", block)
            snippet = re.sub(r"\s+", " ", snippet).strip()
            price_val = _extract_price_from_text(snippet)
            if price_val is None:
                continue

            title_match = re.search(r'<a[^>]*class="[^"]*result__a[^"]*"[^>]*>(.*?)</a>', block, flags=re.IGNORECASE | re.DOTALL)
            title_raw = title_match.group(1) if title_match else ""
            title = re.sub(r"<[^>]+>", " ", title_raw)
            title = re.sub(r"\s+", " ", title).strip() or f"Oferta social {competitor}"

            results.append(
                {
                    "concorrente": competitor,
                    "produto": title,
                    "preco": price_val,
                    "moeda": "BRL",
                    "fonte": "social_websearch",
                    "url": link,
                    "estado": estado,
                    "cidade": cidade,
                    "target_competitor": competitor,
                    "evidencia_social": snippet[:300],
                }
            )
    return results


def _search_competitor_web(
    competitor: str,
    product_query: str,
    limit: int,
    timeout: int,
    estado: str,
    cidade: str,
) -> List[Dict[str, Any]]:
    """
    Busca pública sem API por concorrente usando DuckDuckGo HTML e parsing de página.
    """
    domains = COMPETITOR_DOMAINS.get(competitor, [])
    queries = _build_competitor_search_queries(product_query, competitor, domains, estado, cidade)
    if not queries:
        return []

    results: List[Dict[str, Any]] = []
    seen: set[str] = set()
    started_at = time.monotonic()
    soft_deadline = max(3.0, float(timeout) * 2.0)
    for query in queries:
        if (time.monotonic() - started_at) > soft_deadline:
            break
        if len(results) >= limit:
            break
        ddg_url = f"https://duckduckgo.com/html/?{urlencode({'q': query})}"
        try:
            html = _http_get_text(ddg_url, timeout=timeout)
        except Exception:
            continue

        links = re.findall(r'<a[^>]+class="[^"]*result__a[^"]*"[^>]+href="([^"]+)"', html, flags=re.IGNORECASE)
        if not links:
            links = re.findall(r'<a[^>]+href="(https?://[^"]+)"', html, flags=re.IGNORECASE)

        for link in links:
            if (time.monotonic() - started_at) > soft_deadline:
                break
            if len(results) >= limit:
                break
            link = link.strip()
            if not link.startswith("http"):
                continue
            if link in seen:
                continue
            seen.add(link)

            # Se houver domínio conhecido, restringe; senão aceita e valida depois por brand token.
            domain = _extract_domain(link)
            if domains and not any(domain == d or domain.endswith("." + d) for d in domains):
                continue

            try:
                page = _http_get_text(link, timeout=timeout)
            except Exception:
                continue

            price_match = re.search(r"R\$\s*([0-9\.\,]+)", page)
            if not price_match:
                continue
            raw_price = price_match.group(1)
            price_val = _price_to_float(raw_price)
            if price_val is None:
                continue

            title_match = re.search(r"<title>(.*?)</title>", page, flags=re.IGNORECASE | re.DOTALL)
            title_raw = title_match.group(1) if title_match else ""
            title = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", title_raw)).strip() or f"Produto {competitor}"

            results.append(
                {
                    "concorrente": competitor,
                    "produto": title,
                    "preco": price_val,
                    "moeda": "BRL",
                    "fonte": "websearch_competitor",
                    "url": link,
                    "estado": estado,
                    "cidade": cidade,
                    "target_competitor": competitor,
                }
            )
    return results


def _search_competitor_playwright(
    competitor: str,
    product_query: str,
    limit: int,
    timeout: int,
    estado: str,
    cidade: str,
) -> List[Dict[str, Any]]:
    """
    Busca concorrente com navegador real (Playwright) para páginas dinâmicas.
    Retorna [] se Playwright não estiver disponível no ambiente.
    """
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        return []

    domains = COMPETITOR_DOMAINS.get(competitor, [])
    queries = _build_competitor_search_queries(product_query, competitor, domains, estado, cidade)
    if not queries:
        return []

    results: List[Dict[str, Any]] = []
    seen: set[str] = set()
    timeout_ms = max(2000, timeout * 1000)
    started_at = time.monotonic()
    soft_deadline = max(4.0, float(timeout) * 2.0)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            for query in queries:
                if (time.monotonic() - started_at) > soft_deadline:
                    break
                if len(results) >= limit:
                    break
                ddg_url = f"https://duckduckgo.com/html/?{urlencode({'q': query})}"
                try:
                    page.goto(ddg_url, timeout=timeout_ms, wait_until="domcontentloaded")
                except Exception:
                    continue

                anchors = page.eval_on_selector_all(
                    "a.result__a",
                    "els => els.map(el => ({href: el.href || '', title: (el.textContent||'').trim()}))",
                )

                for row in anchors:
                    if (time.monotonic() - started_at) > soft_deadline:
                        break
                    if len(results) >= limit:
                        break
                    link = str((row or {}).get("href") or "").strip()
                    title = str((row or {}).get("title") or "").strip()
                    if not link or link in seen or not link.startswith("http"):
                        continue
                    seen.add(link)

                    domain = _extract_domain(link)
                    if domains and not any(domain == d or domain.endswith("." + d) for d in domains):
                        continue

                    try:
                        tab = browser.new_page()
                        tab.goto(link, timeout=timeout_ms, wait_until="domcontentloaded")
                        text = tab.inner_text("body")
                        html = tab.content()
                        tab.close()
                    except Exception:
                        continue

                    price_val = _extract_price_from_text(text) or _extract_price_from_text(html)
                    if price_val is None:
                        continue

                    results.append(
                        {
                            "concorrente": competitor,
                            "produto": title or f"Produto {competitor}",
                            "preco": price_val,
                            "moeda": "BRL",
                            "fonte": "playwright_competitor",
                            "url": link,
                            "estado": estado,
                            "cidade": cidade,
                            "target_competitor": competitor,
                        }
                    )
            browser.close()
    except Exception:
        return []

    return results


def _search_competitor_crawler(
    competitor: str,
    product_query: str,
    limit: int,
    timeout: int,
    estado: str,
    cidade: str,
) -> List[Dict[str, Any]]:
    """
    Crawler HTML com parser estruturado (BeautifulSoup quando disponível).
    Fallback para regex quando bs4 não estiver instalado.
    """
    domains = COMPETITOR_DOMAINS.get(competitor, [])
    query = f"{product_query} site:{domains[0]}" if domains else f"{product_query} {competitor}"
    ddg_url = f"https://duckduckgo.com/html/?{urlencode({'q': query})}"
    started_at = time.monotonic()
    soft_deadline = max(3.0, float(timeout) * 2.0)

    try:
        html = _http_get_text(ddg_url, timeout=timeout)
    except Exception:
        return []

    links: List[str] = []
    titles: Dict[str, str] = {}
    try:
        from bs4 import BeautifulSoup  # type: ignore

        soup = BeautifulSoup(html, "html.parser")
        for a in soup.select("a.result__a"):
            href = (a.get("href") or "").strip()
            title = a.get_text(" ", strip=True)
            if href.startswith("http"):
                links.append(href)
                titles[href] = title
    except Exception:
        # fallback regex
        for href in re.findall(r'<a[^>]+class="[^"]*result__a[^"]*"[^>]+href="([^"]+)"', html, flags=re.IGNORECASE):
            href = href.strip()
            if href.startswith("http"):
                links.append(href)
        if not links:
            links = re.findall(r'<a[^>]+href="(https?://[^"]+)"', html, flags=re.IGNORECASE)

    results: List[Dict[str, Any]] = []
    seen: set[str] = set()
    for link in links:
        if (time.monotonic() - started_at) > soft_deadline:
            break
        if len(results) >= limit:
            break
        if link in seen:
            continue
        seen.add(link)

        domain = _extract_domain(link)
        if domains and not any(domain == d or domain.endswith("." + d) for d in domains):
            continue

        try:
            page = _http_get_text(link, timeout=timeout)
        except Exception:
            continue

        price_val = _extract_price_from_text(page)
        if price_val is None:
            continue

        title = titles.get(link, "").strip()
        if not title:
            title_match = re.search(r"<title>(.*?)</title>", page, flags=re.IGNORECASE | re.DOTALL)
            title_raw = title_match.group(1) if title_match else ""
            title = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", title_raw)).strip()

        results.append(
            {
                "concorrente": competitor,
                "produto": title or f"Produto {competitor}",
                "preco": price_val,
                "moeda": "BRL",
                "fonte": "crawler_competitor",
                "url": link,
                "estado": estado,
                "cidade": cidade,
                "target_competitor": competitor,
            }
        )
    return results


def _search_mercadolivre(query: str, limit: int, timeout: int, estado: str, cidade: str) -> List[Dict[str, Any]]:
    payload = _http_get_json(
        "https://api.mercadolibre.com/sites/MLB/search",
        {"q": query, "limit": limit},
        timeout=timeout,
    )
    items = payload.get("results", []) if isinstance(payload, dict) else []
    out: List[Dict[str, Any]] = []
    for item in items[:limit]:
        if not isinstance(item, dict):
            continue
        out.append(
            {
                "concorrente": "Mercado Livre",
                "produto": item.get("title"),
                "preco": item.get("price"),
                "moeda": item.get("currency_id") or "BRL",
                "fonte": "mercadolivre_api",
                "url": item.get("permalink"),
                "estado": estado,
                "cidade": cidade,
            }
        )
    return out


def _unwrap_google_link(raw_href: str) -> str:
    href = str(raw_href or "").strip()
    if not href:
        return ""
    href = href.replace("&amp;", "&")

    if href.startswith("/url?"):
        parsed = parse_qs(urlsplit(href).query)
        candidate = (parsed.get("q") or parsed.get("url") or [""])[0]
        return unquote(candidate)

    if href.startswith("https://www.google.com/url?") or href.startswith("https://www.google.com.br/url?"):
        parsed = parse_qs(urlsplit(href).query)
        candidate = (parsed.get("q") or parsed.get("url") or [""])[0]
        return unquote(candidate)

    return href


def _search_google_shopping_web(
    query: str,
    limit: int,
    timeout: int,
    estado: str,
    cidade: str,
) -> List[Dict[str, Any]]:
    params = {
        "q": query,
        "udm": "28",
        "hl": "pt-BR",
        "gl": "br",
    }
    if cidade or estado:
        params["location"] = _build_location(estado, cidade)

    url = f"https://www.google.com/search?{urlencode(params)}"
    try:
        html = _http_get_text(url, timeout=timeout)
    except Exception:
        return []

    anchor_pattern = re.compile(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', flags=re.IGNORECASE | re.DOTALL)
    clean_tag_pattern = re.compile(r"<[^>]+>")

    out: List[Dict[str, Any]] = []
    seen: set[str] = set()
    for match in anchor_pattern.finditer(html):
        if len(out) >= limit:
            break

        href = _unwrap_google_link(match.group(1))
        if not href.startswith("http"):
            continue
        if href in seen:
            continue
        seen.add(href)

        domain = _extract_domain(href)
        if not domain:
            continue

        start, end = match.span()
        snippet = html[max(0, start - 400):min(len(html), end + 400)]
        price = _extract_price_from_text(snippet)
        if price is None:
            continue

        title_raw = clean_tag_pattern.sub(" ", match.group(2) or "")
        title = re.sub(r"\s+", " ", title_raw).strip()
        if not title or len(title) < 3:
            title = f"Produto em {domain}"

        out.append(
            {
                "concorrente": domain,
                "produto": title,
                "preco": price,
                "moeda": "BRL",
                "fonte": "google_shopping_web",
                "url": href,
                "estado": estado,
                "cidade": cidade,
            }
        )
    return out


def _search_serpapi(
    query: str,
    limit: int,
    timeout: int,
    estado: str,
    cidade: str,
) -> List[Dict[str, Any]]:
    api_key = (settings.SERPAPI_API_KEY or "").strip()
    if not api_key:
        return _search_google_shopping_web(query, limit, timeout, estado, cidade)

    payload = _http_get_json(
        "https://serpapi.com/search.json",
        {
            "engine": settings.SERPAPI_ENGINE,
            "q": query,
            "api_key": api_key,
            "hl": "pt-br",
            "gl": "br",
            "location": _build_location(estado, cidade),
            "num": limit,
        },
        timeout=timeout,
    )
    items = payload.get("shopping_results", []) if isinstance(payload, dict) else []
    out: List[Dict[str, Any]] = []

    def _serpapi_url(row: Dict[str, Any]) -> str:
        for key in ("link", "product_link", "shopping_link", "offer_link", "serpapi_link"):
            value = str(row.get(key) or "").strip()
            if value:
                return value
        return ""

    for item in items[: max(limit * 2, limit)]:
        if not isinstance(item, dict):
            continue
        extracted = item.get("extracted_price")
        if extracted is None:
            price_raw = str(item.get("price") or "")
            extracted = price_raw
        out.append(
            {
                "concorrente": item.get("source") or item.get("store_name") or "Google Shopping",
                "produto": item.get("title"),
                "preco": extracted,
                "moeda": "BRL",
                "fonte": "serpapi_google_shopping",
                "url": _serpapi_url(item),
                "estado": estado,
                "cidade": cidade,
            }
        )
    return out[:limit]


def _search_bellart(query: str, limit: int, timeout: int, estado: str, cidade: str) -> List[Dict[str, Any]]:
    """
    Consulta direta ao e-commerce Bellart (WordPress/WooCommerce) via busca pública.
    """
    encoded = urlencode({"s": query})
    search_url = f"https://www.bellartdecor.com.br/?{encoded}"
    with urlopen(search_url, timeout=timeout) as resp:  # nosec B310 - domínio fixo
        html = resp.read().decode("utf-8", errors="ignore")

    # Captura cards com link de produto e valor em BRL.
    card_pattern = re.compile(
        r'<a[^>]+href="(?P<link>https://www\.bellartdecor\.com\.br/[^"]+)"[^>]*>(?P<inner>.*?)</a>',
        flags=re.IGNORECASE | re.DOTALL,
    )
    price_pattern = re.compile(r"R\$\s*([0-9\.\,]+)")
    title_pattern = re.compile(r'title="([^"]+)"', flags=re.IGNORECASE)
    clean_tag_pattern = re.compile(r"<[^>]+>")

    results: List[Dict[str, Any]] = []
    seen_links: set[str] = set()
    for match in card_pattern.finditer(html):
        link = match.group("link").strip()
        if "/produto/" not in link:
            continue
        if link in seen_links:
            continue
        seen_links.add(link)
        inner = match.group("inner") or ""
        title_match = title_pattern.search(match.group(0))
        title = title_match.group(1).strip() if title_match else clean_tag_pattern.sub(" ", inner).strip()
        price_match = price_pattern.search(inner)
        if not price_match:
            continue
        raw_price = price_match.group(1)
        normalized_price = raw_price.replace(".", "").replace(",", ".")
        try:
            price_val: Any = float(normalized_price)
        except Exception:
            price_val = raw_price
        results.append(
            {
                "concorrente": "Bellart",
                "produto": title or "Produto Bellart",
                "preco": price_val,
                "moeda": "BRL",
                "fonte": "bellart_site",
                "url": link,
                "estado": estado,
                "cidade": cidade,
            }
        )
        if len(results) >= limit:
            break
    return results


def _load_manual_reference(
    query: str,
    segmento: str,
    estado: str,
    cidade: str,
    limit: int,
    competitors: List[str],
) -> List[Dict[str, Any]]:
    file_path = Path(settings.COMPETITIVE_MANUAL_FILE)
    if not file_path.exists():
        return []
    try:
        raw = json.loads(file_path.read_text(encoding="utf-8"))
    except Exception as e:
        logger.warning(f"Falha ao ler base manual concorrencial: {e}")
        return []

    if not isinstance(raw, list):
        return []

    qn = _normalize_text(query)
    sn = _normalize_text(segmento)
    st = _normalize_text(estado)
    ct = _normalize_text(cidade)

    out: List[Dict[str, Any]] = []
    for row in raw:
        if not isinstance(row, dict):
            continue
        row_estado = _normalize_text(str(row.get("estado", "")))
        row_cidade = _normalize_text(str(row.get("cidade", "")))
        row_segmento = _normalize_text(str(row.get("segmento", "")))
        row_produto = _normalize_text(str(row.get("produto", "")))

        if st and row_estado and row_estado != st:
            continue
        if ct and row_cidade and row_cidade != ct:
            continue
        if sn and row_segmento and sn not in row_segmento:
            continue
        if qn and row_produto and qn not in row_produto and qn not in _normalize_text(str(row.get("descricao", ""))):
            continue

        item = {
            "concorrente": row.get("concorrente"),
            "produto": row.get("produto") or row.get("descricao"),
            "preco": row.get("preco"),
            "moeda": row.get("moeda") or "BRL",
            "fonte": row.get("fonte") or "base_manual_concorrencial",
            "url": row.get("url"),
            "estado": row.get("estado") or estado,
            "cidade": row.get("cidade") or cidade,
        }
        if not _item_matches_competitor(item, competitors):
            continue
        out.append(item)
        if len(out) >= limit:
            break
    return out


@tool
def pesquisar_precos_concorrentes(
    descricao_produto: str,
    segmento: str = "",
    estado: str = "RJ",
    cidade: str = "",
    limite: str = "10",
    concorrentes: str = "",
) -> Dict[str, Any]:
    """
    Pesquisa referências de preços em concorrentes/marketplaces para compras.

    USE QUANDO:
    - Usuário pedir pesquisa de preço de mercado/concorrência.
    - Usuário pedir comparação com concorrentes (RJ/MG/ES).

    PARÂMETROS:
    - descricao_produto: descrição ou SKU pesquisado
    - segmento: segmento comercial (ex.: PAPELARIA, ARTES)
    - estado: UF foco (RJ, MG, ES)
    - cidade: cidade foco (opcional)
    - limite: quantidade máxima de resultados (string numérica)
    - concorrentes: nomes de concorrentes desejados separados por vírgula (opcional)
    """
    if not settings.COMPETITIVE_INTEL_ENABLED:
        return {
            "status": "error",
            "error": "Pesquisa concorrencial está desabilitada no ambiente.",
        }

    query = (descricao_produto or "").strip()
    if not query:
        return {
            "status": "error",
            "error": "Informe o produto/descrição para pesquisa concorrencial.",
        }

    allowed_states = {s.strip().upper() for s in (settings.COMPETITIVE_ALLOWED_STATES or "").split(",") if s.strip()}
    state = (estado or "").strip().upper() or "RJ"
    if allowed_states and state not in allowed_states:
        return {
            "status": "error",
            "error": f"Estado '{state}' fora do escopo configurado ({', '.join(sorted(allowed_states))}).",
        }

    limit = _parse_limit(limite)
    timeout = max(2, int(settings.COMPETITIVE_HTTP_TIMEOUT_SEC or 10))
    total_timeout = max(timeout, int(getattr(settings, "COMPETITIVE_TOTAL_TIMEOUT_SEC", 25) or 25))
    max_items_per_competitor = max(1, int(getattr(settings, "COMPETITIVE_MAX_ITEMS_PER_COMPETITOR", 3) or 3))
    started_at = time.monotonic()
    priority = [p.strip().lower() for p in (settings.COMPETITIVE_PROVIDER_PRIORITY or "").split(",") if p.strip()]
    if not priority:
        priority = ["playwright", "crawler", "websearch", "social", "mercadolivre", "google_shopping", "serpapi", "bellart"]
    target_competitors = _parse_competitors(concorrentes)
    all_competitors_mode = _all_competitors_requested(query)
    default_competitors = _default_scan_competitors(all_competitors_mode)
    manual_enabled = bool(getattr(settings, "COMPETITIVE_ALLOW_MANUAL", False))
    if not manual_enabled:
        priority = [p for p in priority if p != "manual"]
    else:
        manual_path = Path(settings.COMPETITIVE_MANUAL_FILE)
        manual_available = manual_path.exists() and manual_path.stat().st_size > 2
        if not manual_available:
            priority = [p for p in priority if p != "manual"]
    if not priority:
        priority = ["playwright", "crawler", "websearch", "social", "mercadolivre", "google_shopping", "serpapi", "bellart"]

    product_query = _extract_product_query(query)
    query_with_context = product_query or query
    if segmento:
        query_with_context = f"{query_with_context} {segmento}".strip()
    if concorrentes:
        query_with_context = f"{query_with_context} {concorrentes}".strip()

    generic_market_query = (product_query or query).strip()
    if segmento:
        generic_market_query = f"{generic_market_query} {segmento}".strip()

    priority, timeout, total_timeout, default_competitors = _optimize_strategy_for_query(
        priority=priority,
        target_competitors=target_competitors,
        timeout=timeout,
        total_timeout=total_timeout,
        default_competitors=default_competitors,
    )

    collected: List[Dict[str, Any]] = []
    providers_used: List[str] = []
    provider_errors: List[str] = []
    collection_cap = limit if target_competitors else min(120, max(limit * 3, 30))

    for provider in priority:
        if (time.monotonic() - started_at) > total_timeout:
            provider_errors.append("timeout_total_excedido: loop principal")
            break
        if len(collected) >= collection_cap:
            break
        try:
            remaining = max(1, collection_cap - len(collected))
            found: List[Dict[str, Any]] = []
            if provider == "mercadolivre":
                found = _search_mercadolivre(query_with_context, remaining, timeout, state, cidade)
            elif provider in {"serpapi", "google_shopping"}:
                found = _search_serpapi(query_with_context, remaining, timeout, state, cidade)
            elif provider == "playwright":
                if target_competitors:
                    for comp in target_competitors:
                        if (time.monotonic() - started_at) > total_timeout:
                            provider_errors.append("timeout_total_excedido: playwright_target")
                            break
                        if len(found) >= remaining:
                            break
                        found.extend(
                            _search_competitor_playwright(
                                comp,
                                product_query=product_query or query,
                                limit=max(1, remaining - len(found)),
                                timeout=timeout,
                                estado=state,
                                cidade=cidade,
                            )
                        )
                else:
                    for comp in default_competitors:
                        if (time.monotonic() - started_at) > total_timeout:
                            provider_errors.append("timeout_total_excedido: playwright_default")
                            break
                        if len(found) >= remaining:
                            break
                        found.extend(
                            _search_competitor_playwright(
                                comp,
                                product_query=product_query or query,
                                limit=max(1, remaining - len(found)),
                                timeout=timeout,
                                estado=state,
                                cidade=cidade,
                            )
                        )
            elif provider == "crawler":
                if target_competitors:
                    for comp in target_competitors:
                        if (time.monotonic() - started_at) > total_timeout:
                            provider_errors.append("timeout_total_excedido: crawler_target")
                            break
                        if len(found) >= remaining:
                            break
                        found.extend(
                            _search_competitor_crawler(
                                comp,
                                product_query=product_query or query,
                                limit=max(1, remaining - len(found)),
                                timeout=timeout,
                                estado=state,
                                cidade=cidade,
                            )
                        )
                else:
                    for comp in default_competitors:
                        if (time.monotonic() - started_at) > total_timeout:
                            provider_errors.append("timeout_total_excedido: crawler_default")
                            break
                        if len(found) >= remaining:
                            break
                        found.extend(
                            _search_competitor_crawler(
                                comp,
                                product_query=product_query or query,
                                limit=max(1, remaining - len(found)),
                                timeout=timeout,
                                estado=state,
                                cidade=cidade,
                            )
                        )
            elif provider == "websearch":
                # Busca por concorrente alvo sem depender de API
                if target_competitors:
                    for comp in target_competitors:
                        if (time.monotonic() - started_at) > total_timeout:
                            provider_errors.append("timeout_total_excedido: websearch_target")
                            break
                        if len(found) >= remaining:
                            break
                        found.extend(
                            _search_competitor_web(
                                comp,
                                product_query=product_query or query,
                                limit=max(1, remaining - len(found)),
                                timeout=timeout,
                                estado=state,
                                cidade=cidade,
                            )
                        )
                else:
                    # sem concorrente explícito: usa principais concorrentes digitais/varejo
                    for comp in default_competitors:
                        if (time.monotonic() - started_at) > total_timeout:
                            provider_errors.append("timeout_total_excedido: websearch_default")
                            break
                        if len(found) >= remaining:
                            break
                        found.extend(
                            _search_competitor_web(
                                comp,
                                product_query=product_query or query,
                                limit=max(1, remaining - len(found)),
                                timeout=timeout,
                                estado=state,
                                cidade=cidade,
                            )
                        )
            elif provider == "social":
                if target_competitors:
                    for comp in target_competitors:
                        if (time.monotonic() - started_at) > total_timeout:
                            provider_errors.append("timeout_total_excedido: social_target")
                            break
                        if len(found) >= remaining:
                            break
                        found.extend(
                            _search_social_competitor(
                                comp,
                                product_query=product_query or query,
                                limit=max(1, remaining - len(found)),
                                timeout=timeout,
                                estado=state,
                                cidade=cidade,
                            )
                        )
            elif provider == "bellart":
                # Só consulta Bellart direto se for alvo explícito ou não houver alvo definido.
                if (not target_competitors) or ("bellart" in target_competitors):
                    found = _search_bellart(query_with_context, remaining, timeout, state, cidade)
            elif provider == "manual":
                found = _load_manual_reference(query, segmento, state, cidade, remaining, target_competitors)

            if target_competitors and found:
                found = [f for f in found if _item_matches_competitor(f, target_competitors)]

            if found:
                providers_used.append(provider)
                collected.extend(found)
        except Exception as e:
            provider_errors.append(f"{provider}: {e}")

    validated: List[Dict[str, Any]] = []
    discarded: List[str] = []
    for candidate in collected:
        ok, reason, normalized = _quality_gate_item(candidate)
        if ok:
            validated.append(normalized)
        else:
            discarded.append(reason)

    fallback_mode_used = False
    if len(validated) == 0 and target_competitors:
        # Segunda tentativa automática: benchmark de mercado sem restringir concorrente-alvo.
        fallback_mode_used = True
        for provider in priority:
            if (time.monotonic() - started_at) > total_timeout:
                provider_errors.append("timeout_total_excedido: loop fallback")
                break
            if len(validated) >= collection_cap:
                break
            try:
                remaining = max(1, collection_cap - len(validated))
                found: List[Dict[str, Any]] = []
                if provider == "mercadolivre":
                    found = _search_mercadolivre(generic_market_query, remaining, timeout, state, cidade)
                elif provider in {"serpapi", "google_shopping"}:
                    found = _search_serpapi(generic_market_query, remaining, timeout, state, cidade)
                elif provider == "playwright":
                    for comp in ["americanas", "kalunga", "bellart", "amazon", "shopee"]:
                        if (time.monotonic() - started_at) > total_timeout:
                            provider_errors.append("timeout_total_excedido: loop_fallback_playwright")
                            break
                        if len(found) >= remaining:
                            break
                        found.extend(
                            _search_competitor_playwright(
                                comp,
                                product_query=generic_market_query,
                                limit=max(1, remaining - len(found)),
                                timeout=timeout,
                                estado=state,
                                cidade=cidade,
                            )
                        )
                elif provider == "crawler":
                    for comp in ["americanas", "kalunga", "bellart", "amazon", "shopee"]:
                        if (time.monotonic() - started_at) > total_timeout:
                            provider_errors.append("timeout_total_excedido: loop_fallback_crawler")
                            break
                        if len(found) >= remaining:
                            break
                        found.extend(
                            _search_competitor_crawler(
                                comp,
                                product_query=generic_market_query,
                                limit=max(1, remaining - len(found)),
                                timeout=timeout,
                                estado=state,
                                cidade=cidade,
                            )
                        )
                elif provider == "websearch":
                    for comp in ["americanas", "kalunga", "bellart", "amazon", "shopee"]:
                        if (time.monotonic() - started_at) > total_timeout:
                            provider_errors.append("timeout_total_excedido: loop_fallback_websearch")
                            break
                        if len(found) >= remaining:
                            break
                        found.extend(
                            _search_competitor_web(
                                comp,
                                product_query=generic_market_query,
                                limit=max(1, remaining - len(found)),
                                timeout=timeout,
                                estado=state,
                                cidade=cidade,
                            )
                        )
                elif provider == "social":
                    for comp in ["amigao", "tubarao", "tid's"]:
                        if (time.monotonic() - started_at) > total_timeout:
                            provider_errors.append("timeout_total_excedido: loop_fallback_social")
                            break
                        if len(found) >= remaining:
                            break
                        found.extend(
                            _search_social_competitor(
                                comp,
                                product_query=generic_market_query,
                                limit=max(1, remaining - len(found)),
                                timeout=timeout,
                                estado=state,
                                cidade=cidade,
                            )
                        )
                elif provider == "bellart":
                    found = _search_bellart(generic_market_query, remaining, timeout, state, cidade)
                elif provider == "manual":
                    # Sem base manual obrigatória: não depende de CSV para funcionar.
                    found = []

                for candidate in found:
                    ok, reason, normalized = _quality_gate_item(candidate)
                    if ok:
                        validated.append(normalized)
                    else:
                        discarded.append(reason)
            except (TimeoutError, OSError, ValueError, KeyError) as e:
                provider_errors.append(f"{provider}(fallback): {e}")

    total = len(validated)
    if total == 0:
        hints = _target_without_public_price_hint(target_competitors)
        if hints:
            msg = (
                "Não encontrei preço público confiável para "
                + ", ".join(hints)
                + " neste momento. "
                "Esses concorrentes geralmente não expõem catálogo de preços completo no site."
            )
            if fallback_mode_used:
                msg += " Também tentei benchmark alternativo e não houve evidência validada para este produto."
        else:
            msg = (
                "Não encontrei referências válidas após validação de evidência. "
                "Tente detalhar produto/SKU, cidade e concorrente-alvo."
            )
        if provider_errors:
            msg += " Algumas fontes externas estão indisponíveis agora."
        return {
            "status": "success",
            "mensagem": msg,
            "itens": [],
            "total_itens": 0,
            "providers_used": providers_used,
            "provider_errors": provider_errors[:3],
            "quality_gate": {
                "validated": 0,
                "discarded": len(discarded),
                "discard_reasons": discarded[:5],
                "domain_whitelist": _allowed_domains(),
                "fallback_seed_local": False,
            },
            "fontes_consultadas": _build_sources(collected),
            "consultado_em": datetime.utcnow().isoformat() + "Z",
            "metodo_consulta": "externo_sem_seed_local",
            "metodo_detalhado": "providers: " + ",".join(priority),
            "concorrentes_alvo": target_competitors,
            "fallback_benchmark_aplicado": fallback_mode_used,
        }

    # Ordena por preço quando numérico
    def _price_key(item: Dict[str, Any]) -> float:
        raw = _price_to_float(item.get("preco"))
        return float(raw) if raw is not None else float("inf")

    validated_sorted = sorted(validated, key=_price_key)
    validated = _diversify_competitor_results(
        validated_sorted,
        limit=limit,
        max_per_competitor=max_items_per_competitor,
    )
    avg_price_values = [p for p in [_price_key(i) for i in validated] if p != float("inf")]
    avg_price = round(sum(avg_price_values) / len(avg_price_values), 2) if avg_price_values else None

    return {
        "status": "success",
        "mensagem": f"Pesquisa concorrencial concluída. Referências validadas: {len(validated)}.",
        "itens": validated,
        "total_itens": len(validated),
        "preco_medio_referencia": avg_price,
        "providers_used": providers_used,
        "provider_errors": provider_errors[:3],
        "quality_gate": {
            "validated": len(validated),
            "discarded": len(discarded),
            "discard_reasons": discarded[:5],
            "domain_whitelist": _allowed_domains(),
        },
        "fontes_consultadas": _build_sources(validated),
        "consultado_em": datetime.utcnow().isoformat() + "Z",
        "metodo_consulta": "fallback_externo_playwright_crawler_websearch_social_mercadolivre_serpapi_bellart_manual",
        "metodo_detalhado": "providers: " + ",".join(priority),
        "concorrentes_alvo": target_competitors,
        "fallback_benchmark_aplicado": fallback_mode_used,
        "escopo": {
            "estado": state,
            "cidade": cidade,
            "segmento": segmento,
            "query": query,
        },
    }


# ---------------------------------------------------------------------------
# NOVA FERRAMENTA: Pesquisa de Mercado Web (aberta, sem filtro por concorrente)
# ---------------------------------------------------------------------------

def _search_duckduckgo_web(
    query: str,
    limit: int,
    timeout: int,
) -> List[Dict[str, Any]]:
    """
    Busca genérica via DuckDuckGo HTML (sem API key).
    DDG usa redirect links via //duckduckgo.com/l/?uddg=REAL_URL.
    """
    ddg_url = f"https://duckduckgo.com/html/?{urlencode({'q': query + ' preço comprar'})}"
    try:
        html = _http_get_text(ddg_url, timeout=timeout)
    except Exception as e:
        logger.warning(f"DuckDuckGo web search failed: {e}")
        return []

    results: List[Dict[str, Any]] = []
    seen: set[str] = set()

    # DDG coloca resultados em blocos com class "result results_links"
    # Cada bloco tem: H2 > a.result__a (título+link), a.result__snippet (snippet)
    # Os links reais são redirect: //duckduckgo.com/l/?uddg=ENCODED_URL

    # Extrair blocos de resultado via H2 + link redirect
    blocks = re.split(r'<h2[^>]*class="[^"]*result[^"]*"', html)

    for block in blocks[1:]:  # Pular preamble antes do primeiro resultado
        if len(results) >= limit:
            break

        # Extrair URL real via redirect DDG
        uddg_match = re.search(r'uddg=([^&"]+)', block)
        if not uddg_match:
            continue
        link = unquote(uddg_match.group(1)).strip()
        if not link.startswith("http"):
            continue
        if link in seen:
            continue
        seen.add(link)

        # Extrair título do H2 > a
        title_match = re.search(r'>(.*?)</a>', block, flags=re.DOTALL)
        title_raw = title_match.group(1) if title_match else ""
        title = re.sub(r"<[^>]+>", " ", title_raw)
        title = re.sub(r"\s+", " ", title).strip()

        # Extrair snippet
        snippet_match = re.search(
            r'class="[^"]*result__snippet[^"]*"[^>]*>(.*?)</[at]>',
            block, flags=re.IGNORECASE | re.DOTALL,
        )
        snippet_raw = snippet_match.group(1) if snippet_match else ""
        snippet = re.sub(r"<[^>]+>", " ", snippet_raw)
        snippet = re.sub(r"\s+", " ", snippet).strip()

        # Tentar extrair preço
        price_val = _extract_price_from_text(snippet) or _extract_price_from_text(title)

        domain = _extract_domain(link)

        results.append({
            "produto": title or f"Resultado em {domain}",
            "preco": price_val,
            "moeda": "BRL" if price_val else None,
            "vendedor": domain,
            "fonte": "duckduckgo_web",
            "url": link,
            "snippet": snippet[:300] if snippet else None,
        })

    return results


def _search_google_shopping_open(
    query: str,
    limit: int,
    timeout: int,
) -> List[Dict[str, Any]]:
    """
    Wrapper de _search_google_shopping_web sem restrição geográfica.
    Retorna resultados com adaptação de schema para pesquisa de mercado.
    """
    raw = _search_google_shopping_web(query, limit, timeout, estado="", cidade="")
    out: List[Dict[str, Any]] = []
    for item in raw:
        out.append({
            "produto": item.get("produto"),
            "preco": _price_to_float(item.get("preco")),
            "moeda": item.get("moeda", "BRL"),
            "vendedor": item.get("concorrente") or _extract_domain(str(item.get("url", ""))),
            "fonte": "google_shopping",
            "url": item.get("url"),
        })
    return out


def _search_mercadolivre_open(
    query: str,
    limit: int,
    timeout: int,
) -> List[Dict[str, Any]]:
    """
    Pesquisa de mercado via HTML scraping do Mercado Livre.
    A API pública (api.mercadolibre.com) exige autenticação desde 2025.
    Usa lista.mercadolivre.com.br que é público e retorna dados ricos.
    """
    # Formatar query para URL do ML (espaços viram hífens)
    slug = re.sub(r"\s+", "-", query.strip().lower())
    ml_url = f"https://lista.mercadolivre.com.br/{slug}"

    try:
        html = _http_get_text(ml_url, timeout=timeout)
    except Exception as e:
        logger.warning(f"Mercado Livre HTML scraping failed: {e}")
        return []

    out: List[Dict[str, Any]] = []

    # Extrair títulos dos produtos (class poly-component__title ou similar)
    title_blocks = re.findall(
        r'<a[^>]*class="[^"]*poly-component__title[^"]*"[^>]*>(.*?)</a>',
        html, flags=re.DOTALL | re.IGNORECASE,
    )
    if not title_blocks:
        # Fallback: h2 com class title
        title_blocks = re.findall(
            r'<h2[^>]*>(.*?)</h2>',
            html, flags=re.DOTALL | re.IGNORECASE,
        )

    # Extrair preços (andes-money-amount__fraction)
    prices_raw = re.findall(
        r'class="andes-money-amount__fraction"[^>]*>([0-9.]+)</span>',
        html, flags=re.IGNORECASE,
    )

    # Extrair URLs dos produtos
    product_urls = re.findall(
        r'<a[^>]*href="(https://[^"]*mercadolivre\.com\.br/[^"]*MLB[^"]+)"',
        html, flags=re.IGNORECASE,
    )
    # Deduplicar URLs mantendo ordem
    seen_urls: list[str] = []
    for u in product_urls:
        u_clean = u.split("?")[0]  # Remover query params
        if u_clean not in seen_urls:
            seen_urls.append(u_clean)

    for i in range(min(limit, len(title_blocks))):
        title_raw = title_blocks[i]
        title = re.sub(r"<[^>]+>", " ", title_raw)
        title = re.sub(r"\s+", " ", title).strip()
        if not title:
            continue

        price = None
        if i < len(prices_raw):
            try:
                price = float(prices_raw[i].replace(".", ""))
            except (ValueError, TypeError):
                pass

        url = seen_urls[i] if i < len(seen_urls) else ""

        out.append({
            "produto": title,
            "preco": price,
            "moeda": "BRL",
            "vendedor": "Mercado Livre",
            "fonte": "mercadolivre",
            "url": url,
        })

    return out


def _search_mercadolivre_market(
    query: str,
    limit: int,
    timeout: int,
) -> List[Dict[str, Any]]:
    """
    Provider prioritário de Mercado Livre para pesquisa de mercado aberta.
    Tenta API pública primeiro (mais estável e volumosa) e faz fallback para HTML.
    """
    try:
        api_rows = _search_mercadolivre(query, limit, timeout, estado="", cidade="")
    except Exception:
        api_rows = []

    out: List[Dict[str, Any]] = []
    for item in api_rows[:limit]:
        out.append(
            {
                "produto": item.get("produto"),
                "preco": _price_to_float(item.get("preco")),
                "moeda": item.get("moeda", "BRL"),
                "vendedor": "Mercado Livre",
                "fonte": "mercadolivre_api",
                "url": item.get("url"),
            }
        )
    if out:
        return out

    return _search_mercadolivre_open(query, limit, timeout)


def _collect_market_competitors(items: List[Dict[str, Any]]) -> List[str]:
    competitors: List[str] = []
    for item in items:
        name = str(item.get("concorrente") or "").strip()
        if not name:
            continue
        if name not in competitors:
            competitors.append(name)
    return competitors


def _expand_market_competitor_coverage(
    product_query: str,
    validated: List[Dict[str, Any]],
    seen_urls: set[str],
    collection_cap: int,
    timeout: int,
    started_at: float,
    total_timeout: int,
) -> tuple[bool, List[str]]:
    """
    Quando a pesquisa aberta fica concentrada em poucos concorrentes, tenta ampliar
    cobertura com busca direta por concorrentes relevantes.
    """
    min_competitors = max(1, int(getattr(settings, "COMPETITIVE_MARKET_MIN_COMPETITORS", 3) or 3))
    current_competitors = _collect_market_competitors(validated)
    if len(current_competitors) >= min_competitors:
        return False, []

    errors: List[str] = []
    added_any = False
    current_keys = {_normalize_text(name).replace(" ", "") for name in current_competitors}
    fallback_candidates = [c for c in _default_scan_competitors(True) if c != "mercado livre"]
    local_timeout = max(2, min(timeout, 6))

    for competitor in fallback_candidates:
        if (time.monotonic() - started_at) >= total_timeout:
            errors.append("timeout_total_excedido: fallback_multi_competidor")
            break
        if len(validated) >= collection_cap:
            break
        if len(_collect_market_competitors(validated)) >= min_competitors:
            break

        display_name = _normalize_competitor_display_name(competitor)
        display_key = _normalize_text(display_name).replace(" ", "")
        if display_key and display_key in current_keys:
            continue

        try:
            rows = _search_competitor_web(
                competitor=competitor,
                product_query=product_query,
                limit=2,
                timeout=local_timeout,
                estado="",
                cidade="",
            )
        except Exception as exc:
            errors.append(f"fallback_competitor_web:{competitor}:{exc}")
            continue

        for row in rows:
            if len(validated) >= collection_cap:
                break
            url = str(row.get("url") or "").strip()
            produto = str(row.get("produto") or "").strip()
            if not produto:
                continue
            if url and url in seen_urls:
                continue
            if url:
                seen_urls.add(url)

            competitor_name = _infer_market_competitor(
                {
                    "vendedor": row.get("concorrente"),
                    "fonte": row.get("fonte"),
                },
                url,
            )
            validated.append(
                {
                    "concorrente": competitor_name,
                    "produto": produto,
                    "preco": row.get("preco"),
                    "moeda": row.get("moeda") or "BRL",
                    "fonte": row.get("fonte", "websearch_competitor"),
                    "url": url,
                    "estado": "",
                    "cidade": "",
                    "target_competitor": competitor_name,
                }
            )
            current_keys.add(_normalize_text(competitor_name).replace(" ", ""))
            added_any = True

    return added_any, errors


def _search_serpapi_open(
    query: str,
    limit: int,
    timeout: int,
) -> List[Dict[str, Any]]:
    """
    SerpAPI para pesquisa de mercado aberta (Shopping + orgânica).
    Retorna [] se SERPAPI_API_KEY não estiver configurada.
    """
    api_key = (settings.SERPAPI_API_KEY or "").strip()
    if not api_key:
        return []

    # Tenta Google Shopping primeiro
    payload = _http_get_json(
        "https://serpapi.com/search.json",
        {
            "engine": "google_shopping",
            "q": query,
            "api_key": api_key,
            "hl": "pt-br",
            "gl": "br",
            "num": limit,
        },
        timeout=timeout,
    )
    items = payload.get("shopping_results", []) if isinstance(payload, dict) else []
    out: List[Dict[str, Any]] = []

    def _serpapi_url(row: Dict[str, Any]) -> str:
        for key in ("link", "product_link", "shopping_link", "offer_link", "serpapi_link"):
            value = str(row.get(key) or "").strip()
            if value:
                return value
        return ""

    for item in items[:limit]:
        if not isinstance(item, dict):
            continue
        price = item.get("extracted_price")
        if price is None:
            price = _price_to_float(item.get("price", ""))
        out.append({
            "produto": item.get("title"),
            "preco": price,
            "moeda": "BRL",
            "vendedor": item.get("source") or item.get("store_name") or "Google Shopping",
            "fonte": "serpapi_shopping",
            "url": _serpapi_url(item),
            "thumbnail": item.get("thumbnail"),
        })
    return out


@tool
def pesquisar_mercado_web(
    termo_pesquisa: str,
    limite: str = "15",
) -> Dict[str, Any]:
    """
    Pesquisa de mercado EXTERNA para encontrar produtos, preços e fornecedores na internet.

    USE QUANDO:
    - Usuário pedir "pesquisa de mercado" de qualquer produto.
    - Usuário perguntar "quanto custa X no mercado?", "onde comprar X?".
    - Usuário pedir cotação ou comparação de preços FORA da base interna.
    - Qualquer busca por produtos em marketplaces, e-commerces ou lojas online.

    NÃO USE QUANDO:
    - O usuário quiser analisar dados INTERNOS de vendas/estoque (use consultar_dados_flexivel).
    - O usuário quiser comparar com concorrentes ESPECÍFICOS da Caçula (use pesquisar_precos_concorrentes).

    PARÂMETROS:
    - termo_pesquisa: nome do produto a pesquisar (ex: "fita adesiva 45x45", "cola bastão 40g")
    - limite: quantidade máxima de resultados (string numérica, default "15")
    """
    query = (termo_pesquisa or "").strip()
    if not query:
        return {
            "status": "error",
            "error": "Informe o produto/termo para pesquisa de mercado.",
        }

    # Limpar query de comandos conversacionais
    clean_query = _extract_product_query(query)
    if not clean_query:
        clean_query = query

    try:
        limit = max(1, min(int(str(limite or "15").strip()), 50))
    except (TypeError, ValueError):
        limit = 15

    timeout = max(3, int(settings.COMPETITIVE_HTTP_TIMEOUT_SEC or 10))
    total_timeout = max(timeout * 3, 30)
    started_at = time.monotonic()

    all_results: List[Dict[str, Any]] = []
    sources_used: List[str] = []
    source_errors: List[str] = []

    collection_cap = min(120, max(limit * 3, 30))
    provider_budget_base = max(5, min(20, limit))
    provider_steps = [
        ("mercadolivre", _search_mercadolivre_market),
        ("google_shopping", _search_google_shopping_open),
        ("serpapi", _search_serpapi_open),
        ("duckduckgo", _search_duckduckgo_web),
    ]

    for provider_name, provider_fn in provider_steps:
        if (time.monotonic() - started_at) >= total_timeout:
            source_errors.append("timeout_total_excedido: pesquisa_mercado_web")
            break
        if len(all_results) >= collection_cap:
            break

        provider_budget = min(provider_budget_base, collection_cap - len(all_results))
        provider_budget = max(1, provider_budget)
        try:
            provider_results = provider_fn(clean_query, provider_budget, timeout)
            if provider_results:
                all_results.extend(provider_results)
                sources_used.append(provider_name)
                logger.info(f"[MARKET_SEARCH] {provider_name}: {len(provider_results)} resultados")
        except Exception as e:
            source_errors.append(f"{provider_name}: {e}")
            logger.warning(f"[MARKET_SEARCH] {provider_name} falhou: {e}")

    # --- Quality gate simplificada (aceita produto + URL, preço opcional) ---
    validated: List[Dict[str, Any]] = []
    discarded_count = 0
    seen_urls: set[str] = set()
    for item in all_results:
        url = str(item.get("url") or "").strip()
        produto = str(item.get("produto") or "").strip()
        if not produto:
            discarded_count += 1
            continue
        # Deduplicar por URL
        if url and url in seen_urls:
            discarded_count += 1
            continue
        if url:
            seen_urls.add(url)
        competitor = _infer_market_competitor(item, url)
        # Padronizar schema do item para compatibilidade com pesquisar_precos_concorrentes
        validated.append({
            "concorrente": competitor,
            "produto": produto,
            "preco": item.get("preco"),
            "moeda": item.get("moeda") or "BRL",
            "fonte": item.get("fonte", "web"),
            "url": url,
            "estado": "",
            "cidade": "",
            "target_competitor": competitor,
        })
        if len(validated) >= collection_cap:
            break

    expanded_coverage, coverage_errors = _expand_market_competitor_coverage(
        product_query=clean_query,
        validated=validated,
        seen_urls=seen_urls,
        collection_cap=collection_cap,
        timeout=timeout,
        started_at=started_at,
        total_timeout=total_timeout,
    )
    if expanded_coverage and "competitor_web_fallback" not in sources_used:
        sources_used.append("competitor_web_fallback")
    if coverage_errors:
        source_errors.extend(coverage_errors[:3])

    # --- Ordenar por preço (itens com preço primeiro) ---
    def _sort_key(item: Dict[str, Any]) -> tuple:
        price = _price_to_float(item.get("preco"))
        has_price = 0 if price is not None else 1
        return (has_price, price if price is not None else float("inf"))

    validated = sorted(validated, key=_sort_key)
    max_items_per_competitor = max(1, int(getattr(settings, "COMPETITIVE_MAX_ITEMS_PER_COMPETITOR", 3) or 3))
    validated = _diversify_competitor_results(
        validated,
        limit=limit,
        max_per_competitor=max_items_per_competitor,
    )

    competitors_identified: List[str] = []
    for item in validated:
        competitor = str(item.get("concorrente") or "").strip()
        if competitor and competitor not in competitors_identified:
            competitors_identified.append(competitor)
    min_competitors = max(1, int(getattr(settings, "COMPETITIVE_MARKET_MIN_COMPETITORS", 3) or 3))
    coverage_summary = {
        "identificados": len(competitors_identified),
        "meta_minima": min_competitors,
        "atingida": len(competitors_identified) >= min_competitors,
    }

    # --- Calcular estatísticas de preço ---
    prices = [_price_to_float(i.get("preco")) for i in validated]
    valid_prices = [p for p in prices if p is not None and p > 0]
    stats: Dict[str, Any] = {}
    if valid_prices:
        stats = {
            "preco_minimo": round(min(valid_prices), 2),
            "preco_maximo": round(max(valid_prices), 2),
            "preco_medio": round(sum(valid_prices) / len(valid_prices), 2),
            "total_com_preco": len(valid_prices),
        }

    elapsed = round(time.monotonic() - started_at, 1)

    if not validated:
        return {
            "status": "success",
            "mensagem": (
                f"Não encontrei resultados para '{clean_query}' nas fontes consultadas. "
                "Tente refinar o nome do produto ou usar termos mais específicos."
            ),
            "itens": [],
            "total_itens": 0,
            "providers_used": sources_used,
            "provider_errors": source_errors[:3],
            "quality_gate": {
                "validated": 0,
                "discarded": discarded_count,
                "discard_reasons": [],
                "tipo": "mercado_aberto",
            },
            "fontes_consultadas": sources_used,
            "consultado_em": datetime.utcnow().isoformat() + "Z",
            "metodo_consulta": "pesquisa_mercado_web",
            "metodo_detalhado": f"providers: {','.join(sources_used) or 'nenhum'}",
            "concorrentes_alvo": [],
            "concorrentes_identificados": [],
            "cobertura_concorrentes": {
                "identificados": 0,
                "meta_minima": min_competitors,
                "atingida": False,
            },
            "fallback_benchmark_aplicado": False,
            "termo_pesquisado": clean_query,
            "estatisticas_preco": stats or None,
            "tempo_busca_segundos": elapsed,
        }

    return {
        "status": "success",
        "mensagem": f"Pesquisa de mercado concluída para '{clean_query}'. {len(validated)} resultados encontrados.",
        "itens": validated,
        "total_itens": len(validated),
        "providers_used": sources_used,
        "provider_errors": source_errors[:3] if source_errors else [],
        "quality_gate": {
            "validated": len(validated),
            "discarded": discarded_count,
            "discard_reasons": [],
            "tipo": "mercado_aberto",
        },
        "fontes_consultadas": sources_used,
        "consultado_em": datetime.utcnow().isoformat() + "Z",
        "metodo_consulta": "pesquisa_mercado_web",
        "metodo_detalhado": f"providers: {','.join(sources_used)}",
        "concorrentes_alvo": [],
        "concorrentes_identificados": competitors_identified,
        "cobertura_concorrentes": coverage_summary,
        "fallback_benchmark_aplicado": False,
        "termo_pesquisado": clean_query,
        "estatisticas_preco": stats or None,
        "tempo_busca_segundos": elapsed,
    }
