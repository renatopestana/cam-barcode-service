"""Interface de linha de comando (CLI) do cam-barcode-service."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Optional

from cam_barcode_service import __version__
from cam_barcode_service.config import AppConfig, load_config
from cam_barcode_service.parser import PRESETS, describe, load_products, parse_label
from cam_barcode_service.reader import BarcodeReader
from cam_barcode_service.service import ScannerService


def _setup_logging(verbose: bool, log_file: Optional[str]) -> None:
    handlers: list[logging.Handler] = [logging.StreamHandler(sys.stdout)]
    if log_file:
        handlers.append(logging.FileHandler(log_file, encoding="utf-8"))
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=handlers,
    )


def _cmd_run(args: argparse.Namespace) -> int:
    cfg = load_config(Path(args.config)) if args.config else AppConfig()

    if args.camera is not None:
        cfg.camera.id = args.camera
    if args.layout:
        cfg.parser.layout = args.layout
    if args.products:
        cfg.parser.products_csv = args.products
    if args.cooldown is not None:
        cfg.cooldown_seconds = args.cooldown
    if args.keyboard:
        cfg.outputs.keyboard.enabled = True
    if args.webhook:
        cfg.outputs.webhook.enabled = True
        cfg.outputs.webhook.url = args.webhook
    if args.csv_log:
        cfg.outputs.csv_log.enabled = True
        cfg.outputs.csv_log.path = args.csv_log

    service = ScannerService(cfg)
    return service.run(preview=args.preview)


def _cmd_parse(args: argparse.Namespace) -> int:
    layout = PRESETS[args.layout]
    products = load_products(Path(args.products)) if args.products else {}
    scan = parse_label(args.code, layout, products)
    if args.json:
        print(json.dumps(scan.to_dict(), ensure_ascii=False, indent=2))
    else:
        print("\n".join(describe(scan)))
    return 0


def _cmd_image(args: argparse.Namespace) -> int:
    import cv2

    img = cv2.imread(args.path)
    if img is None:
        print(f"Erro: não foi possível abrir a imagem {args.path}", file=sys.stderr)
        return 1

    layout = PRESETS[args.layout]
    products = load_products(Path(args.products)) if args.products else {}
    reader = BarcodeReader(backend=args.backend)
    found = [d for d in reader.read(img) if len(d.text) == 13 and d.text.isdigit()]
    if not found:
        print("Nenhum código EAN-13 encontrado na imagem.")
        return 2

    for d in found:
        scan = parse_label(d.text, layout, products)
        if args.json:
            print(json.dumps(scan.to_dict(), ensure_ascii=False, indent=2))
        else:
            print("\n".join(describe(scan)) + "\n")
    return 0


def _cmd_init_config(args: argparse.Namespace) -> int:
    dest = Path(args.output)
    if dest.exists() and not args.force:
        print(f"Arquivo já existe: {dest}. Use --force para sobrescrever.", file=sys.stderr)
        return 1

    sample = {
        "camera": {
            "id": 0,
            "width": 640,
            "height": 480,
            "backend": "auto",
            "skip_frames": 1,
            "loop_sleep_seconds": 0.03,
        },
        "parser": {
            "layout": "plataforma5",
            "products_csv": None,
            "only_valid_ean13": True,
        },
        "cooldown_seconds": 3.0,
        "outputs": {
            "console": {"enabled": True},
            "keyboard": {
                "enabled": True,
                "suffix_key": "enter",
                "interval_seconds": 0.0,
                "failsafe": True,
            },
            "webhook": {
                "enabled": False,
                "url": "http://127.0.0.1:8000/api/v1/barcode/webhook",
                "timeout_seconds": 1.5,
                "headers": {},
            },
            "csv_log": {"enabled": False, "path": "leituras.csv"},
        },
    }
    dest.write_text(json.dumps(sample, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Arquivo de configuração criado em: {dest}")
    return 0


def _cmd_webhook_server(args: argparse.Namespace) -> int:
    from cam_barcode_service.webhook_example import run_server

    return run_server(host=args.host, port=args.port)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cam-barcode",
        description=(
            "Serviço headless para leitura de códigos de barras EAN-13 via câmera, "
            "com suporte a emulação de teclado (Keyboard Wedge), Webhook HTTP e CSV."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Exemplos:\n"
            "  cam-barcode init-config\n"
            "  cam-barcode run --config config.json\n"
            "  cam-barcode run --camera 0 --keyboard --preview\n"
            "  cam-barcode parse 2000310004062 --layout plataforma5 --json\n"
            "  cam-barcode image etiqueta.jpg --layout plataforma5\n"
            "  cam-barcode webhook-server --port 8000\n"
        ),
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("-v", "--verbose", action="store_true", help="Ativa logs detalhados (DEBUG)")
    parser.add_argument("--log-file", help="Salva logs de execução em arquivo")

    sub = parser.add_subparsers(dest="command", required=True)

    # run
    p_run = sub.add_parser("run", help="Inicia o serviço de leitura via câmera (headless por padrão)")
    p_run.add_argument("-c", "--config", help="Caminho para o arquivo config.json")
    p_run.add_argument("--camera", type=int, help="ID da câmera (sobrescreve config.json)")
    p_run.add_argument("--layout", choices=PRESETS, help="Layout da etiqueta de balança")
    p_run.add_argument("--products", help="CSV de produtos (codigo,nome,preco_kg)")
    p_run.add_argument("--cooldown", type=float, help="Segundos antes de repetir o mesmo código")
    p_run.add_argument("--keyboard", action="store_true", help="Habilita saída como teclado (Keyboard Wedge)")
    p_run.add_argument("--webhook", help="URL de destino para habilitar saída via Webhook POST")
    p_run.add_argument("--csv-log", help="Caminho de arquivo para habilitar log CSV")
    p_run.add_argument("--preview", action="store_true", help="Abre janela de vídeo para calibração/teste")
    p_run.set_defaults(func=_cmd_run)

    # parse
    p_parse = sub.add_parser("parse", help="Decodifica e fatia um código EAN-13 sem abrir a câmera")
    p_parse.add_argument("code", help="Código EAN-13 (13 dígitos)")
    p_parse.add_argument("--layout", choices=PRESETS, default="plataforma5")
    p_parse.add_argument("--products", help="CSV opcional de produtos")
    p_parse.add_argument("--json", action="store_true", help="Imprime saída em formato JSON")
    p_parse.set_defaults(func=_cmd_parse)

    # image
    p_img = sub.add_parser("image", help="Lê códigos EAN-13 a partir de uma imagem estática")
    p_img.add_argument("path", help="Caminho da imagem (JPG/PNG)")
    p_img.add_argument("--layout", choices=PRESETS, default="plataforma5")
    p_img.add_argument("--products", help="CSV opcional de produtos")
    p_img.add_argument("--backend", choices=["auto", "opencv", "pyzbar"], default="auto")
    p_img.add_argument("--json", action="store_true", help="Imprime saída em formato JSON")
    p_img.set_defaults(func=_cmd_image)

    # init-config
    p_init = sub.add_parser("init-config", help="Gera um arquivo config.json pronto para edição")
    p_init.add_argument("-o", "--output", default="config.json", help="Arquivo de destino (padrão: config.json)")
    p_init.add_argument("--force", action="store_true", help="Sobrescreve arquivo se já existir")
    p_init.set_defaults(func=_cmd_init_config)

    # webhook-server
    p_srv = sub.add_parser("webhook-server", help="Sobe servidor FastAPI de exemplo para testar webhooks")
    p_srv.add_argument("--host", default="127.0.0.1")
    p_srv.add_argument("--port", type=int, default=8000)
    p_srv.set_defaults(func=_cmd_webhook_server)

    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    _setup_logging(verbose=args.verbose, log_file=args.log_file)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
