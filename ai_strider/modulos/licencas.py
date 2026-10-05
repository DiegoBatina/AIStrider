"""Aba "Painel mestre de licenças".

Portado do Painel Mestre de Licenças v0.3 (master_panel.py). A fonte de verdade
continua sendo a central de licenças em HTTPS; esta aba só repassa as chamadas
administrativas para ela, com o token de administrador.
"""
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import requests
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse

from ai_strider.layout import pagina

CENTRAL_URL = os.getenv("AI_STRIDER_LICENCAS_URL", "https://licencas.revengetunel.online").rstrip("/")
# Mesmo arquivo de token que o painel antigo usava, para quem já tem ele configurado.
TOKEN_FILE = Path(os.getenv("LOCALAPPDATA", str(Path.home()))) / "PainelMestreLicencas" / "admin_token.txt"

PRODUCTS = {
    "RUNE": "Rune Pro", "LUMINA": "LuminaEAD", "SHOW": "Showball", "SAMRAH": "Samrah Tabacaria",
    "MOL": "MOL Helper / MTGO Helper", "OFICINA": "Oficina Mecânica", "PREMODERN": "Liga Brasileira Premodern",
}
STATUS_ACOES = {"activate": "active", "freeze": "frozen", "cancel": "cancelled"}

router = APIRouter(prefix="/licencas")


def central_token() -> str:
    token = os.getenv("AI_STRIDER_LICENCAS_TOKEN", "").strip()
    if token:
        return token
    try:
        return TOKEN_FILE.read_text(encoding="utf-8").strip()
    except OSError:
        return ""


def central(method, path, data=None):
    token = central_token()
    if not token:
        raise HTTPException(500, "Token administrativo da central de licenças não configurado")
    try:
        r = requests.request(
            method, CENTRAL_URL + path,
            headers={"Authorization": "Bearer " + token, "User-Agent": "AIStrider-PainelLicencas/1.0"},
            json=data, timeout=15,
        )
    except requests.RequestException as e:
        raise HTTPException(503, "Central de licenças indisponível: " + str(e))
    try:
        body = r.json()
    except ValueError:
        body = {"detail": r.text or "Resposta inválida da central"}
    if r.status_code >= 400:
        detail = body.get("detail", body) if isinstance(body, dict) else body
        raise HTTPException(r.status_code, str(detail))
    return body


def _vencida(x, agora):
    exp = x.get("expires_at")
    if not exp:
        return False
    try:
        d = datetime.fromisoformat(exp.replace("Z", "+00:00"))
    except ValueError:
        return False
    if d.tzinfo is None:
        d = d.replace(tzinfo=timezone.utc)
    return d < agora


def resumo(rows):
    agora = datetime.now(timezone.utc)
    out = []
    for code, name in PRODUCTS.items():
        rs = [x for x in rows if x.get("product_code") == code]
        ativas = [x for x in rs if x.get("status") == "active"]
        out.append({
            "product_code": code, "product_name": name,
            "active": sum(1 for x in ativas if not _vencida(x, agora)),
            "expired": sum(1 for x in ativas if _vencida(x, agora)),
            "frozen": sum(1 for x in rs if x.get("status") == "frozen"),
            "cancelled": sum(1 for x in rs if x.get("status") == "cancelled"),
        })
    return out


def _listar():
    rows = central("GET", "/admin/licenses")
    for d in rows:
        d["product_name"] = PRODUCTS.get(d.get("product_code"), d.get("product_code"))
    return rows


@router.get("/api/licenses")
def listar():
    return _listar()


@router.get("/api/summary")
def summary():
    return resumo(_listar())


@router.post("/api/licenses")
async def criar(req: Request):
    return central("POST", "/admin/licenses", await req.json())


@router.post("/api/licenses/{key}/extend")
def estender(key: str, days: int = 30):
    return central("POST", f"/admin/licenses/{key}/extend", {"days": max(1, days)})


