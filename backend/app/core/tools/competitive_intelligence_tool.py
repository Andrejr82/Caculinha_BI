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
from urllib.parse import urlencode, urlparse
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

SEED_PRICE_REFERENCES = [
    {
        "pattern": r"fita\s+adesiva\s+45x45",
        "produto": "Fita adesiva 45x45",
        "preco": 10.49,
    },
]


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


def _local_seed_reference(
    query: str,
    competitors: List[str],
    estado: str,
    cidade: str,
    limit: int,
) -> List[Dict[str, Any]]:
    q = _normalize_text(query)
    out: List[Dict[str, Any]] = []
    for seed in SEED_PRICE_REFERENCES:
        if len(out) >= limit:
            break
        pattern = seed.get("pattern", "")
        if pattern and not re.search(pattern, q, flags=re.IGNORECASE):
            continue
        comp = competitors[0] if competitors else "benchmark_mercado"
        out.append(
            {
                "concorrente": comp,
                "produto": seed.get("produto") or "Referência de mercado",
                "preco": float(seed.get("preco") or 0),
                "moeda": "BRL",
                "fonte": "benchmark_seed_local",
                "url": "",
                "estado": estado,
                "cidade": cidade,
                "dominio": "manual",
                "disponibilidade": "estimativa_operacional",
            }
        )
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


def _extract_product_query(raw: str) -> str:
    """Tenta reduzir pergunta livre para termo de produto pesquisável."""
    q = (raw or "").strip()
    if not q:
        return ""
    q_low = _normalize_text(q)
    # Remove prefixos comuns de comando
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
    # Mantém parte antes de " para ..." (normalmente onde está o concorrente-alvo)
    if " para " in q_low:
        q_low = q_low.split(" para ", 1)[0].strip()
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
    - para base manual, URL é opcional (evidência é a própria planilha de compras)
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
    if not is_manual:
        if not url:
            return False, "url_ausente", item
        if source == "websearch_competitor":
            target_comp = _normalize_text(str(item.get("target_competitor") or ""))
            tokens = _brand_tokens(target_comp) if target_comp else []
            compact_domain = domain.replace(".", "")
            brand_ok = any(t in compact_domain for t in tokens if t)
            if not (_domain_allowed(url) or brand_ok):
                return False, f"dominio_nao_confere_competidor:{domain or 'desconhecido'}", item
        else:
            if not _domain_allowed(url):
                return False, f"dominio_nao_whitelist:{domain or 'desconhecido'}", item

    normalized = dict(item)
    normalized["preco"] = price_num
    normalized["dominio"] = domain if domain else ("manual" if is_manual else "")
    normalized["disponibilidade"] = normalized.get("disponibilidade") or "nao_validada"
    return True, "ok", normalized


def _http_get_json(url: str, params: Dict[str, Any], timeout: int) -> Dict[str, Any]:
    encoded = urlencode(params, doseq=True)
    full_url = f"{url}?{encoded}" if encoded else url
    req = Request(
        full_url,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; CaculinhaBot/1.0; +https://www.lojascacula.com.br)",
            "Accept": "application/json,text/plain,*/*",
        },
    )
    with urlopen(req, timeout=timeout) as resp:  # nosec B310 - URL controlado por código
        body = resp.read().decode("utf-8", errors="ignore")
    try:
        return json.loads(body)
    except Exception:
        return {}


def _http_get_text(url: str, timeout: int) -> str:
    req = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; CaculinhaBot/1.0; +https://www.lojascacula.com.br)"
        },
    )
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
    for profile in profiles:
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
    if domains:
        query = f"{product_query} site:{domains[0]}"
    else:
        query = f"{product_query} {competitor}"

    ddg_url = f"https://duckduckgo.com/html/?{urlencode({'q': query})}"
    html = _http_get_text(ddg_url, timeout=timeout)
    links = re.findall(r'<a[^>]+class="[^"]*result__a[^"]*"[^>]+href="([^"]+)"', html, flags=re.IGNORECASE)
    if not links:
        links = re.findall(r'<a[^>]+href="(https?://[^"]+)"', html, flags=re.IGNORECASE)

    results: List[Dict[str, Any]] = []
    seen: set[str] = set()
    for link in links:
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
    query = f"{product_query} site:{domains[0]}" if domains else f"{product_query} {competitor}"
    ddg_url = f"https://duckduckgo.com/html/?{urlencode({'q': query})}"

    results: List[Dict[str, Any]] = []
    seen: set[str] = set()
    timeout_ms = max(2000, timeout * 1000)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(ddg_url, timeout=timeout_ms, wait_until="domcontentloaded")
            anchors = page.eval_on_selector_all(
                "a.result__a",
                "els => els.map(el => ({href: el.href || '', title: (el.textContent||'').trim()}))",
            )

            for row in anchors:
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


