# Contribuindo com o cam-barcode-service

Contribuições são muito bem-vindas!

## Configurando o ambiente de desenvolvimento

```bash
git clone https://github.com/renatopestana/cam-barcode-service.git
cd cam-barcode-service
python -m venv .venv
# Linux/macOS:
source .venv/bin/activate
# Windows:
.venv\Scripts\activate

pip install -e ".[dev,all]"
```

## Padrões de qualidade

Antes de abrir um Pull Request, execute o linter e os testes:

```bash
ruff check src tests
pytest
```

## Fluxo de PR

1. Crie uma branch descritiva (`feat/mqtt-output`, `fix/camera-reconnect`).
2. Adicione testes unitários para novas regras ou saídas.
3. Atualize a documentação caso adicione novas opções de configuração ou CLI.
