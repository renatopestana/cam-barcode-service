# Changelog

## [1.0.0] - 2026-11-19

### Adicionado
- Estrutura de pacote Python padrão (`src/` layout + `pyproject.toml`).
- Serviço headless de captura via câmera (`ScannerService`) com modo `--preview` opcional.
- Domínio de saídas plugáveis (`KeyboardOutput`, `WebhookOutput`, `CsvLogOutput`, `ConsoleOutput`).
- CLI unificada `cam-barcode` com subcomandos `run`, `parse`, `image`, `init-config` e `webhook-server`.
- Scripts de deploy para Windows (`pythonw.exe` + atalho) e Linux (`systemd --user`).
- Testes automatizados com `pytest` e workflow de CI no GitHub Actions.
