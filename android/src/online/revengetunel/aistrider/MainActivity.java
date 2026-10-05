package online.revengetunel.aistrider;

import android.app.Activity;
import android.graphics.Color;
import android.os.Bundle;
import android.webkit.JavascriptInterface;
import android.webkit.WebChromeClient;
import android.webkit.WebSettings;
import android.webkit.WebView;

import org.json.JSONObject;

import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.util.Iterator;

/**
 * App Android do AI Strider: a aba de licenças (assets/index.html) numa WebView.
 *
 * As chamadas para a central de licenças passam pela ponte "Nativo" (HTTP feito
 * aqui no Java), então a central não precisa liberar CORS para o app.
 */
public class MainActivity extends Activity {
    private WebView web;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        web = new WebView(this);
        web.setBackgroundColor(Color.parseColor("#0b1020"));
        WebSettings s = web.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);
        // Sem WebChromeClient a WebView ignora alert/confirm/prompt (usados em Cancelar, + dias, Trocar PC).
        web.setWebChromeClient(new WebChromeClient());
        web.addJavascriptInterface(new Ponte(), "Nativo");
        setContentView(web);
        if (savedInstanceState != null) {
            web.restoreState(savedInstanceState);
        } else {
            // Origem https fixa: o localStorage (endereço e token da central) fica guardado entre aberturas.
            web.loadDataWithBaseURL("https://app.aistrider.local/", lerAsset("index.html"), "text/html", "utf-8", null);
        }
    }

    @Override
    protected void onSaveInstanceState(Bundle outState) {
        super.onSaveInstanceState(outState);
        web.saveState(outState);
    }

    private String lerAsset(String nome) {
        try (InputStream in = getAssets().open(nome)) {
            return new String(lerTudo(in), "UTF-8");
        } catch (Exception e) {
            return "<p>Erro ao abrir o app: " + e + "</p>";
        }
    }

    private static byte[] lerTudo(InputStream in) throws java.io.IOException {
        ByteArrayOutputStream out = new ByteArrayOutputStream();
        byte[] buf = new byte[8192];
        int n;
        while ((n = in.read(buf)) > 0) out.write(buf, 0, n);
        return out.toByteArray();
    }

    private void responder(final String id, final int status, final String corpo) {
        final String js = "window.__nativoResposta(" + JSONObject.quote(id) + "," + status + "," + JSONObject.quote(corpo) + ")";
        web.post(new Runnable() {
            public void run() {
                web.evaluateJavascript(js, null);
            }
        });
    }

    class Ponte {
        @JavascriptInterface
        public void request(final String id, final String metodo, final String url, final String cabecalhosJson, final String corpo) {
            new Thread(new Runnable() {
                public void run() {
                    HttpURLConnection c = null;
                    try {
                        if (!url.startsWith("https://")) throw new IllegalArgumentException("A central precisa ser https");
                        c = (HttpURLConnection) new URL(url).openConnection();
                        c.setConnectTimeout(15000);
                        c.setReadTimeout(15000);
                        c.setRequestMethod(metodo);
                        c.setRequestProperty("User-Agent", "AIStrider-Android/1.0");
                        JSONObject h = new JSONObject(cabecalhosJson == null || cabecalhosJson.isEmpty() ? "{}" : cabecalhosJson);
                        for (Iterator<String> it = h.keys(); it.hasNext(); ) {
                            String k = it.next();
                            c.setRequestProperty(k, h.getString(k));
                        }
                        if (corpo != null && !corpo.isEmpty()) {
                            c.setDoOutput(true);
                            OutputStream out = c.getOutputStream();
                            out.write(corpo.getBytes("UTF-8"));
                            out.close();
                        }
                        int status = c.getResponseCode();
                        InputStream in = status >= 400 ? c.getErrorStream() : c.getInputStream();
                        String texto = in == null ? "" : new String(lerTudo(in), "UTF-8");
                        responder(id, status, texto);
                    } catch (Exception e) {
                        responder(id, 0, String.valueOf(e.getMessage()));
                    } finally {
                        if (c != null) c.disconnect();
                    }
                }
            }).start();
        }
    }
}
