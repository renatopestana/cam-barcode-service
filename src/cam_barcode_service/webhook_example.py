"""Servidor FastAPI de exemplo para consumir leituras via Webhook HTTP."""

from __future__ import annotations

from typing import Any, Optional


def create_app() -> Any:
    try:
        from fastapi import FastAPI
        from pydantic import BaseModel
    except ImportError as exc:
        raise RuntimeError(
            "O servidor de exemplo requer FastAPI e Uvicorn. Instale com: "
            "pip install 'cam-barcode-service[server]'"
        ) from exc

    app = FastAPI(
        title="cam-barcode-service Webhook Receiver",
        description="Exemplo de API local que recebe leituras do serviço de câmera.",
        version="1.0.0",
    )

    class ProductPayload(BaseModel):
        code: int
        name: str
        price_kg: float

    class BarcodePayload(BaseModel):
        raw: str
        layout: str
        check_ok: bool
        is_scale_label: bool
        prefix: str
        plu: int
        plu_str: str
        const: str
        value_str: str
        check_digit: str
        price: Optional[float] = None
        weight: Optional[float] = None
        product: Optional[ProductPayload] = None

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/api/v1/barcode/webhook")
    async def receive_barcode(payload: BarcodePayload) -> dict[str, Any]:
        print(
            f"[WEBHOOK] EAN-13={payload.raw} | PLU={payload.plu} | "
            f"Preço={payload.price} | Peso={payload.weight}"
        )
        return {"status": "received", "raw": payload.raw, "plu": payload.plu}

    return app


def run_server(host: str = "127.0.0.1", port: int = 8000) -> int:
    try:
        import uvicorn
    except ImportError as exc:
        raise RuntimeError(
            "Instale as dependências do servidor com: pip install 'cam-barcode-service[server]'"
        ) from exc

    app = create_app()
    uvicorn.run(app, host=host, port=port)
    return 0
