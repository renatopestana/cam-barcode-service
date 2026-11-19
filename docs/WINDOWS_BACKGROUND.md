# Executando em Background no Windows (Sem Janela)

Para operar a câmera de forma 100% invisível no Windows — inclusive atuando como um leitor USB (Keyboard Wedge) — o serviço deve rodar na sessão do usuário utilizando `pythonw.exe`.

## Opção 1: Script Automático (PowerShell)

Dentro da pasta do projeto (com o ambiente virtual `.venv` criado e `config.json` configurado):

```powershell
.\deploy\windows\criar_atalho_windows.ps1 -AddToStartup
```

Isso criará o atalho **Cam Barcode Service** na Área de Trabalho e na pasta de inicialização do Windows (`shell:startup`).

## Opção 2: Manual

1. Clique com o botão direito na Área de Trabalho → **Novo > Atalho**.
2. Em **Local do item**, informe:
   ```text
   C:\caminho\do\projeto\.venv\Scripts\pythonw.exe -m cam_barcode_service.cli run --config config.json --log-file service.log
   ```
3. Clique com o botão direito no atalho → **Propriedades** → campo **Iniciar em**:
   ```text
   C:\caminho\do\projeto
   ```
4. *(Opcional)* Pressione `Win + R`, digite `shell:startup` e copie o atalho para iniciar com o Windows.

## Como encerrar o serviço

1. Pressione `Ctrl + Shift + Esc` para abrir o **Gerenciador de Tarefas**.
2. Vá na aba **Detalhes**, localize `pythonw.exe` e clique em **Finalizar tarefa**.
3. Em emergência no modo teclado, mova o cursor do mouse para qualquer canto da tela (`FAILSAFE` do PyAutoGUI).
