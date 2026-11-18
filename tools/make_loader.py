"""Genera assets/index.html: lanzador con la app incluida (base64) que nunca navega a otra página."""
import base64, re, sys
d=sys.argv[1]; apk_ver=int(sys.argv[2]); out=sys.argv[3] if len(sys.argv)>3 else d+'/index.html'
app=open(d+'/app.html',encoding='utf-8').read()
ver=int(re.search(r'var APP_VER=(\d+);',app).group(1))
b64=base64.b64encode(app.encode('utf-8')).decode()
html='''<!doctype html>
<html lang="es-CL"><head><meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"/>
<title>Sindicato N°2</title><style>html,body{margin:0;background:#0f4643;height:100%%}</style></head>
<body>
<script>
/* Lanzador: muestra la app incluida en el APK o una versión más nueva descargada desde GitHub.
   Nunca navega a otra página: el APK no tiene WebViewClient y Android enviaría la navegación fuera de la app. */
(function(){
  var APK_VER=%d, BUNDLED_APP=%d, B64="%s";
  function bundled(){var bin=atob(B64),u=new Uint8Array(bin.length);for(var i=0;i<bin.length;i++)u[i]=bin.charCodeAt(i);return new TextDecoder('utf-8').decode(u)}
  try{var CH=window.AndroidApp&&AndroidApp.canal&&AndroidApp.canal();if(CH)localStorage.setItem('sin2_canal',CH)}catch(e){}
  function pick(){
    var html=null,ver=0;
    try{
      localStorage.setItem('sin2_apk_ver',String(APK_VER));
      ver=+localStorage.getItem('sin2_app_ver')||0;html=localStorage.getItem('sin2_app_html');
      var pend=+localStorage.getItem('sin2_boot_pending')||0;
      if(pend&&pend===ver){localStorage.setItem('sin2_app_bad',String(ver));localStorage.removeItem('sin2_app_html');localStorage.removeItem('sin2_app_ver');localStorage.removeItem('sin2_boot_pending');html=null;ver=0}
      if(html&&ver>BUNDLED_APP&&html.indexOf('SIN2-APP-OK')>0){localStorage.setItem('sin2_boot_pending',String(ver));return html}
    }catch(e){}
    return bundled();
  }
  window.__sin2Boot=function(){var h=pick();setTimeout(function(){document.open();document.write(h);document.close()},0)};
  window.__sin2Boot();
})();
</script>
</body></html>
''' % (apk_ver, ver, b64)
import os; os.makedirs(os.path.dirname(out) or '.', exist_ok=True); open(out,'w',encoding='utf-8').write(html); print('loader ok, app',ver,'apk',apk_ver,len(html))
