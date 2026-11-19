# cam-barcode-service

Serviço profissional e **headless** (sem janela de vídeo) em Python para leitura de códigos de barras **EAN-13** via câmera comum — com suporte nativo ao fatiamento de **etiquetas de balança** (PLU, preço e peso) e entrega de dados via **Emulação de Teclado (Keyboard Wedge)**, **Webhook HTTP** ou **CSV**.

## Principais Recursos

- **Execução em Background (Headless):** captura e decodifica frames sem abrir janela gráfica.
- **Modo Teclado (Keyboard Wedge):** atua como um leitor USB físico, digitando o código diretamente no campo focado de qualquer sistema desktop ou página web.
- **Integração com Backends (Webhook HTTP):** envia um JSON estruturado (`raw`, `plu`, `price`, `weight`, `product`) via `POST` para APIs locais ou remotas.
- **Fatiador de Etiquetas de Balança:** presets prontos (`plataforma5`, `plataforma6`, `peso5`, `peso6`, `plu4`) e cálculo automático de peso/preço via catálogo CSV.
- **Arquitetura Extensível:** adicione novos canais de saída (MQTT, WebSocket, fila) herdando de `BaseOutput`.
- **Multiplataforma:** pronto para rodar via atalho silencioso (`pythonw.exe`) no Windows ou `systemd --user` no Linux.

---

## Instalação

```bash
# Instalação básica (apenas captura + parser)
pip install .

# Com emulação de teclado (Keyboard Wedge)
pip install ".[keyboard]"

# Com envio via Webhook HTTP
pip install ".[webhook]"

# Instalação completa (teclado + webhook + servidor FastAPI de exemplo)
pip install ".[all]"
```

> Para desenvolvimento local com edição em tempo real: `pip install -e ".[dev,all]"`.

---

## Início Rápido

### 1. Gere o arquivo de configuração

```bash
cam-barcode init-config
```

Edite o arquivo `config.json` gerado para ativar `keyboard` e/ou `webhook`.

### 2. Teste a câmera com preview visual (opcional)

```bash
cam-barcode run --config config.json --preview
```

### 3. Rode em background (headless)

```bash
cam-barcode run --config config.json
```

---

## Comandos da CLI (`cam-barcode --help`)

| Comando | Descrição |
| :--- | :--- |
| `cam-barcode run` | Inicia o serviço de leitura via câmera (headless por padrão). |
| `cam-barcode parse <codigo>` | Fatia e valida um código EAN-13 sem abrir a câmera (`--json` disponível). |
| `cam-barcode image <arquivo>` | Decodifica códigos EAN-13 em uma imagem estática. |
| `cam-barcode init-config` | Gera um `config.json` de exemplo pronto para uso. |
| `cam-barcode webhook-server` | Sobe uma API FastAPI local na porta `8000` para testar o recebimento de webhooks. |

### Exemplos úteis

```bash
# Testar fatiamento em JSON
cam-barcode parse 2000310004062 --layout plataforma5 --json

# Rodar direto pela linha de comando atuando como teclado
cam-barcode run --camera 0 --keyboard

# Rodar enviando para um backend local
cam-barcode run --camera 0 --webhook http://127.0.0.1:8000/api/v1/barcode/webhook
```

---

## Payload do Webhook

Quando `outputs.webhook.enabled` está ativo, cada leitura válida envia um `POST` com o seguinte JSON:

```json
{
  "raw": "2000310004062",
  "layout": "plataforma5",
  "check_ok": true,
  "is_scale_label": true,
  "prefix": "2",
  "plu": 31,
  "plu_str": "00031",
  "const": "0",
  "value_str": "00406",
  "check_digit": "2",
  "price": 4.06,
  "weight": 0.07,
  "product": {
    "code": 31,
    "name": "CONTRA FILE",
    "price_kg": 58.0
  }
}
```

---

## Uso como Biblioteca Python

Você também pode importar o parser ou o serviço diretamente em outros projetos Python:

```python
from cam_barcode_service import PRESETS, parse_label

scan = parse_label("2000310004062", PRESETS["plataforma5"])
print(scan.plu, scan.price, scan.check_ok)
```

---

## Documentação Adicional

- [Arquitetura e Extensibilidade (MQTT, WebSocket, etc.)](docs/ARCHITECTURE.md)
- [Executando em Background no Windows (Atalho Silencioso)](docs/WINDOWS_BACKGROUND.md)
- [Guia de Contribuição](CONTRIBUTING.md)

## Licença

Distribuído sob a licença MIT. Veja [LICENSE](LICENSE) para mais informações.
