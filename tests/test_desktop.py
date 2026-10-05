import urllib.request

from ai_strider import desktop


def test_abre_janela_com_o_sistema_e_encerra(monkeypatch):
    vistos = []

    def janela_falsa(url):
        with urllib.request.urlopen(url + "/licencas", timeout=5) as r:
            vistos.append((url, r.read().decode("utf-8")))

    monkeypatch.setattr(desktop, "PORTA_PADRAO", desktop._porta_qualquer())
    monkeypatch.setattr(desktop, "abrir_janela", janela_falsa)
    desktop.main([])
    assert vistos and "Painel mestre de licenças" in vistos[0][1]


def test_sem_edge_nem_chrome_usa_navegador_padrao(monkeypatch):
    abertos, avisos = [], []
    monkeypatch.setattr(desktop, "achar_navegador_app", lambda: None)
    monkeypatch.setattr(desktop.webbrowser, "open", abertos.append)
    monkeypatch.setattr(desktop, "aviso", lambda t, erro=False: avisos.append(t))
    desktop.abrir_janela("http://127.0.0.1:1")
    assert abertos == ["http://127.0.0.1:1"] and avisos
