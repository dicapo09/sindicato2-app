package cl.sindicato.pacificodelsur;

import android.app.Activity;
import android.content.ActivityNotFoundException;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.graphics.Insets;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.view.View;
import android.view.WindowInsets;
import android.view.WindowManager;
import android.webkit.JavascriptInterface;
import android.webkit.ValueCallback;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.window.OnBackInvokedDispatcher;

import com.google.firebase.messaging.FirebaseMessaging;

/** App del Sindicato N°2: muestra la app web incluida (assets/index.html), que se actualiza sola desde GitHub. */
public class MainActivity extends Activity {
    private static final String INICIO = "file:///android_asset/index.html";
    private WebView web;
    private static final int ELEGIR_FOTO = 7;
    private ValueCallback<Uri[]> fotoCallback;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        // Seguridad: impide pantallazos y grabaciones de pantalla, y oculta la app en "recientes"
        getWindow().setFlags(WindowManager.LayoutParams.FLAG_SECURE, WindowManager.LayoutParams.FLAG_SECURE);
        web = new WebView(this);
        web.setBackgroundColor(0xFF0F4643);
        WebSettings s = web.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);
        s.setMediaPlaybackRequiresUserGesture(true);
        web.addJavascriptInterface(new Puente(), "AndroidApp");
        Avisos.crearCanal(this);
        web.setWebChromeClient(new WebChromeClient() {
            /** Permite a la directiva elegir fotos (JPG) desde la galería o la cámara del teléfono. */
            @Override
            public boolean onShowFileChooser(WebView view, ValueCallback<Uri[]> cb, FileChooserParams params) {
                if (fotoCallback != null) fotoCallback.onReceiveValue(null);
                fotoCallback = cb;
                Intent i = new Intent(Intent.ACTION_GET_CONTENT);
                i.addCategory(Intent.CATEGORY_OPENABLE);
                i.setType("image/*");
                i.putExtra(Intent.EXTRA_ALLOW_MULTIPLE, params.getMode() == FileChooserParams.MODE_OPEN_MULTIPLE);
                try {
                    startActivityForResult(Intent.createChooser(i, "Elegir foto"), ELEGIR_FOTO);
                } catch (ActivityNotFoundException e) {
                    fotoCallback = null;
                    return false;
                }
                return true;
            }
        });
        web.setWebViewClient(new WebViewClient() {
            @Override
            public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest req) {
                return abrirFuera(req.getUrl());
            }
        });

        // Android 15+ dibuja la app bajo las barras del sistema: se deja el espacio que corresponde
        web.setOnApplyWindowInsetsListener((v, insets) -> {
            if (Build.VERSION.SDK_INT >= 30) {
                Insets b = insets.getInsets(WindowInsets.Type.systemBars() | WindowInsets.Type.ime());
                v.setPadding(b.left, b.top, b.right, b.bottom);
            } else {
                v.setPadding(insets.getSystemWindowInsetLeft(), insets.getSystemWindowInsetTop(),
                        insets.getSystemWindowInsetRight(), insets.getSystemWindowInsetBottom());
            }
            return insets;
        });

        setContentView(web);
        if (savedInstanceState != null) web.restoreState(savedInstanceState);
        else web.loadUrl(INICIO);

        if (Build.VERSION.SDK_INT >= 33) {
            getOnBackInvokedDispatcher().registerOnBackInvokedCallback(
                    OnBackInvokedDispatcher.PRIORITY_DEFAULT, this::atras);
        }
    }

    /** Enlaces externos (noticias, WhatsApp, correo, teléfono) se abren en su propia app. */
    private boolean abrirFuera(Uri uri) {
        String u = uri.toString();
        if (u.startsWith("file:///android_asset/")) return false;
        try {
            startActivity(new Intent(Intent.ACTION_VIEW, uri));
        } catch (ActivityNotFoundException ignored) { }
        return true;
    }

    /** Botón Atrás: primero navega dentro de la app; si ya está en el inicio, sale. */
    private void atras() {
        web.evaluateJavascript("(window.__appBack&&window.__appBack())?'1':'0'", r -> {
            if (r == null || !r.contains("1")) finish();
        });
    }

    @Override
    @SuppressWarnings("deprecation")
    public void onBackPressed() {
        if (Build.VERSION.SDK_INT >= 33) { super.onBackPressed(); return; }
        atras();
    }

    @Override
    protected void onActivityResult(int req, int res, Intent data) {
        super.onActivityResult(req, res, data);
        if (req != ELEGIR_FOTO || fotoCallback == null) return;
        Uri[] r = null;
        if (res == RESULT_OK && data != null) {
            if (data.getClipData() != null) {
                int n = data.getClipData().getItemCount();
                r = new Uri[n];
                for (int k = 0; k < n; k++) r[k] = data.getClipData().getItemAt(k).getUri();
            } else if (data.getData() != null) {
                r = new Uri[]{ data.getData() };
            }
        }
        fotoCallback.onReceiveValue(r);
        fotoCallback = null;
    }

    @Override
    protected void onSaveInstanceState(Bundle out) {
        super.onSaveInstanceState(out);
        web.saveState(out);
    }

    /** Pide permiso para mostrar notificaciones (Android 13+), solo una vez y tras iniciar sesión. */
    private void pedirPermisoAvisos() {
        if (Build.VERSION.SDK_INT < 33) return;
        if (checkSelfPermission(android.Manifest.permission.POST_NOTIFICATIONS) == PackageManager.PERMISSION_GRANTED) return;
        if (getPreferences(MODE_PRIVATE).getBoolean("permiso_pedido", false)) return;
        getPreferences(MODE_PRIVATE).edit().putBoolean("permiso_pedido", true).apply();
        requestPermissions(new String[]{ android.Manifest.permission.POST_NOTIFICATIONS }, 8);
    }

    /** Lo que la app web puede preguntar a Android. */
    private class Puente {
        @JavascriptInterface public String canal() { return BuildConfig.CANAL; }
        @JavascriptInterface public String version() { return BuildConfig.VERSION_NAME; }
        /** Activa o desactiva el bloqueo de pantallazos (por defecto activado). */
        @JavascriptInterface public void proteger(final boolean si) {
            runOnUiThread(() -> {
                if (si) getWindow().addFlags(WindowManager.LayoutParams.FLAG_SECURE);
                else getWindow().clearFlags(WindowManager.LayoutParams.FLAG_SECURE);
            });
        }

        /** true si este APK puede recibir notificaciones push. */
        @JavascriptInterface public boolean push() {
            try { FirebaseMessaging.getInstance(); return true; } catch (Exception e) { return false; }
        }

        /** El socio activo se suscribe a los avisos de su sindicato (tema «sin2» o «s_<código>»). */
        @JavascriptInterface public boolean suscribir(String tema) {
            if (!temaValido(tema)) return false;
            try {
                FirebaseMessaging.getInstance().subscribeToTopic(tema);
                runOnUiThread(MainActivity.this::pedirPermisoAvisos);
                return true;
            } catch (Exception e) { return false; }
        }

        /** Al cerrar sesión o cambiar de sindicato deja de recibir esos avisos. */
        @JavascriptInterface public boolean desuscribir(String tema) {
            if (!temaValido(tema)) return false;
            try { FirebaseMessaging.getInstance().unsubscribeFromTopic(tema); return true; } catch (Exception e) { return false; }
        }

        private boolean temaValido(String t) { return t != null && t.matches("[a-zA-Z0-9_-]{2,60}"); }
    }
}
