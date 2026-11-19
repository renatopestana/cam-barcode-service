import json
from pathlib import Path

from cam_barcode_service.config import AppConfig, load_config
from cam_barcode_service.outputs import CsvLogOutput
from cam_barcode_service.parser import PRESETS, parse_label


def test_load_config_from_json(tmp_path: Path):
    cfg_file = tmp_path / "config.json"
    cfg_file.write_text(
        json.dumps(
            {
                "camera": {"id": 2, "width": 1280, "height": 720},
                "cooldown_seconds": 5.0,
                "outputs": {
                    "keyboard": {"enabled": True, "suffix_key": "tab"},
                    "webhook": {"enabled": True, "url": "http://localhost:9000/hook"},
                },
            }
        ),
        encoding="utf-8",
    )

    cfg = load_config(cfg_file)
    assert isinstance(cfg, AppConfig)
    assert cfg.camera.id == 2
    assert cfg.cooldown_seconds == 5.0
    assert cfg.outputs.keyboard.enabled is True
    assert cfg.outputs.keyboard.suffix_key == "tab"
    assert cfg.outputs.webhook.url == "http://localhost:9000/hook"


def test_csv_log_output(tmp_path: Path):
    log_path = tmp_path / "leituras.csv"
    out = CsvLogOutput(log_path)
    scan = parse_label("2000310004062", PRESETS["plataforma5"])
    out.emit(scan)

    lines = log_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    assert "2000310004062" in lines[1]
