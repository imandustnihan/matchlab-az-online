package az.matchlab.mobile;

import android.app.Activity;
import android.content.Intent;
import android.graphics.Color;
import android.graphics.Typeface;
import android.net.Uri;
import android.os.Bundle;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.webkit.WebResourceRequest;
import android.webkit.WebResourceError;
import android.webkit.WebResourceResponse;
import android.webkit.WebSettings;
import android.webkit.CookieManager;
import android.widget.Button;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.view.WindowInsets;
import org.json.JSONObject;
import java.io.InputStream;
import java.io.ByteArrayOutputStream;
import java.nio.charset.StandardCharsets;

public final class MainActivity extends Activity {
    private static final String SITE="https://matchlab-az-online.onrender.com/";
    private static final String HOST="matchlab-az-online.onrender.com";
    private FrameLayout frame;
    private WebView browser;
    private LinearLayout status;
    private boolean failed=false;

    @Override public void onCreate(Bundle saved){
        super.onCreate(saved);
        getWindow().setStatusBarColor(Color.rgb(9,19,31));
        getWindow().setNavigationBarColor(Color.rgb(9,19,31));
        frame=new FrameLayout(this);
        browser=new WebView(this);
        browser.setBackgroundColor(Color.rgb(10,20,31));
        WebSettings settings=browser.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);
        settings.setAllowFileAccess(false);
        settings.setJavaScriptCanOpenWindowsAutomatically(false);
        settings.setMediaPlaybackRequiresUserGesture(true);
        settings.setUserAgentString(settings.getUserAgentString()+" MATCHLABAZ-Mobile/0.9.28");
        CookieManager.getInstance().setAcceptThirdPartyCookies(browser,false);
        browser.setWebViewClient(new WebViewClient(){
            @Override public void onPageStarted(WebView v,String u,android.graphics.Bitmap icon){failed=false;status("Yüklənir…",false);}
            @Override public boolean shouldOverrideUrlLoading(WebView v,WebResourceRequest req){
                Uri u=req.getUrl();
                if("https".equals(u.getScheme())&&HOST.equalsIgnoreCase(u.getHost())) return false;
                if("https".equals(u.getScheme())){
                    try{startActivity(new Intent(Intent.ACTION_VIEW,u));}catch(Exception ignored){}
                }
                return true;
            }
            @Override public void onReceivedError(WebView v,WebResourceRequest req,WebResourceError e){
                if(req!=null&&req.isForMainFrame()){failed=true;status("Serverə qoşulmaq mümkün olmadı",true);}
            }
            @Override public void onReceivedHttpError(WebView v,WebResourceRequest req,WebResourceResponse res){
                if(req!=null&&req.isForMainFrame()&&res!=null&&res.getStatusCode()>=500){
                    failed=true;status("Server cavab vermir",true);
                }
            }
            @Override public void onPageFinished(WebView v,String u){
                if(!u.startsWith(SITE))return;
                if(!failed){clearStatus();injectUI();}
            }
        });
        frame.addView(browser,new FrameLayout.LayoutParams(-1,-1));
        frame.setOnApplyWindowInsetsListener((v,insets)->{
            frame.setPadding(insets.getSystemWindowInsetLeft(),insets.getSystemWindowInsetTop(),insets.getSystemWindowInsetRight(),insets.getSystemWindowInsetBottom());
            return insets;
        });
        setContentView(frame);
        status("MATCHLAB AZ açılır…",false);
        browser.loadUrl(SITE);
    }
    private String read(String name)throws Exception{
        try(InputStream in=getAssets().open(name);ByteArrayOutputStream out=new ByteArrayOutputStream()){
            byte[] buf=new byte[4096];int count;
            while((count=in.read(buf))!=-1)out.write(buf,0,count);
            return out.toString(StandardCharsets.UTF_8.name());
        }
    }
    private void injectUI(){
        try{
            String css=read("simple-ui.css");
            browser.evaluateJavascript("(function(){if(document.getElementById('matchlab-native-css'))return;var s=document.createElement('style');s.id='matchlab-native-css';s.textContent="+JSONObject.quote(css)+";document.head.appendChild(s)})()",null);
            browser.evaluateJavascript(read("simple-ui.js"),null);
        }catch(Exception ignored){}
    }
    private int dp(int value){return Math.round(value*getResources().getDisplayMetrics().density);}
    private void clearStatus(){
        if(status!=null){frame.removeView(status);status=null;}
        browser.setVisibility(View.VISIBLE);
    }
    private void status(String message,boolean retry){
        if(status!=null)frame.removeView(status);
        status=new LinearLayout(this);status.setOrientation(LinearLayout.VERTICAL);status.setGravity(Gravity.CENTER);
        status.setPadding(dp(24),dp(24),dp(24),dp(24));status.setBackgroundColor(Color.rgb(10,20,31));
        TextView title=new TextView(this);title.setText("MATCHLAB AZ");title.setTextSize(28);
        title.setTextColor(Color.rgb(178,247,109));title.setTypeface(null,Typeface.BOLD);title.setGravity(Gravity.CENTER);
        status.addView(title);
        TextView detail=new TextView(this);detail.setText(message);detail.setTextSize(16);detail.setTextColor(Color.WHITE);
        detail.setGravity(Gravity.CENTER);detail.setPadding(0,dp(24),0,dp(24));status.addView(detail);
        if(retry){
            TextView hint=new TextView(this);hint.setText("Pulsuz server yuxu rejimində ola bilər.");hint.setTextColor(Color.LTGRAY);
            status.addView(hint);
            Button button=new Button(this);button.setText("Yenidən yoxla");button.setAllCaps(false);
            button.setOnClickListener(v->{clearStatus();browser.loadUrl(SITE);});status.addView(button);
        }
        browser.setVisibility(View.INVISIBLE);
        frame.addView(status,new FrameLayout.LayoutParams(-1,-1));
    }
    @Override public void onBackPressed(){
        if(browser!=null&&browser.canGoBack())browser.goBack();else super.onBackPressed();
    }
    @Override protected void onDestroy(){
        if(browser!=null){browser.stopLoading();browser.destroy();}
        super.onDestroy();
    }
}
