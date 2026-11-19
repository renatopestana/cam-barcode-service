"""Domínio de distribuição: saídas plugáveis para cada código de barras lido.

Para adicionar novos canais (ex.: MQTT, WebSocket, RabbitMQ), basta herdar de
``BaseOutput`` e implementar o método ``emit(scan)``.
"""

from __future__ import annotations

import csv
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Optional

from cam_barcode_service.config import OutputsConfig
from cam_barcode_service.parser import Scan, describe

logger = logging.getLogger(__name__)


class BaseOutput(ABC):
    """Contrato base para qualquer destino de leitura."""

    name: str = "base"

    @abstractmethod
    def emit(self, scan: Scan) -> None:
        """Processa e entrega um objeto Scan."""


class ConsoleOutput(BaseOutput):
    """Imprime os detalhes formatados da leitura no log/stdout."""

    name = "console"

    def emit(self, scan: Scan) -> None:
        logger.info("Leitura confirmada:\n%s", "\n".join(describe(scan)))


class KeyboardOutput(BaseOutput):
    """Atua como um leitor USB físico (Keyboard Wedge), digitando o código no foco atual."""

    name = "keyboard"

    def __init__(
        self,
        suffix_key: Optional[str] = "enter",
        interval_seconds: float = 0.0,
        failsafe: bool = True,
    ) -> None:
        try:
            import pyautogui
        except ImportError as exc:
            raise RuntimeError(
                "Saída de teclado requer 'pyautogui'. Instale com: "
                "pip install 'cam-barcode-service[keyboard]'"
            ) from exc

        pyautogui.FAILSAFE = failsafe
        self._pyautogui = pyautogui
        self.suffix_key = suffix_key
        self.interval_seconds = interval_seconds

    def emit(self, scan: Scan) -> None:
        self._pyautogui.write(scan.raw, interval=self.interval_seconds)
        if self.suffix_key:
            self._pyautogui.press(self.suffix_key)
        logger.debug("Teclado emulado para código %s (sufixo=%s)", scan.raw, self.suffix_key)


class WebhookOutput(BaseOutput):
    """Envia a leitura estruturada via HTTP POST JSON para um backend web/local."""

    name = "webhook"

    def __init__(
        self,
        url: str,
        timeout_seconds: float = 1.5,
        headers: Optional[dict[str, str]] = None,
    ) -> None:
        try:
            import requests
        except ImportError as exc:
            raise RuntimeError(
                "Saída de webhook requer 'requests'. Instale com: "
                "pip install 'cam-barcode-service[webhook]'"
            ) from exc

        self._requests = requests
        self.url = url
        self.timeout_seconds = timeout_seconds
        self.headers = headers or {}

    def emit(self, scan: Scan) -> None:
        payload = scan.to_dict()
        try:
            resp = self._requests.post(
                self.url,
                json=payload,
                headers=self.headers,
                timeout=self.timeout_seconds,
            )
            resp.raise_for_status()
            logger.debug("Webhook entregue (%s) -> HTTP %s", self.url, resp.status_code)
        except Exception as exc:
            logger.error("Falha ao enviar webhook para %s: %s", self.url, exc)


class CsvLogOutput(BaseOutput):
    """Persiste histórico de leituras em arquivo CSV local."""

    name = "csv_log"

    def __init__(self, path: Path) -> None:
        self.path = path
        if not self.path.exists():
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(
                "data_hora,codigo,layout,dv_ok,plu,produto,preco,peso_kg\n",
                encoding="utf-8",
            )

    def emit(self, scan: Scan) -> None:
        with self.path.open("a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(
                [
                    datetime.now().isoformat(timespec="seconds"),
                    scan.raw,
                    scan.layout.name,
                    int(scan.check_ok),
                    scan.plu,
                    scan.product.name if scan.product else "",
                    str(scan.price) if scan.price is not None else "",
                    str(scan.weight) if scan.weight is not None else "",
                ]
            )


def build_outputs(cfg: OutputsConfig) -> list[BaseOutput]:
    """Instancia as saídas habilitadas conforme a configuração."""
    outputs: list[BaseOutput] = []
    if cfg.console.enabled:
        outputs.append(ConsoleOutput())
    if cfg.keyboard.enabled:
        outputs.append(
            KeyboardOutput(
                suffix_key=cfg.keyboard.suffix_key,
                interval_seconds=cfg.keyboard.interval_seconds,
                failsafe=cfg.keyboard.failsafe,
            )
        )
    if cfg.webhook.enabled:
        outputs.append(
            WebhookOutput(
                url=cfg.webhook.url,
                timeout_seconds=cfg.webhook.timeout_seconds,
                headers=cfg.webhook.headers,
            )
        )
    if cfg.csv_log.enabled:
        outputs.append(CsvLogOutput(Path(cfg.csv_log.path)))
    return outputs
