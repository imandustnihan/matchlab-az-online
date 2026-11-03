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
import java.io.File;
import java.io.FileOutputStream;
import java.security.MessageDigest;
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
    private static final LruCache<String,Bitmap> CACHE=new LruCache<String,Bitmap>(12288){
        @Override protected int sizeOf(String url,Bitmap bitmap){
            return Math.max(1,bitmap.getByteCount()/1024);
        }
    };
    private final Context appContext;
    private final ImageView picture;
    private final TextView initial;
    private int dp(float n){return Math.round(n*getResources().getDisplayMetrics().density);}
    public TeamBadge(Context context,String name,String imageUrl,int size) {
        super(context);
        appContext=context.getApplicationContext();
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
    private File diskEntry(String url){
        try{
            MessageDigest sha=MessageDigest.getInstance("SHA-256");
            byte[] bytes=sha.digest(url.getBytes("UTF-8"));
            StringBuilder key=new StringBuilder();
            for(byte b:bytes)key.append(String.format(java.util.Locale.ROOT,"%02x",b&0xff));
            File dir=new File(appContext.getCacheDir(),"verified_badges");
            if(!dir.exists())dir.mkdirs();
            return new File(dir,key+".img");
        }catch(Exception ignored){return null;}
    }
    private Bitmap decodeDisk(File file){
        if(file==null||!file.isFile()||file.length()>900000)return null;
        BitmapFactory.Options opts=new BitmapFactory.Options();
        opts.inJustDecodeBounds=true;BitmapFactory.decodeFile(file.getAbsolutePath(),opts);
        if(opts.outHeight<1||opts.outWidth<1)return null;
        opts.inSampleSize=Math.max(1,Math.max(opts.outHeight,opts.outWidth)/256);
        opts.inJustDecodeBounds=false;
        return BitmapFactory.decodeFile(file.getAbsolutePath(),opts);
    }
    private void load(String url){
        Bitmap cached=CACHE.get(url);
        if(cached!=null){apply(url,cached);return;}
        setTag(url);
        POOL.execute(()->{
            Bitmap bmp=null;
            File disk=diskEntry(url);
            bmp=decodeDisk(disk);
            if(bmp!=null){CACHE.put(url,bmp);final Bitmap ready=bmp;post(()->apply(url,ready));return;}
            HttpURLConnection connection=null;
            try{
                URL uri=new URL(url);
                if(!"https".equals(uri.getProtocol()))return;
                connection=(HttpURLConnection)uri.openConnection();
                connection.setConnectTimeout(4500);
                connection.setReadTimeout(6500);
                connection.setInstanceFollowRedirects(false);
                connection.setRequestProperty("User-Agent","MATCHLABAZ-Android/0.9.52");
                if(connection.getResponseCode()!=200)return;
                String mime=connection.getContentType();
                if(mime==null||!mime.toLowerCase().startsWith("image/"))return;
                int length=connection.getContentLength();
                if(length>900_000)return;
                try(InputStream input=connection.getInputStream();ByteArrayOutputStream bytes=new ByteArrayOutputStream()){
                    byte[] buffer=new byte[4096];int n;
                    while((n=input.read(buffer))!=-1){
                        bytes.write(buffer,0,n);
                        if(bytes.size()>900_000)return;
                    }
                    byte[] data=bytes.toByteArray();
                    BitmapFactory.Options opts=new BitmapFactory.Options();
                    opts.inJustDecodeBounds=true;
                    BitmapFactory.decodeByteArray(data,0,data.length,opts);
                    if(opts.outHeight<1||opts.outWidth<1)return;
                    opts.inSampleSize=Math.max(1,Math.max(opts.outHeight,opts.outWidth)/256);
                    opts.inJustDecodeBounds=false;
                    bmp=BitmapFactory.decodeByteArray(data,0,data.length,opts);
                    if(bmp!=null&&disk!=null){
                        try(FileOutputStream saved=new FileOutputStream(disk)){saved.write(data);}
                        catch(Exception ignored){}
                    }
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
