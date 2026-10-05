"""Aplicação principal do AI Strider."""
import sys
import threading
import webbrowser

import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from ai_strider.layout import ABAS, pagina
from ai_strider.modulos import licencas

app = FastAPI(title="AI Strider")
app.include_router(licencas.router)


@app.get("/", response_class=HTMLResponse)
def inicio():
    cards = "".join(
        f'<a class="atalho" href="{rota}"><b>{nome}</b></a>' for rota, nome in ABAS if rota != "/"
    )
    corpo = f"""<h1>AI Strider</h1><div class="sub">Painel administrativo dos nossos sistemas.</div>
<div class="atalhos">{cards}</div>"""
    estilo = """.atalhos{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:10px;margin-top:18px}
.atalho{display:block;background:#131c31;border:1px solid #24304b;border-radius:14px;padding:18px;color:#e5e7eb;text-decoration:none}
.atalho:hover{border-color:#2563eb}"""
    return pagina("/", "Início", corpo, estilo)


def run(host: str = "127.0.0.1", port: int = 8788, abrir_navegador: bool = True):
    if abrir_navegador:
        threading.Timer(1.0, lambda: webbrowser.open(f"http://{host}:{port}")).start()
    uvicorn.run(app, host=host, port=port, log_level="warning")


if __name__ == "__main__":
    run(abrir_navegador="--sem-navegador" not in sys.argv)