def _search_serpapi(
    query: str,
    limit: int,
    timeout: int,
    estado: str,
    cidade: str,
) -> List[Dict[str, Any]]:
    api_key = (settings.SERPAPI_API_KEY or "").strip()
    if not api_key:
        return []

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
                "url": item.get("link"),
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
    started_at = time.monotonic()
    priority = [p.strip().lower() for p in (settings.COMPETITIVE_PROVIDER_PRIORITY or "").split(",") if p.strip()]
    if not priority:
        priority = ["playwright", "crawler", "websearch", "social", "mercadolivre", "serpapi", "bellart"]
    target_competitors = _parse_competitors(concorrentes)
    manual_path = Path(settings.COMPETITIVE_MANUAL_FILE)
    manual_available = manual_path.exists() and manual_path.stat().st_size > 2
    if not manual_available:
        priority = [p for p in priority if p != "manual"]
    if not priority:
        priority = ["playwright", "crawler", "websearch", "social", "mercadolivre", "serpapi", "bellart"]

    product_query = _extract_product_query(query)
    query_with_context = product_query or query
    if segmento:
        query_with_context = f"{query_with_context} {segmento}".strip()
    if concorrentes:
        query_with_context = f"{query_with_context} {concorrentes}".strip()

    generic_market_query = (product_query or query).strip()
    if segmento:
        generic_market_query = f"{generic_market_query} {segmento}".strip()

    # Quando há concorrente-alvo, priorizar fontes com identificação de loja.
    if target_competitors:
        preferred = ["playwright", "crawler", "websearch", "social", "serpapi", "bellart", "manual", "mercadolivre"]
        priority = [p for p in preferred if p in priority] + [p for p in priority if p not in preferred]

    collected: List[Dict[str, Any]] = []
    providers_used: List[str] = []
    provider_errors: List[str] = []

    for provider in priority:
        if (time.monotonic() - started_at) > total_timeout:
            provider_errors.append("timeout_total_excedido: loop principal")
            break
        if len(collected) >= limit:
            break
        try:
            remaining = max(1, limit - len(collected))
            found: List[Dict[str, Any]] = []
            if provider == "mercadolivre":
                found = _search_mercadolivre(query_with_context, remaining, timeout, state, cidade)
            elif provider == "serpapi":
                found = _search_serpapi(query_with_context, remaining, timeout, state, cidade)
            elif provider == "playwright":
                if target_competitors:
                    for comp in target_competitors:
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
                    for comp in ["americanas", "kalunga", "bellart"]:
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
                    for comp in ["americanas", "kalunga", "bellart"]:
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
                    for comp in ["americanas", "kalunga", "bellart"]:
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
            if len(validated) >= limit:
                break
            try:
                remaining = max(1, limit - len(validated))
                found: List[Dict[str, Any]] = []
                if provider == "mercadolivre":
                    found = _search_mercadolivre(generic_market_query, remaining, timeout, state, cidade)
                elif provider == "serpapi":
                    found = _search_serpapi(generic_market_query, remaining, timeout, state, cidade)
                elif provider == "playwright":
                    for comp in ["americanas", "kalunga", "bellart", "amazon", "shopee"]:
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
            except Exception as e:
                provider_errors.append(f"{provider}(fallback): {e}")

    total = len(validated)
    if total == 0:
        seed_items = _local_seed_reference(query, target_competitors, state, cidade, limit)
        if seed_items:
            return {
                "status": "success",
                "mensagem": (
                    "Sem evidência externa validada no momento. "
                    "Retornando referência operacional estimada para não interromper a análise."
                ),
                "itens": seed_items,
                "total_itens": len(seed_items),
                "preco_medio_referencia": seed_items[0].get("preco"),
                "providers_used": providers_used,
                "provider_errors": provider_errors[:3],
                "quality_gate": {
                    "validated": 0,
                    "discarded": len(discarded),
                    "discard_reasons": discarded[:5],
                    "domain_whitelist": _allowed_domains(),
                    "fallback_seed_local": True,
                },
                "fontes_consultadas": _build_sources(seed_items),
                "consultado_em": datetime.utcnow().isoformat() + "Z",
                "metodo_consulta": "fallback_seed_local",
                "metodo_detalhado": "providers: " + ",".join(priority),
                "concorrentes_alvo": target_competitors,
                "fallback_benchmark_aplicado": True,
                "escopo": {
                    "estado": state,
                    "cidade": cidade,
                    "segmento": segmento,
                    "query": query,
                },
            }

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
            },
            "fontes_consultadas": _build_sources(collected),
            "consultado_em": datetime.utcnow().isoformat() + "Z",
            "metodo_consulta": "fallback_externo_playwright_crawler_websearch_social_mercadolivre_serpapi_bellart_manual",
            "metodo_detalhado": "providers: " + ",".join(priority),
            "concorrentes_alvo": target_competitors,
            "fallback_benchmark_aplicado": fallback_mode_used,
        }

    # Ordena por preço quando numérico
    def _price_key(item: Dict[str, Any]) -> float:
        raw = _price_to_float(item.get("preco"))
        return float(raw) if raw is not None else float("inf")

    validated = sorted(validated, key=_price_key)[:limit]
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


