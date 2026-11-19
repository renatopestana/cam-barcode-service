# Arquitetura do Projeto

O `cam-barcode-service` adota uma separação clara em **4 domínios independentes** dentro do layout padrão `src/`:

```text
[Câmera / Imagem]
       │
       ▼
1. Domínio de Captura (reader.py + service.py)
       │  Frame -> Detection(text, points)
       ▼
2. Domínio de Regra de Negócio (parser.py)
       │  Validação EAN-13 + Fatiamento (PLU, Preço, Peso, Produto) -> Scan
       ▼
3. Domínio de Controle (service.py)
       │  Cooldown / Deduplicação + Sinais SO (SIGINT/SIGTERM)
       ▼
4. Domínio de Distribuição (outputs.py)
       ├── KeyboardOutput  (Emulação de teclado / Keyboard Wedge)
       ├── WebhookOutput   (HTTP POST JSON para backends locais/web)
       ├── CsvLogOutput    (Persistência local em CSV)
       └── ConsoleOutput   (Log estruturado)
```

## Como estender com novas saídas (ex.: MQTT ou WebSocket)

O domínio de distribuição usa o padrão *Strategy/Observer*. Qualquer desenvolvedor pode criar um novo conector herdando de `BaseOutput`:

```python
from cam_barcode_service import AppConfig, BaseOutput, Scan, ScannerService

class MqttOutput(BaseOutput):
    name = "mqtt"

    def __init__(self, broker: str, topic: str):
        self.broker = broker
        self.topic = topic

    def emit(self, scan: Scan) -> None:
        # Publique scan.to_dict() no seu broker MQTT
        print(f"Publicando em {self.topic}: {scan.raw}")

cfg = AppConfig()
service = ScannerService(cfg, outputs=[MqttOutput("localhost", "pdv/barcode")])
service.run(preview=False)
```
