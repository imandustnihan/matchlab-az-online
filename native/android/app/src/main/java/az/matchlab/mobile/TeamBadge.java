package az.matchlab.mobile;

import android.content.Context;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.util.LruCache;
import android.view.Gravity;
import android.widget.FrameLayout;
import android.widget.ImageView;
import android.widget.TextView;
import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/** Shows real source-provided team badges, or neutral initials when unavailable.
 * Never downloads images over cleartext or invents club identities.
 */
public final class TeamBadge extends FrameLayout {
    private static final ExecutorService POOL=Executors.newFixedThreadPool(3);
    private static final LruCache<String,Bitmap> CACHE=new LruCache<String,Bitmap>(80){
        @Override protected int sizeOf(String url,Bitmap bitmap){
            return Math.max(1,bitmap.getByteCount()/1024);
        }
    };
    private final ImageView picture;
    private final TextView initial;
    private int dp(float n){return Math.round(n*getResources().getDisplayMetrics().density);}
    public TeamBadge(Context context,String name,String imageUrl,int size) {
        super(context);
        GradientDrawable bg=new GradientDrawable();
        bg.setColor(Color.rgb(34,52,66));bg.setCornerRadius(dp(10));
        bg.setStroke(dp(1),Color.rgb(54,78,92));
        setBackground(bg);
        setClipToOutline(true);
        initial=new TextView(context);
        String title=name==null?"":name.trim();
        initial.setText(title.length()>0?title.substring(0,1).toUpperCase():"•");
        initial.setTextSize(13);
        initial.setTextColor(Color.rgb(176,235,140));
        initial.setTypeface(Typeface.DEFAULT,Typeface.BOLD);
        initial.setGravity(Gravity.CENTER);
        addView(initial,new FrameLayout.LayoutParams(-1,-1));
        picture=new ImageView(context);
        picture.setScaleType(ImageView.ScaleType.FIT_CENTER);
        picture.setPadding(dp(3),dp(3),dp(3),dp(3));
        picture.setVisibility(GONE);
        addView(picture,new FrameLayout.LayoutParams(-1,-1));
        setContentDescription(title);
        setMinimumWidth(dp(size));setMinimumHeight(dp(size));
        if(imageUrl!=null&&imageUrl.startsWith("https://")&&imageUrl.length()<700)load(imageUrl);
    }
    private void load(String url){
        Bitmap cached=CACHE.get(url);
        if(cached!=null){apply(url,cached);return;}
        setTag(url);
        POOL.execute(()->{
            Bitmap bmp=null;
            HttpURLConnection connection=null;
            try{
                URL uri=new URL(url);
                if(!"https".equals(uri.getProtocol()))return;
                connection=(HttpURLConnection)uri.openConnection();
                connection.setConnectTimeout(4500);
                connection.setReadTimeout(6500);
                connection.setInstanceFollowRedirects(false);
                connection.setRequestProperty("User-Agent","MATCHLABAZ-Android/0.9.47");
                if(connection.getResponseCode()!=200)return;
                String mime=connection.getContentType();
                if(mime==null||!mime.toLowerCase().startsWith("image/"))return;
                int length=connection.getContentLength();
                if(length>500_000)return;
                try(InputStream input=connection.getInputStream();ByteArrayOutputStream bytes=new ByteArrayOutputStream()){
                    byte[] buffer=new byte[4096];int n;
                    while((n=input.read(buffer))!=-1){
                        bytes.write(buffer,0,n);
                        if(bytes.size()>500_000)return;
                    }
                    byte[] data=bytes.toByteArray();
                    BitmapFactory.Options opts=new BitmapFactory.Options();
                    opts.inJustDecodeBounds=true;
                    BitmapFactory.decodeByteArray(data,0,data.length,opts);
                    if(opts.outHeight<1||opts.outWidth<1)return;
                    opts.inSampleSize=Math.max(1,Math.max(opts.outHeight,opts.outWidth)/128);
                    opts.inJustDecodeBounds=false;
                    bmp=BitmapFactory.decodeByteArray(data,0,data.length,opts);
                }
                if(bmp!=null)CACHE.put(url,bmp);
            }catch(Exception ignored){/* neutral initials remain */ }
            finally{if(connection!=null)connection.disconnect();}
            final Bitmap result=bmp;
            if(result!=null)post(()->apply(url,result));
        });
    }
    private void apply(String url,Bitmap bitmap){
        if(!url.equals(getTag())&&getTag()!=null)return;
        picture.setImageBitmap(bitmap);picture.setVisibility(VISIBLE);
        initial.setVisibility(GONE);
    }
}
