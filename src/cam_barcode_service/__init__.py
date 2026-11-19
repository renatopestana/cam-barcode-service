"""cam_barcode_service: serviço headless de leitura de códigos de barras EAN-13 via câmera."""

from cam_barcode_service.config import AppConfig, load_config
from cam_barcode_service.outputs import (
    BaseOutput,
    ConsoleOutput,
    CsvLogOutput,
    KeyboardOutput,
    WebhookOutput,
    build_outputs,
)
from cam_barcode_service.parser import (
    PRESETS,
    Layout,
    Product,
    Scan,
    brl,
    describe,
    ean13_check_digit,
    is_valid_ean13,
    kg,
    load_products,
    parse_label,
)
from cam_barcode_service.reader import BarcodeReader, Detection
from cam_barcode_service.service import ScannerService

__version__ = "1.0.0"

__all__ = [
    "__version__",
    "AppConfig",
    "load_config",
    "BaseOutput",
    "ConsoleOutput",
    "CsvLogOutput",
    "KeyboardOutput",
    "WebhookOutput",
    "build_outputs",
    "PRESETS",
    "Layout",
    "Product",
    "Scan",
    "brl",
    "describe",
    "ean13_check_digit",
    "is_valid_ean13",
    "kg",
    "load_products",
    "parse_label",
    "BarcodeReader",
    "Detection",
    "ScannerService",
]
