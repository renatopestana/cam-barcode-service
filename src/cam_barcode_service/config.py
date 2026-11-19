"""Modelos e carregamento de configuração do serviço."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional


@dataclass
class CameraConfig:
    id: int = 0
    width: int = 640
    height: int = 480
    backend: str = "auto"
    skip_frames: int = 1
    loop_sleep_seconds: float = 0.03


@dataclass
class ParserConfig:
    layout: str = "plataforma5"
    products_csv: Optional[str] = None
    only_valid_ean13: bool = True


@dataclass
class ConsoleOutputConfig:
    enabled: bool = True


@dataclass
class KeyboardOutputConfig:
    enabled: bool = False
    suffix_key: Optional[str] = "enter"
    interval_seconds: float = 0.0
    failsafe: bool = True


@dataclass
class WebhookOutputConfig:
    enabled: bool = False
    url: str = "http://127.0.0.1:8000/api/v1/barcode/webhook"
    timeout_seconds: float = 1.5
    headers: dict[str, str] = field(default_factory=dict)


@dataclass
class CsvLogOutputConfig:
    enabled: bool = False
    path: str = "leituras.csv"


@dataclass
class OutputsConfig:
    console: ConsoleOutputConfig = field(default_factory=ConsoleOutputConfig)
    keyboard: KeyboardOutputConfig = field(default_factory=KeyboardOutputConfig)
    webhook: WebhookOutputConfig = field(default_factory=WebhookOutputConfig)
    csv_log: CsvLogOutputConfig = field(default_factory=CsvLogOutputConfig)


@dataclass
class AppConfig:
    camera: CameraConfig = field(default_factory=CameraConfig)
    parser: ParserConfig = field(default_factory=ParserConfig)
    cooldown_seconds: float = 3.0
    outputs: OutputsConfig = field(default_factory=OutputsConfig)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AppConfig:
        cam_d = data.get("camera", {})
        par_d = data.get("parser", {})
        out_d = data.get("outputs", {})

        return cls(
            camera=CameraConfig(
                id=int(cam_d.get("id", 0)),
                width=int(cam_d.get("width", 640)),
                height=int(cam_d.get("height", 480)),
                backend=str(cam_d.get("backend", "auto")),
                skip_frames=max(1, int(cam_d.get("skip_frames", 1))),
                loop_sleep_seconds=float(cam_d.get("loop_sleep_seconds", 0.03)),
            ),
            parser=ParserConfig(
                layout=str(par_d.get("layout", "plataforma5")),
                products_csv=par_d.get("products_csv"),
                only_valid_ean13=bool(par_d.get("only_valid_ean13", True)),
            ),
            cooldown_seconds=float(data.get("cooldown_seconds", 3.0)),
            outputs=OutputsConfig(
                console=ConsoleOutputConfig(
                    enabled=bool(out_d.get("console", {}).get("enabled", True)),
                ),
                keyboard=KeyboardOutputConfig(
                    enabled=bool(out_d.get("keyboard", {}).get("enabled", False)),
                    suffix_key=out_d.get("keyboard", {}).get("suffix_key", "enter"),
                    interval_seconds=float(
                        out_d.get("keyboard", {}).get("interval_seconds", 0.0)
                    ),
                    failsafe=bool(out_d.get("keyboard", {}).get("failsafe", True)),
                ),
                webhook=WebhookOutputConfig(
                    enabled=bool(out_d.get("webhook", {}).get("enabled", False)),
                    url=str(
                        out_d.get("webhook", {}).get(
                            "url", "http://127.0.0.1:8000/api/v1/barcode/webhook"
                        )
                    ),
                    timeout_seconds=float(
                        out_d.get("webhook", {}).get("timeout_seconds", 1.5)
                    ),
                    headers=dict(out_d.get("webhook", {}).get("headers", {})),
                ),
                csv_log=CsvLogOutputConfig(
                    enabled=bool(out_d.get("csv_log", {}).get("enabled", False)),
                    path=str(out_d.get("csv_log", {}).get("path", "leituras.csv")),
                ),
            ),
        )


def load_config(path: Optional[Path] = None) -> AppConfig:
    """Carrega AppConfig de um arquivo JSON; se omitido, retorna defaults."""
    if path is None:
        return AppConfig()
    if not path.exists():
        raise FileNotFoundError(f"Arquivo de configuração não encontrado: {path}")
    with path.open("r", encoding="utf-8") as f:
        raw = json.load(f)
    return AppConfig.from_dict(raw)
