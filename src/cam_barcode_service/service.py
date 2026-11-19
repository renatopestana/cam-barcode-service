"""Domínio de captura: loop da câmera em modo headless ou com preview opcional."""

from __future__ import annotations

import logging
import signal
import time
from pathlib import Path
from typing import Any, Optional

from cam_barcode_service.config import AppConfig
from cam_barcode_service.outputs import BaseOutput, build_outputs
from cam_barcode_service.parser import (
    PRESETS,
    Layout,
    Product,
    Scan,
    describe,
    load_products,
    parse_label,
)
from cam_barcode_service.reader import BarcodeReader

logger = logging.getLogger(__name__)


def _draw_panel(cv2: Any, frame: Any, lines: list[str], ok: bool) -> None:
    color = (0, 200, 0) if ok else (0, 140, 255)
    pad, lh = 8, 22
    w = min(frame.shape[1] - 10, 760)
    h = pad * 2 + lh * len(lines)
    overlay = frame.copy()
    cv2.rectangle(overlay, (5, 5), (5 + w, 5 + h), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)
    for i, line in enumerate(lines):
        cv2.putText(
            frame,
            line,
            (12, 5 + pad + lh * (i + 1) - 6),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            color if i == 0 else (255, 255, 255),
            1,
            cv2.LINE_AA,
        )


class ScannerService:
    """Serviço principal que captura frames, decodifica EAN-13 e despacha para as saídas."""

    def __init__(
        self,
        config: AppConfig,
        outputs: Optional[list[BaseOutput]] = None,
        layout: Optional[Layout] = None,
        products: Optional[dict[int, Product]] = None,
    ) -> None:
        self.config = config
        self.layout = layout or PRESETS[config.parser.layout]
        self.layout.validate()

        if products is not None:
            self.products = products
        elif config.parser.products_csv:
            self.products = load_products(Path(config.parser.products_csv))
        else:
            self.products = {}

        self.outputs = outputs if outputs is not None else build_outputs(config.outputs)
        self._running = False
        self._last_seen: dict[str, float] = {}

    def stop(self) -> None:
        """Solicita parada limpa do loop de captura."""
        self._running = False

    def dispatch(self, scan: Scan) -> None:
        """Entrega o Scan para todas as saídas configuradas de forma isolada."""
        for out in self.outputs:
            try:
                out.emit(scan)
            except Exception as exc:
                logger.error("Erro na saída '%s': %s", out.name, exc)

    def _should_emit(self, code: str, now: float) -> bool:
        if now - self._last_seen.get(code, 0.0) > self.config.cooldown_seconds:
            self._last_seen[code] = now
            return True
        return False

    def _install_signal_handlers(self) -> None:
        def _handle(signum: int, _frame: Any) -> None:
            logger.info("Sinal %s recebido. Encerrando serviço...", signum)
            self.stop()

        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                signal.signal(sig, _handle)
            except ValueError:
                # Ignora caso o serviço rode em uma thread secundária
                pass

    def run(self, preview: bool = False) -> int:
        """Inicia o loop de leitura da câmera.

        Args:
            preview: Se False (padrão), roda 100% em background sem abrir janela.
                     Se True, exibe janela OpenCV para calibração/diagnóstico.
        """
        import cv2

        self._install_signal_handlers()
        reader = BarcodeReader(backend=self.config.camera.backend)
        cap = cv2.VideoCapture(self.config.camera.id)
        if not cap.isOpened():
            logger.error("Não foi possível abrir a câmera %s.", self.config.camera.id)
            return 1

        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.config.camera.width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config.camera.height)

        out_names = [o.name for o in self.outputs] or ["nenhuma"]
        logger.info(
            "Serviço iniciado | modo=%s | câmera=%s | backend=%s | layout=%s | saídas=%s",
            "preview" if preview else "headless",
            self.config.camera.id,
            reader.backend,
            self.layout.name,
            ", ".join(out_names),
        )

        self._running = True
        frame_n = 0
        last_scan: Optional[Scan] = None
        last_shown = 0.0

        try:
            while self._running:
                ok, frame = cap.read()
                if not ok:
                    logger.warning("Falha ao capturar frame da câmera. Tentando novamente...")
                    time.sleep(1.0)
                    continue

                frame_n += 1
                if frame_n % self.config.camera.skip_frames == 0:
                    for d in reader.read(frame):
                        if len(d.text) != 13 or not d.text.isdigit():
                            continue
                        if preview and d.points:
                            for a, b in zip(d.points, d.points[1:] + d.points[:1]):
                                cv2.line(frame, a, b, (0, 255, 0), 2)
                        try:
                            scan = parse_label(d.text, self.layout, self.products)
                        except ValueError:
                            continue

                        if self.config.parser.only_valid_ean13 and not scan.check_ok:
                            logger.debug("EAN-13 com DV inválido ignorado: %s", scan.raw)
                            continue

                        now = time.time()
                        last_scan, last_shown = scan, now
                        if self._should_emit(scan.raw, now):
                            self.dispatch(scan)

                if preview:
                    if last_scan and time.time() - last_shown < 4.0:
                        _draw_panel(cv2, frame, describe(last_scan), last_scan.check_ok)
                    else:
                        _draw_panel(
                            cv2,
                            frame,
                            [f"Aponte a etiqueta [layout: {self.layout.name}] (q/ESC sai)"],
                            True,
                        )
                    cv2.imshow("cam-barcode-service (preview)", frame)
                    key = cv2.waitKey(1) & 0xFF
                    if key in (ord("q"), 27):
                        break
                elif self.config.camera.loop_sleep_seconds > 0:
                    time.sleep(self.config.camera.loop_sleep_seconds)
        finally:
            cap.release()
            if preview:
                cv2.destroyAllWindows()
            logger.info("Serviço encerrado.")

        return 0
