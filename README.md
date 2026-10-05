# AI Strider

Painel administrativo dos sistemas AI Strider. Cada área do sistema é uma aba.

## Abas

| Aba | Rota | O que faz |
| --- | --- | --- |
| Início | `/` | Atalhos para as áreas do sistema |
| Painel mestre de licenças | `/licencas` | Gera, ativa, congela, cancela, renova e troca o PC das licenças dos 7 sistemas (Rune Pro, LuminaEAD, Showball, Samrah Tabacaria, MOL/MTGO Helper, Oficina Mecânica, Liga Brasileira Premodern) |

## Rodar no Windows

Dê dois cliques em `AIStrider.exe`. O sistema abre numa janela própria (janela de app do Edge, sem barra de endereço nem abas) e fechar a janela encerra o programa. Se o computador não tiver Edge nem Chrome, ele abre no navegador padrão e um aviso fica na tela; clique em OK para encerrar.

Opções: `AIStrider.exe --navegador` abre no navegador padrão; `AIStrider.exe --sem-navegador` sobe só o servidor em http://127.0.0.1:8788.

Para rodar a partir do código: `ABRIR_AI_STRIDER.bat` (cria o ambiente Python e instala as dependências).

Para gerar o `.exe` à mão: `GERAR_EXE_WINDOWS.bat` (sai em `dist\AIStrider.exe`).

## Executáveis prontos

A cada push, o GitHub Actions (`.github/workflows/executaveis.yml`) gera e testa:

- `AIStrider.exe` para Windows (abre o sistema numa janela própria)
- `AIStrider-tablet.apk` para tablet Android

Os dois ficam na página **Releases** do repositório, na versão `build-<branch>`.

## Tablet

O app de tablet (`tablet/`) é a aba de licenças empacotada com Capacitor. Como no tablet não roda o servidor Python, a tela fala direto com a central de licenças. Na primeira vez, abra **Conexão com a central** e cole o token de administrador; ele fica guardado só no aparelho.

Para gerar à mão: `python tablet/build_www.py`, depois em `tablet/`: `npm install`, `npx cap add android`, `npx cap sync android` e `./gradlew assembleDebug` dentro de `tablet/android` (precisa do Android SDK).

## Configurar a central de licenças

A aba de licenças conversa com a central em HTTPS (padrão `https://licencas.revengetunel.online`). Ela precisa do token de administrador, lido nesta ordem:

1. variável de ambiente `AI_STRIDER_LICENCAS_TOKEN`
2. arquivo `%LOCALAPPDATA%\PainelMestreLicencas\admin_token.txt` (o mesmo do painel antigo, então quem já usava não precisa fazer nada)

Para apontar para outra central, defina `AI_STRIDER_LICENCAS_URL`.

O painel é administrativo: rode só na sua máquina (ele escuta apenas em `127.0.0.1`).

## Adicionar uma aba nova

1. Crie `ai_strider/modulos/<nome>.py` com um `APIRouter(prefix="/<rota>")` e uma tela que use `layout.pagina(...)`.
2. Registre o router em `ai_strider/main.py`.
3. Acrescente `("/<rota>", "Título")` em `ABAS` no `ai_strider/layout.py`.

## Testes

```
pip install -r requirements-dev.txt
pytest
```
