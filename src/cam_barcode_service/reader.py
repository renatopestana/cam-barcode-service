"""Abstração de detecção e decodificação de códigos de barras em frames de imagem."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional


@dataclass(frozen=True)
class Detection:
    text: str
    points: Optional[list[tuple[int, int]]]


class BarcodeReader:
    """Usa o detector de barcodes do OpenCV (>= 4.8) ou, opcionalmente, o pyzbar."""

    def __init__(self, backend: str = "auto") -> None:
        import cv2  # import tardio para permitir uso do parser sem dependências de visão

        self.cv2 = cv2
        self.backend = backend
        self._zbar: Any = None
        self._det: Any = None

        if backend in ("auto", "opencv") and hasattr(cv2, "barcode"):
            self._det = cv2.barcode.BarcodeDetector()
            self.backend = "opencv"
        elif backend in ("auto", "pyzbar"):
            try:
                from pyzbar import pyzbar  # type: ignore[import-untyped]

                self._zbar = pyzbar
                self.backend = "pyzbar"
            except ImportError:
                pass

        if self._det is None and self._zbar is None:
            raise RuntimeError(
                "Nenhum leitor de barcode disponível. Instale opencv-python>=4.8 "
                "(pip install opencv-python) ou pyzbar (pip install pyzbar)."
            )

    def read(self, frame: Any) -> list[Detection]:
        """Retorna todos os códigos detectados no frame."""
        return self._read_opencv(frame) if self._det is not None else self._read_zbar(frame)

    def _read_opencv(self, frame: Any) -> list[Detection]:
        import numpy as np

        det = self._det
        fn = getattr(det, "detectAndDecodeWithType", None) or det.detectAndDecode
        res = fn(frame)
        if len(res) == 4:
            ok, infos, _types, pts = res
        elif len(res) == 3:
            infos, _types, pts = res
            ok = bool(infos)
        else:
            return []

        if not ok or pts is None or infos is None:
            return []
        if isinstance(infos, str):
            infos = [infos]

        pts_arr = np.asarray(pts).reshape(-1, 4, 2)
        out: list[Detection] = []
        for text, quad in zip(infos, pts_arr):
            if text:
                out.append(Detection(text, [(int(x), int(y)) for x, y in quad]))
        return out

    def _read_zbar(self, frame: Any) -> list[Detection]:
        gray = self.cv2.cvtColor(frame, self.cv2.COLOR_BGR2GRAY)
        out: list[Detection] = []
        for d in self._zbar.decode(gray):
            if d.type == "EAN13":
                pts = [(p.x, p.y) for p in d.polygon]
                out.append(Detection(d.data.decode("ascii", "ignore"), pts))
        return out
