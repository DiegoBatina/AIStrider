"""Moldura comum das páginas do AI Strider: cabeçalho e barra de abas."""
from html import escape

# Cada aba do sistema: (rota, título). Novas abas entram aqui.
ABAS = [
    ("/", "Início"),
    ("/licencas", "Painel mestre de licenças"),
]

ESTILO = """*{box-sizing:border-box}body{font-family:Segoe UI,Arial,sans-serif;background:#0b1020;color:#e5e7eb;margin:0}
header{background:#0d1528;border-bottom:1px solid #24304b}.top{max-width:1500px;margin:auto;padding:14px 26px 0}
.marca{font-size:18px;font-weight:700;letter-spacing:.3px}.marca span{color:#60a5fa}
nav{display:flex;gap:4px;margin-top:12px;flex-wrap:wrap}nav a{color:#94a3b8;text-decoration:none;padding:10px 16px;border-radius:10px 10px 0 0;border:1px solid transparent;border-bottom:0}
nav a:hover{color:#e5e7eb}nav a.ativa{color:#e5e7eb;background:#0b1020;border-color:#24304b}
.w{max-width:1500px;margin:auto;padding:26px}.sub{color:#94a3b8}
@media(max-width:760px){.top{padding:12px 14px 0}.w{padding:16px 14px 28px}h1{font-size:23px}
nav a{padding:9px 12px;font-size:14px}input,select,button{font-size:16px}}"""


def pagina(rota_ativa: str, titulo: str, corpo: str, estilo_extra: str = "", abas_visiveis=None) -> str:
    abas = "".join(
        f'<a href="{rota}" class="{"ativa" if rota == rota_ativa else ""}">{escape(nome)}</a>'
        for rota, nome in (ABAS if abas_visiveis is None else abas_visiveis)
    )
    return f"""<!doctype html><html lang="pt-br"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{escape(titulo)} · AI Strider</title><style>{ESTILO}{estilo_extra}</style></head>
<body><header><div class="top"><div class="marca">AI <span>Strider</span></div><nav>{abas}</nav></div></header>
<main class="w">{corpo}</main></body></html>"""