@router.post("/api/licenses/{key}/reset-device")
def trocar_pc(key: str):
    return central("POST", f"/admin/licenses/{key}/reset-device")


@router.get("/api/licenses/{key}/history")
def historico(key: str):
    return central("GET", f"/admin/licenses/{key}/history")


# Rota genérica por último, para não engolir /extend e /reset-device.
@router.post("/api/licenses/{key}/{acao}")
def mudar_status(key: str, acao: str):
    if acao not in STATUS_ACOES:
        raise HTTPException(404, "Ação desconhecida")
    return central("POST", f"/admin/licenses/{key}/status", {"status": STATUS_ACOES[acao]})


ESTILO = """.p,.card{background:#131c31;border:1px solid #24304b;border-radius:14px;padding:17px;margin-top:14px}
.cards{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}.r{display:flex;gap:8px;flex-wrap:wrap}
input,select,button{padding:10px;border-radius:8px;border:1px solid #24304b;background:#0d1528;color:#e5e7eb}
button{border:0;background:#2563eb;cursor:pointer}.red{background:#b91c1c}.green{background:#166534}.amber{background:#a16207}.muted{background:#334155}
.tw{overflow-x:auto}table{width:100%;border-collapse:collapse;margin-top:10px}th,td{text-align:left;padding:9px;border-bottom:1px solid #24304b;font-size:12px}
.n{font-size:24px;font-weight:700}code{user-select:all}.hist{max-height:260px;overflow:auto}.erro{color:#fca5a5}
@media(max-width:1000px){.cards{grid-template-columns:1fr 1fr}}@media(max-width:560px){.cards{grid-template-columns:1fr}}"""

