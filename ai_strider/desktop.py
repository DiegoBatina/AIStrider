"""Abre o AI Strider como programa do Windows, numa janela própria.

O servidor roda dentro do próprio processo e a tela abre numa janela de app do
Edge (ou do Chrome), sem barra de endereço nem abas. Fechar a janela encerra o
programa. Sem Edge nem Chrome, abre no navegador padrão e um aviso fica aberto
para encerrar.
"""
import os
import socket
import subprocess
import sys
import threading
import time
import urllib.request
import webbrowser
from pathlib import Path

import uvicorn

from ai_strider.main import app

HOST = "127.0.0.1"
PORTA_PADRAO = 8788
NOME = "AI Strider"
DADOS = Path(os.getenv("LOCALAPPDATA", str(Path.home()))) / "AIStrider"


def aviso(texto: str, erro: bool = False) -> None:
    """Caixa de mensagem do Windows (o .exe não tem console)."""
    if sys.platform == "win32":
        import ctypes
        ctypes.windll.user32.MessageBoxW(None, texto, NOME, 0x10 if erro else 0x40)
    else:
        print(texto)


def _porta_livre(porta: int) -> bool:
    with socket.socket() as s:
        return s.connect_ex((HOST, porta)) != 0


def _e_o_ai_strider(url: str) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=2) as r:
            return b"AI <span>Strider</span>" in r.read()
    except OSError:
        return False


def _porta_qualquer() -> int:
    with socket.socket() as s:
        s.bind((HOST, 0))
        return s.getsockname()[1]


def iniciar_servidor(porta: int) -> uvicorn.Server:
    # log_config=None: no .exe sem console não há stdout para o log do uvicorn.
    servidor = uvicorn.Server(uvicorn.Config(app, host=HOST, port=porta, log_config=None, log_level="warning"))
    threading.Thread(target=servidor.run, daemon=True).start()
    for _ in range(100):
        if servidor.started:
            return servidor
        time.sleep(0.1)
    raise RuntimeError(f"O servidor interno não subiu na porta {porta}")


def achar_navegador_app():
    """Edge vem em todo Windows 10/11; Chrome serve como alternativa."""
    bases = [os.getenv(v) for v in ("PROGRAMFILES(X86)", "PROGRAMFILES", "LOCALAPPDATA")]
    candidatos = [
        Path(b) / sub for b in bases if b
        for sub in ("Microsoft/Edge/Application/msedge.exe", "Google/Chrome/Application/chrome.exe")
    ]
    return next((str(c) for c in candidatos if c.is_file()), None)


def abrir_janela(url: str) -> None:
    """Abre a janela e só retorna quando o usuário fechar."""
    exe = achar_navegador_app()
    if exe:
        # Perfil próprio: o processo fica vivo enquanto a janela estiver aberta,
        # mesmo que o Edge normal do usuário esteja aberto.
        perfil = DADOS / "janela"
        perfil.mkdir(parents=True, exist_ok=True)
        proc = subprocess.Popen([
            exe, f"--app={url}", f"--user-data-dir={perfil}", "--window-size=1400,900",
            "--no-first-run", "--no-default-browser-check",
        ])
        proc.wait()
    else:
        webbrowser.open(url)
        aviso(f"{NOME} está aberto no navegador em {url}.\n\nClique em OK para encerrar o programa.")


def main(argv=None) -> None:
    argv = sys.argv[1:] if argv is None else argv
    # No .exe sem console, stdout e stderr são None.
    if sys.stdout is None:
        sys.stdout = open(os.devnull, "w")
    if sys.stderr is None:
        sys.stderr = open(os.devnull, "w")
    try:
        if "--sem-navegador" in argv:
            # Só o servidor, como antes (usado no teste do executável).
            uvicorn.run(app, host=HOST, port=PORTA_PADRAO, log_config=None, log_level="warning")
            return
        porta = PORTA_PADRAO
        url = f"http://{HOST}:{porta}"
        if not _porta_livre(porta):
            if _e_o_ai_strider(url):
                # Já está rodando: só abre outra janela.
                abrir_janela(url)
                return
            porta = _porta_qualquer()
            url = f"http://{HOST}:{porta}"
        servidor = iniciar_servidor(porta)
        if "--navegador" in argv:
            webbrowser.open(url)
            aviso(f"{NOME} está aberto no navegador em {url}.\n\nClique em OK para encerrar o programa.")
        else:
            abrir_janela(url)
        servidor.should_exit = True
    except Exception as e:  # noqa: BLE001 - qualquer falha vira aviso na tela
        aviso(f"Não foi possível abrir o {NOME}:\n\n{e}", erro=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
