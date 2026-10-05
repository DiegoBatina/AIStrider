"""Gera android/assets/index.html: a tela do tablet com o fetch passando pela ponte nativa do app."""
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "tablet"))

import build_www  # noqa: E402

# Troca o fetch da página pelo HTTP do Java (MainActivity.Ponte), que não esbarra em CORS.
PONTE = """<script>(function(){const pend={};let n=0;
window.__nativoResposta=function(id,status,corpo){const p=pend[id];if(!p)return;delete pend[id];
if(status===0)p.rej(new TypeError(corpo||'Falha de rede'));else p.res(new Response(corpo,{status:status}))};
if(window.Nativo)window.fetch=function(url,o){o=o||{};return new Promise(function(res,rej){const id='r'+(++n);pend[id]={res:res,rej:rej};
Nativo.request(id,o.method||'GET',String(url),JSON.stringify(o.headers||{}),o.body==null?'':String(o.body))})};})();</script>"""


def gerar(destino: Path = Path(__file__).resolve().parent / "assets" / "index.html") -> Path:
    html = build_www.gerar(destino).read_text(encoding="utf-8")
    destino.write_text(html.replace("</head>", PONTE + "</head>", 1), encoding="utf-8")
    return destino


if __name__ == "__main__":
    print(gerar())
