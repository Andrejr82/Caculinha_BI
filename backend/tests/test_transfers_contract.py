import pytest
from types import SimpleNamespace

from backend.app.api.v1.endpoints import transfers


def _payload(client_request_id: str):
    return transfers.BulkTransferRequestPayload(
        modo="1->N",
        client_request_id=client_request_id,
        items=[
            transfers.TransferRequestPayload(
                produto_id=100001,
                une_origem=102,
                une_destino=205,
                quantidade=3,
                solicitante_id="frontend",
            )
        ],
    )


@pytest.mark.asyncio
async def test_bulk_transfer_returns_official_protocol(tmp_path, monkeypatch):
    monkeypatch.setattr(transfers, "TRANSFER_REQUESTS_DIR", tmp_path)

    result = await transfers.create_bulk_transfer_request(
        _payload("ADMAT-REQ-001"),
        SimpleNamespace(username="compras_user"),
    )

    assert result["protocol"].startswith("TRF-")
    assert result["status"] == "SOLICITADA_POR_COMPRAS"
    assert result["idempotent_replay"] is False

    files = list(tmp_path.glob("*.json"))
    assert len(files) == 1
    saved = files[0].read_text(encoding="utf-8")
    assert "ADMAT-REQ-001" in saved
    assert result["protocol"] in saved


@pytest.mark.asyncio
async def test_bulk_transfer_is_idempotent_by_client_request_id(tmp_path, monkeypatch):
    monkeypatch.setattr(transfers, "TRANSFER_REQUESTS_DIR", tmp_path)

    first = await transfers.create_bulk_transfer_request(
        _payload("ADMAT-REQ-002"),
        SimpleNamespace(username="compras_user"),
    )
    second = await transfers.create_bulk_transfer_request(
        _payload("ADMAT-REQ-002"),
        SimpleNamespace(username="compras_user"),
    )

    assert second["protocol"] == first["protocol"]
    assert second["batch_id"] == first["batch_id"]
    assert second["idempotent_replay"] is True
    assert len(list(tmp_path.glob("*.json"))) == 1