CORPO = """<h1>Painel mestre de licenças</h1><div class="sub">7 sistemas • planos • validade • congelamento • cancelamento • histórico</div>
__TOPO__<div id="aviso" class="erro"></div>
<div id="cards" class="cards"></div>
<div class="p"><h3>Gerar nova licença</h3><div class="r">
<select id="product"></select><input id="customer" placeholder="Cliente / empresa">
<select id="plan"><option>Mensal</option><option>Anual</option><option>Vitalício</option><option>Teste</option><option>Personalizado</option></select>
<input id="days" type="number" value="30" min="1" placeholder="Dias"><input id="notes" placeholder="Observações">
<button onclick="createL()">Gerar chave</button></div><p id="created"></p></div>
<div class="p"><div class="r"><select id="fp"><option value="">Todos os sistemas</option></select><select id="fs"><option value="">Todos os status</option><option value="active">Ativas</option><option value="frozen">Congeladas</option><option value="cancelled">Canceladas</option></select><input id="q" placeholder="Buscar cliente ou chave"><button class="muted" onclick="load()">Atualizar</button></div>
<div class="tw"><table><thead><tr><th>Sistema</th><th>Cliente</th><th>Plano</th><th>Chave</th><th>Status</th><th>Validade</th><th>PC</th><th>Ações</th></tr></thead><tbody id="tb"></tbody></table></div></div>
<div class="p"><h3>Histórico da licença</h3><div id="history" class="hist sub">Clique em Histórico em uma licença.</div></div>
<script>
const products=__PRODUCTS__;let all=[];
function esc(s){return String(s??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]))}
__API__
const opts=products.map(x=>`<option value="${x.code}">${esc(x.name)}</option>`).join('');
product.innerHTML=opts;fp.innerHTML+=opts;
fp.onchange=render;fs.onchange=render;q.oninput=render;
plan.onchange=()=>{if(plan.value==='Anual')days.value=365;else if(plan.value==='Mensal')days.value=30;else if(plan.value==='Teste')days.value=7;else if(plan.value==='Vitalício')days.value=36500}
const K=k=>encodeURIComponent(k);
async function createL(){try{let j=await api('/licenses',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({product_code:product.value,customer:customer.value,plan:plan.value,days:+days.value,notes:notes.value})});created.innerHTML='Nova chave: <code>'+esc(j.license_key)+'</code>';load()}catch(e){alert(e.message)}}
async function act(k,a){if(a==='cancel'&&!confirm('Cancelar esta licença?'))return;try{await api('/licenses/'+K(k)+'/'+a,{method:'POST'});load();showHistory(k)}catch(e){alert(e.message)}}
async function ext(k){let d=prompt('Adicionar quantos dias?','30');if(d){try{await api('/licenses/'+K(k)+'/extend?days='+K(d),{method:'POST'});load();showHistory(k)}catch(e){alert(e.message)}}}
async function resetD(k){if(confirm('Liberar a licença para outro computador?')){try{await api('/licenses/'+K(k)+'/reset-device',{method:'POST'});load();showHistory(k)}catch(e){alert(e.message)}}}
async function showHistory(k){try{let a=await api('/licenses/'+K(k)+'/history');histEl.scrollIntoView({behavior:'smooth',block:'center'});histEl.innerHTML='<b>'+esc(k)+'</b><table><tr><th>Data</th><th>Evento</th><th>Detalhes</th></tr>'+a.map(x=>`<tr><td>${esc(x.created_at)}</td><td>${esc(x.event)}</td><td>${esc(x.details)}</td></tr>`).join('')+'</table>'}catch(e){alert(e.message)}}
const histEl=document.getElementById('history');
function btn(cls,fn,k,label,extra=''){return `<button class="${cls}" data-k="${esc(k)}" onclick="${fn}(this.dataset.k${extra})">${label}</button>`}
function render(){let s=q.value.toLowerCase();let a=all.filter(x=>(!fp.value||x.product_code===fp.value)&&(!fs.value||x.status===fs.value)&&((x.customer||'')+(x.license_key||'')+(x.plan||'')).toLowerCase().includes(s));
tb.innerHTML=a.map(x=>{const k=x.license_key;return `<tr><td>${esc(x.product_name)}</td><td>${esc(x.customer)}</td><td>${esc(x.plan)}</td><td><code>${esc(k)}</code></td><td>${esc(x.status)}</td><td>${esc(x.expires_at||'Sem prazo')}</td><td>${esc(x.device_id||'-')}</td><td>${btn('green','act',k,'Ativar',",'activate'")} ${btn('amber','act',k,'Congelar',",'freeze'")} ${btn('red','act',k,'Cancelar',",'cancel'")} ${btn('muted','ext',k,'+ dias')} ${btn('muted','resetD',k,'Trocar PC')} ${btn('muted','showHistory',k,'Histórico')}</td></tr>`}).join('')}
async function load(){try{all=await api('/licenses');aviso.textContent='';render();
let sum=await api('/summary');cards.innerHTML=sum.map(x=>`<div class="card"><b>${esc(x.product_name)}</b><div class="n">${x.active}</div><span class="sub">ativas • ${x.frozen} congeladas • ${x.cancelled} canceladas • ${x.expired} vencidas</span></div>`).join('')}catch(e){aviso.textContent='Não foi possível falar com a central de licenças: '+e.message}}
load()
</script>"""


# No sistema, a tela chama as rotas /licencas/api acima, que repassam para a central.
API_SERVIDOR = """async function api(u,o){let r=await fetch('/licencas/api'+u,o);let j=await r.json().catch(()=>({}));if(!r.ok)throw Error(j.detail||'Erro');return j}"""


def corpo(api_js: str = API_SERVIDOR, topo: str = "") -> str:
    produtos = json.dumps([{"code": c, "name": n} for c, n in PRODUCTS.items()], ensure_ascii=False)
    return CORPO.replace("__PRODUCTS__", produtos).replace("__API__", api_js).replace("__TOPO__", topo)


@router.get("", response_class=HTMLResponse)
def tela():
    return pagina("/licencas", "Painel mestre de licenças", corpo(), ESTILO)
