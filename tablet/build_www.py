"""Gera tablet/www/index.html: a aba de licenças como app de tablet.

No tablet não há o servidor Python, então a própria tela fala com a central de
licenças. O endereço e o token ficam guardados só no aparelho. No app Android o
CapacitorHttp faz as chamadas pelo lado nativo, então a central não precisa de CORS.
"""
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from ai_strider.layout import pagina  # noqa: E402
from ai_strider.modulos import licencas  # noqa: E402

TOPO = """<details id="cfg" class="p"><summary><b>Conexão com a central</b></summary><div class="r" style="margin-top:10px">
<input id="cfgUrl" style="flex:1;min-width:220px" placeholder="https://licencas.seudominio"><input id="cfgToken" type="password" style="flex:1;min-width:220px" placeholder="Token de administrador">
<button onclick="salvarCfg()">Salvar</button></div><p class="sub">Fica guardado só neste aparelho.</p></details>"""

API_TABLET = """const CFG_PADRAO=__URL__;
function lerCfg(){try{return{url:localStorage.getItem('central_url')||CFG_PADRAO,token:localStorage.getItem('central_token')||''}}catch(e){return{url:CFG_PADRAO,token:''}}}
function salvarCfg(){try{localStorage.setItem('central_url',cfgUrl.value.trim().replace(/\\/+$/,''));localStorage.setItem('central_token',cfgToken.value.trim())}catch(e){}cfg.open=false;load()}
(function(){const c=lerCfg();cfgUrl.value=c.url;cfgToken.value=c.token;if(!c.token)cfg.open=true})();
const NOMES=Object.fromEntries(products.map(p=>[p.code,p.name]));
const STATUS={activate:'active',freeze:'frozen',cancel:'cancelled'};
async function central(m,path,body){const c=lerCfg();if(!c.token){cfg.open=true;throw Error('Configure o token de administrador em Conexão com a central')}
let r;try{r=await fetch(c.url+path,{method:m,headers:{'Authorization':'Bearer '+c.token,'Content-Type':'application/json'},body:body===undefined?undefined:JSON.stringify(body)})}catch(e){throw Error('Central de licenças indisponível')}
let j=await r.json().catch(()=>({}));if(!r.ok)throw Error(typeof j.detail==='string'?j.detail:'Erro '+r.status);return j}
function vencida(x,agora){if(!x.expires_at)return false;const d=new Date(/[zZ]|[+-]\\d\\d:?\\d\\d$/.test(x.expires_at)?x.expires_at:x.expires_at+'Z');return !isNaN(d)&&d<agora}
async function listar(){const rows=await central('GET','/admin/licenses');rows.forEach(d=>d.product_name=NOMES[d.product_code]||d.product_code);return rows}
async function api(u,o){o=o||{};const m=o.method||'GET';const [p,qs]=u.split('?');const seg=p.split('/').filter(Boolean);
if(p==='/licenses'&&m==='GET')return listar();
if(p==='/summary'){const rows=await listar(),agora=new Date();return products.map(({code,name})=>{const rs=rows.filter(x=>x.product_code===code),at=rs.filter(x=>x.status==='active');return{product_code:code,product_name:name,active:at.filter(x=>!vencida(x,agora)).length,expired:at.filter(x=>vencida(x,agora)).length,frozen:rs.filter(x=>x.status==='frozen').length,cancelled:rs.filter(x=>x.status==='cancelled').length}})}
if(p==='/licenses'&&m==='POST')return central('POST','/admin/licenses',JSON.parse(o.body));
const k=seg[1],acao=seg[2],base='/admin/licenses/'+encodeURIComponent(decodeURIComponent(k));
if(acao==='history')return central('GET',base+'/history');
if(acao==='extend'){const d=parseInt(new URLSearchParams(qs).get('days'))||30;return central('POST',base+'/extend',{days:Math.max(1,d)})}
if(acao==='reset-device')return central('POST',base+'/reset-device');
if(STATUS[acao])return central('POST',base+'/status',{status:STATUS[acao]});
throw Error('Ação desconhecida')}"""


def gerar(destino: Path = RAIZ / "tablet" / "www" / "index.html") -> Path:
    api_js = API_TABLET.replace("__URL__", json.dumps(licencas.CENTRAL_URL))
    html = pagina("/licencas", "Painel mestre de licenças", licencas.corpo(api_js, TOPO), licencas.ESTILO,
                  abas_visiveis=[("/licencas", "Painel mestre de licenças")])
    html = html.replace('href="/licencas"', 'href="#"')
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(html, encoding="utf-8")
    return destino


if __name__ == "__main__":
    print(gerar())
