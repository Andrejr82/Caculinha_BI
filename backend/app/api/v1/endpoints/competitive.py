"""
Competitive Intelligence Endpoints
Upload de cotações CSV para base manual da pesquisa concorrencial.
"""

from __future__ import annotations

import json
from datetime import datetime
from io import StringIO
from pathlib import Path
from typing import Annotated, Any

import pandas as pd
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from backend.app.api.dependencies import require_admin
from backend.app.config.settings import settings
from backend.app.infrastructure.database.models import User

router = APIRouter(prefix="/competitive", tags=["Competitive Intelligence"])


class CompetitiveImportResult(BaseModel):
    status: str
    imported_rows: int
    file_name: str
    target_file: str
    mode: str
    imported_at: str


def _normalize_col(name: str) -> str:
    return (name or "").strip().lower().replace(" ", "_")


def _to_optional_float(value: Any) -> float | None:
    if value is None:
        return None
    txt = str(value).strip()
    if not txt:
        return None
    txt = txt.replace("R$", "").replace(" ", "").replace(".", "").replace(",", ".")
    try:
        return float(txt)
    except Exception:
        return None


@router.get("/csv-template")
async def get_competitive_csv_template(
    current_user: Annotated[User, Depends(require_admin)],
):
    return {
        "columns": [
            "concorrente",
            "segmento",
            "estado",
            "cidade",
            "produto",
            "descricao",
            "preco",
            "moeda",
            "fonte",
            "url",
        ],
        "example": {
            "concorrente": "KALUNGA",
            "segmento": "PAPELARIA",
            "estado": "RJ",
            "cidade": "Rio de Janeiro",
            "produto": "Caderno Universitário 10 matérias",
            "descricao": "Caderno capa dura",
            "preco": "29,90",
            "moeda": "BRL",
            "fonte": "coleta_manual_compras",
            "url": "https://exemplo.com/produto",
        },
    }


@router.post("/import-csv", response_model=CompetitiveImportResult)
async def import_competitive_csv(
    current_user: Annotated[User, Depends(require_admin)],
    file: UploadFile = File(...),
    replace_existing: bool = Form(default=False),
):
    filename = file.filename or "upload.csv"
    if not filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Arquivo inválido. Envie um CSV.")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="CSV vazio.")

    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        text = content.decode("latin-1")

    try:
        df = pd.read_csv(StringIO(text), sep=None, engine="python")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Falha ao ler CSV: {e}")

    if df.empty:
        raise HTTPException(status_code=400, detail="CSV sem linhas.")

    col_map = {_normalize_col(c): c for c in df.columns}
    aliases = {
        "concorrente": ["concorrente", "loja", "fornecedor"],
        "segmento": ["segmento", "categoria", "nicho"],
        "estado": ["estado", "uf"],
        "cidade": ["cidade", "municipio", "município"],
        "produto": ["produto", "sku", "item"],
        "descricao": ["descricao", "descrição", "nome"],
        "preco": ["preco", "preço", "valor"],
        "moeda": ["moeda", "currency"],
        "fonte": ["fonte", "origem"],
        "url": ["url", "link"],
    }

    def get_value(row: pd.Series, target: str) -> Any:
        for alias in aliases[target]:
            col = col_map.get(_normalize_col(alias))
            if col is not None:
                return row.get(col)
        return ""

    records = []
    for _, row in df.iterrows():
        concorrente = str(get_value(row, "concorrente") or "").strip()
        if not concorrente:
            continue
        record = {
            "concorrente": concorrente,
            "segmento": str(get_value(row, "segmento") or "").strip().upper(),
            "estado": str(get_value(row, "estado") or "").strip().upper(),
            "cidade": str(get_value(row, "cidade") or "").strip(),
            "produto": str(get_value(row, "produto") or "").strip(),
            "descricao": str(get_value(row, "descricao") or "").strip(),
            "preco": _to_optional_float(get_value(row, "preco")),
            "moeda": str(get_value(row, "moeda") or "BRL").strip().upper(),
            "fonte": str(get_value(row, "fonte") or "csv_compras").strip(),
            "url": str(get_value(row, "url") or "").strip(),
        }
        records.append(record)

    if not records:
        raise HTTPException(status_code=400, detail="Nenhuma linha válida encontrada no CSV.")

    target = Path(settings.COMPETITIVE_MANUAL_FILE)
    target.parent.mkdir(parents=True, exist_ok=True)
    existing: list[dict[str, Any]] = []
    if target.exists() and not replace_existing:
        try:
            loaded = json.loads(target.read_text(encoding="utf-8"))
            if isinstance(loaded, list):
                existing = loaded
        except Exception:
            existing = []

    final_records = records if replace_existing else (existing + records)
    target.write_text(json.dumps(final_records, ensure_ascii=False, indent=2), encoding="utf-8")

    return CompetitiveImportResult(
        status="success",
        imported_rows=len(records),
        file_name=filename,
        target_file=str(target),
        mode="replace" if replace_existing else "append",
        imported_at=datetime.utcnow().isoformat() + "Z",
    )

