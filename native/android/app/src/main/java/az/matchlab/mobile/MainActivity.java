package az.matchlab.mobile;
import android.app.Activity;
import android.os.Bundle;
import android.os.Build;
import android.content.Intent;
import android.content.pm.ShortcutManager;
import android.content.pm.ShortcutInfo;
import android.graphics.drawable.Icon;
import android.provider.Settings;
import android.graphics.Color;
import android.graphics.Typeface;
import android.net.Uri;
import android.view.Gravity;
import android.view.View;
import android.view.WindowInsets;
import android.view.View;
import android.webkit.*;
import android.widget.*;
import java.io.*;
import java.net.*;
import java.nio.charset.StandardCharsets;
import java.util.*;

public final class MainActivity extends Activity {
    static final String ORIGIN="https://matchlab.local", BACKEND="https://matchlab-az-online.onrender.com";
    static final int BG=Color.rgb(8,14,25);
    WebView web;
    ProgressBar loading;
    TextView failure;
    TextView menuButton;
    int dp(int n){return Math.round(n*getResources().getDisplayMetrics().density);}
    @Override public void onCreate(Bundle state){
        super.onCreate(state);
        getWindow().setStatusBarColor(BG);
        getWindow().setNavigationBarColor(BG);
        FrameLayout root=new FrameLayout(this);
        root.setBackgroundColor(BG);
        web=new WebView(this);web.setBackgroundColor(BG);
        WebSettings settings=web.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setAllowFileAccess(false);
        settings.setAllowContentAccess(false);
        settings.setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);
        settings.setMediaPlaybackRequiresUserGesture(false);
        settings.setUserAgentString(settings.getUserAgentString()+" MATCHLABAZ/0.9.44");
        web.setOverScrollMode(View.OVER_SCROLL_NEVER);
        web.setWebChromeClient(new WebChromeClient());
        web.setWebViewClient(new WebViewClient(){
            @Override public WebResourceResponse shouldInterceptRequest(WebView view,WebResourceRequest req){
                Uri uri=req.getUrl();
                if(!"https".equals(uri.getScheme())||!"matchlab.local".equalsIgnoreCase(uri.getHost()))return null;
                String path=uri.getPath();
                return path!=null&&path.startsWith("/api/")?proxy(uri,req.getMethod()):local(path);
            }
            @Override public boolean shouldOverrideUrlLoading(WebView view,WebResourceRequest req){
                Uri u=req.getUrl();
                if("https".equals(u.getScheme())&&"matchlab.local".equalsIgnoreCase(u.getHost()))return false;
                if("https".equals(u.getScheme())||"http".equals(u.getScheme()))
                    try{startActivity(new Intent(Intent.ACTION_VIEW,u));}catch(Exception ignored){}
                return true;
            }
            @Override public void onPageFinished(WebView view,String url){
                loading.setVisibility(View.GONE);failure.setVisibility(View.GONE);
            }
            @Override public void onReceivedError(WebView view,WebResourceRequest request,WebResourceError err){
                if(request.isForMainFrame()){
                    loading.setVisibility(View.GONE);
                    failure.setText("MATCHLAB AZ interfeysi açıla bilmədi.\nTəkrar yoxlamaq üçün toxun.");
                    failure.setVisibility(View.VISIBLE);
                }
            }
        });
        // Native Android application frame around the real packaged HTML interface.
        LinearLayout shell = new LinearLayout(this);
        shell.setOrientation(LinearLayout.VERTICAL);
        LinearLayout toolbar = new LinearLayout(this);
        toolbar.setBackgroundColor(Color.rgb(13,27,43));
        toolbar.setGravity(Gravity.CENTER_VERTICAL);
        toolbar.setPadding(dp(12),dp(2),dp(8),dp(2));
        ImageView logo = new ImageView(this);
        logo.setImageResource(R.mipmap.ic_launcher);
        logo.setContentDescription("MATCHLAB AZ loqosu");
        LinearLayout.LayoutParams logoParams=new LinearLayout.LayoutParams(dp(38),dp(38));
        logoParams.rightMargin=dp(10);
        toolbar.addView(logo,logoParams);
        LinearLayout titleColumn=new LinearLayout(this);
        titleColumn.setOrientation(LinearLayout.VERTICAL);
        TextView title=new TextView(this);
        title.setText("MATCHLAB AZ");
        title.setTextSize(16);
        title.setTypeface(Typeface.DEFAULT,Typeface.BOLD);
        title.setTextColor(Color.WHITE);
        titleColumn.addView(title);
        TextView subtitle=new TextView(this);
        subtitle.setText("Futbol mərkəzi");
        subtitle.setTextSize(11);
        subtitle.setTextColor(Color.rgb(151,180,194));
        titleColumn.addView(subtitle);
        toolbar.addView(titleColumn,new LinearLayout.LayoutParams(0,-2,1));
        menuButton=new TextView(this);
        menuButton.setText("⋮");
        menuButton.setTextSize(26);
        menuButton.setTextColor(Color.WHITE);
        menuButton.setGravity(Gravity.CENTER);
        menuButton.setContentDescription("Tətbiq menyusu");
        menuButton.setClickable(true);
        menuButton.setFocusable(true);
        menuButton.setOnClickListener(v->showAppMenu());
        toolbar.addView(menuButton,new LinearLayout.LayoutParams(dp(48),dp(48)));
        shell.addView(toolbar,new LinearLayout.LayoutParams(-1,dp(52)));
        shell.addView(web,new LinearLayout.LayoutParams(-1,0,1));
        root.addView(shell,new FrameLayout.LayoutParams(-1,-1));
        loading=new ProgressBar(this);
        root.addView(loading,new FrameLayout.LayoutParams(dp(40),dp(40),Gravity.CENTER));
        failure=new TextView(this);
        failure.setTextColor(Color.WHITE);failure.setTextSize(16);
        failure.setGravity(Gravity.CENTER);failure.setBackgroundColor(BG);
        failure.setPadding(dp(24),dp(24),dp(24),dp(24));
        failure.setVisibility(View.GONE);
        failure.setOnClickListener(v->{failure.setVisibility(View.GONE);loading.setVisibility(View.VISIBLE);web.reload();});
        root.addView(failure,new FrameLayout.LayoutParams(-1,-1));
        if(Build.VERSION.SDK_INT>=30){
            getWindow().setDecorFitsSystemWindows(false);
            root.setOnApplyWindowInsetsListener((v,insets)->{
                android.graphics.Insets safe=insets.getInsets(WindowInsets.Type.systemBars()|WindowInsets.Type.displayCutout());
                root.setPadding(safe.left,safe.top,safe.right,safe.bottom);
                return insets;
            });
        }else root.setFitsSystemWindows(true);
        setContentView(root);
        if(Build.VERSION.SDK_INT>=30)root.requestApplyInsets();
        web.loadUrl(ORIGIN+"/index.html");
    }

    private void showAppMenu(){
        PopupMenu popup=new PopupMenu(this,menuButton);
        popup.getMenu().add(0,1,0,"Ana ekrana qısayol əlavə et");
        popup.getMenu().add(0,2,1,"Yenilə");
        popup.getMenu().add(0,3,2,"Android tətbiq məlumatları");
        popup.getMenu().add(0,4,3,"MATCHLAB AZ haqqında");
        popup.setOnMenuItemClickListener(item->{
            switch(item.getItemId()){
                case 1: requestHomeShortcut();return true;
                case 2:
                    if(web!=null){loading.setVisibility(View.VISIBLE);web.reload();}
                    return true;
                case 3:
                    Intent details=new Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS);
                    details.setData(Uri.parse("package:"+getPackageName()));
                    try{startActivity(details);}
                    catch(Exception ex){Toast.makeText(this,"Android tətbiq ayarları açıla bilmədi",Toast.LENGTH_SHORT).show();}
                    return true;
                case 4:
                    new android.app.AlertDialog.Builder(this)
                        .setTitle("MATCHLAB AZ")
                        .setMessage("Versiya 0.9.44 · Futbol mərkəzi\n\nHTML interfeysi APK daxilindədir. Canlı məlumatlar internet tələb edir.\n\nTətbiqi silmək üçün Android Ayarlar → Tətbiqlər → MATCHLAB AZ.")
                        .setPositiveButton("Bağla",(dialog,which)->dialog.dismiss()).show();
                    return true;
            }
            return false;
        });
        popup.show();
    }
    private void requestHomeShortcut(){
        // Launcher/user approval is required. Never claim the icon was added
        // until Android itself completes the pin request.
        final ShortcutManager manager=(ShortcutManager)getSystemService(SHORTCUT_SERVICE);
        if(manager==null||!manager.isRequestPinShortcutSupported()){
            Toast.makeText(this,"Başlatma ekranı qısayol əlavə etməyi dəstəkləmir",Toast.LENGTH_LONG).show();
            return;
        }
        Intent launch=new Intent(this,MainActivity.class);
        launch.setAction(Intent.ACTION_MAIN);
        launch.addCategory(Intent.CATEGORY_LAUNCHER);
        launch.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK|Intent.FLAG_ACTIVITY_CLEAR_TOP);
        ShortcutInfo shortcut=new ShortcutInfo.Builder(this,"matchlab-home")
            .setShortLabel("MATCHLAB AZ")
            .setLongLabel("MATCHLAB AZ — Futbol mərkəzi")
            .setIcon(Icon.createWithResource(this,R.mipmap.ic_launcher))
            .setIntent(launch)
            .build();
        new Thread(()->{
            boolean accepted=false;
            try{accepted=manager.requestPinShortcut(shortcut,null);}catch(Exception ignored){}
            final boolean requested=accepted;
            runOnUiThread(()->Toast.makeText(this,requested
                ?"Ana ekran qısayolunu əlavə etmə sorğusunu təsdiqlə"
                :"Qısayol sorğusu bu başlatma ekranında qəbul edilmədi",
                Toast.LENGTH_LONG).show());
        }).start();
    }

    static final Map<String,String> MIME=new HashMap<>();
    static{
        MIME.put("/index.html","text/html");MIME.put("/styles.css","text/css");
        MIME.put("/app.js","text/javascript");MIME.put("/catalog.js","text/javascript");
        MIME.put("/featured_media.js","text/javascript");
        MIME.put("/coach_tactics.js","text/javascript");
        MIME.put("/assets/icon.svg","image/svg+xml");MIME.put("/shell.css","text/css");MIME.put("/shell.js","text/javascript");
        MIME.put("/install.js","text/javascript");MIME.put("/service-worker.js","text/javascript");
        MIME.put("/manifest.webmanifest","application/manifest+json");
        MIME.put("/assets/pwa-192.png","image/png");MIME.put("/assets/pwa-512.png","image/png");MIME.put("/assets/pwa-512-maskable.png","image/png");
    }
    static WebResourceResponse response(int code,String mime,byte[] bytes){
        Map<String,String> h=new HashMap<>();
        h.put("Cache-Control","no-store");
        h.put("X-Content-Type-Options","nosniff");
        return new WebResourceResponse(mime,"UTF-8",code,code<400?"OK":"Unavailable",h,new ByteArrayInputStream(bytes));
    }
    static WebResourceResponse unavailable(){
        return response(503,"application/json","{\"available\":false,\"error\":\"Server bağlantısı yoxdur\"}".getBytes(StandardCharsets.UTF_8));
    }
    WebResourceResponse local(String path){
        if(path==null||"/".equals(path))path="/index.html";
        String mime=MIME.get(path);
        if(mime==null)return response(404,"text/plain","Not Found".getBytes(StandardCharsets.UTF_8));
        try(InputStream in=getAssets().open("web/"+path.substring(1));ByteArrayOutputStream out=new ByteArrayOutputStream()){
            byte[] b=new byte[8192];int n;
            while((n=in.read(b))!=-1)out.write(b,0,n);
            byte[] bytes=out.toByteArray();
            return response(200,mime,bytes);
        }catch(Exception ex){return response(500,"text/plain","HTML asset missing".getBytes(StandardCharsets.UTF_8));}
    }
    WebResourceResponse proxy(Uri uri,String method){
        if(!"GET".equalsIgnoreCase(method))
            return response(403,"application/json","{\"error\":\"Bu əməliyyat bağlıdır\"}".getBytes(StandardCharsets.UTF_8));
        HttpURLConnection c=null;
        try{
            c=(HttpURLConnection)new URL(BACKEND+uri.getEncodedPath()+
                (uri.getEncodedQuery()==null?"":"?"+uri.getEncodedQuery())).openConnection();
            c.setConnectTimeout(17000);c.setReadTimeout(50000);
            c.setRequestProperty("Accept","application/json");
            c.setRequestProperty("User-Agent","MATCHLABAZ-HTML/0.9.44");
            int code=c.getResponseCode();
            InputStream stream=code>=400?c.getErrorStream():c.getInputStream();
            if(stream==null)return unavailable();
            try(InputStream in=stream;ByteArrayOutputStream out=new ByteArrayOutputStream()){
                byte[] b=new byte[8192];int n;
                while((n=in.read(b))!=-1){
                    out.write(b,0,n);
                    if(out.size()>8000000)return unavailable();
                }
                return response(code,"application/json",out.toByteArray());
            }
        }catch(Exception ex){return unavailable();}
        finally{if(c!=null)c.disconnect();}
    }
    @Override public void onBackPressed(){if(web!=null&&web.canGoBack())web.goBack();else super.onBackPressed();}
    @Override protected void onDestroy(){if(web!=null){web.stopLoading();web.destroy();web=null;}super.onDestroy();}
}
