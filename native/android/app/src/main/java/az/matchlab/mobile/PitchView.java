package az.matchlab.mobile;

import android.app.AlertDialog;
import android.content.Context;
import android.content.SharedPreferences;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.Path;
import android.graphics.RectF;
import android.view.MotionEvent;
import android.view.View;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.Toast;
import java.util.Locale;

/** MATCHLAB native tactical editor — draggable, editable, persistent local plans.
 * These positions are user tactics, never claims about real football lineups.
 */
public final class PitchView extends View {
    private final Paint p=new Paint(Paint.ANTI_ALIAS_FLAG);
    private final String formation;
    private final SharedPreferences prefs;
    private final float[] x=new float[11],y=new float[11];
    private final String[] names=new String[11],numbers=new String[11];
    private int dragging=-1;
    private float downX,downY;
    private boolean changed=false;
    private long pressedAt;
    private int dp(float n){return Math.round(n*getResources().getDisplayMetrics().density);}
    public PitchView(Context context,String formation){
        super(context);this.formation=formation;
        prefs=context.getSharedPreferences("matchlab_tactics",Context.MODE_PRIVATE);
        setLayerType(View.LAYER_TYPE_SOFTWARE,null);
        setContentDescription("İnteraktiv taktika meydançası, 11 oyunçu");
        load();
    }
    private float clamp(float z,float a,float b){return Math.max(a,Math.min(z,b));}
    private void defaults(){
        int[] layers=new int[formation.split("-").length+1];layers[0]=1;
        String[] parts=formation.split("-");
        for(int i=0;i<parts.length;i++){
            try{layers[i+1]=Integer.parseInt(parts[i]);}catch(Exception ignored){layers[i+1]=0;}
        }
        int n=0;
        for(int row=0;row<layers.length;row++){
            int count=layers[row];
            float by=.88f-row*(.75f/(layers.length-1));
            for(int col=0;col<count&&n<11;col++,n++){
                x[n]=(col+1f)/(count+1f);y[n]=by;
            }
        }
        for(int i=0;i<11;i++){names[i]="";numbers[i]=String.valueOf(i+1);}
    }
    private void load(){
        defaults();
        for(int i=0;i<11;i++){
            String key=formation+"_"+i;
            x[i]=clamp(prefs.getFloat(key+"_x",x[i]),.09f,.91f);
            y[i]=clamp(prefs.getFloat(key+"_y",y[i]),.09f,.91f);
            names[i]=prefs.getString(key+"_name","");
            numbers[i]=prefs.getString(key+"_no",String.valueOf(i+1));
        }
    }
    private void save(){
        SharedPreferences.Editor edit=prefs.edit();
        for(int i=0;i<11;i++){
            String k=formation+"_"+i;
            edit.putFloat(k+"_x",x[i]);edit.putFloat(k+"_y",y[i]);
            edit.putString(k+"_name",names[i]);edit.putString(k+"_no",numbers[i]);
        }
        edit.apply();
    }
    public void reset(){
        SharedPreferences.Editor edit=prefs.edit();
        for(int i=0;i<11;i++){
            String k=formation+"_"+i;
            for(String suffix:new String[]{"_x","_y","_name","_no"})edit.remove(k+suffix);
        }
        edit.apply();defaults();invalidate();
    }
    public String exportText(){
        StringBuilder b=new StringBuilder("MATCHLAB AZ · Taktiki plan "+formation);
        for(int i=0;i<11;i++)b.append("\n").append(numbers[i]).append(". ")
            .append(names[i].trim().isEmpty()?"Mövqe "+(i+1):names[i])
            .append(String.format(Locale.US," (%.0f%%, %.0f%%)",x[i]*100,y[i]*100));
        b.append("\nİstifadəçinin yaratdığı məşq planı — real oyun heyəti deyil.");
        return b.toString();
    }
    private RectF field(){
        float inset=dp(9);
        return new RectF(inset,inset,getWidth()-inset,getHeight()-inset);
    }
    private void stroke(int color,float width){
        p.setColor(color);p.setStyle(Paint.Style.STROKE);p.setStrokeWidth(width);
    }
    private void drawPlayer(Canvas c,RectF f,int index){
        float px=f.left+x[index]*f.width(),py=f.top+y[index]*f.height();
        float radius=dp(17);
        p.setStyle(Paint.Style.FILL);p.setColor(Color.argb(78,0,0,0));
        c.drawCircle(px,py+dp(2),radius+dp(2),p);
        p.setColor(dragging==index?Color.WHITE:Color.rgb(170,245,111));
        c.drawCircle(px,py,radius,p);
        p.setColor(Color.rgb(10,35,36));p.setTextSize(dp(12));
        p.setTypeface(android.graphics.Typeface.create(android.graphics.Typeface.DEFAULT,android.graphics.Typeface.BOLD));
        p.setTextAlign(Paint.Align.CENTER);
        c.drawText(numbers[index],px,py+dp(4),p);
        if(!names[index].isEmpty()){
            String label=names[index].length()>13?names[index].substring(0,13)+"…":names[index];
            p.setColor(Color.argb(210,7,25,34));
            p.setTextSize(dp(10));
            float tw=p.measureText(label);
            RectF background=new RectF(px-tw/2-dp(5),py+radius+dp(4),px+tw/2+dp(5),py+radius+dp(20));
            c.drawRoundRect(background,dp(5),dp(5),p);
            p.setColor(Color.WHITE);
            c.drawText(label,px,py+radius+dp(16),p);
        }
    }
    @Override protected void onDraw(Canvas c){
        super.onDraw(c);
        RectF f=field();if(f.width()<=0||f.height()<=0)return;
        p.setStyle(Paint.Style.FILL);
        p.setColor(Color.rgb(19,88,67));c.drawRoundRect(f,dp(17),dp(17),p);
        for(int stripe=0;stripe<8;stripe++){
            p.setColor(stripe%2==0?Color.rgb(26,102,77):Color.rgb(21,95,71));
            c.save();c.clipRect(f);c.drawRect(f.left,f.top+stripe*f.height()/8f,f.right,f.top+(stripe+1)*f.height()/8f,p);c.restore();
        }
        stroke(Color.argb(190,238,250,238),dp(1.4f));
        RectF inner=new RectF(f.left+dp(11),f.top+dp(11),f.right-dp(11),f.bottom-dp(11));
        c.drawRect(inner,p);
        c.drawLine(inner.left,inner.centerY(),inner.right,inner.centerY(),p);
        c.drawCircle(inner.centerX(),inner.centerY(),dp(36),p);
        float boxW=inner.width()*.58f,boxH=inner.height()*.14f;
        c.drawRect(inner.centerX()-boxW/2,inner.top,inner.centerX()+boxW/2,inner.top+boxH,p);
        c.drawRect(inner.centerX()-boxW/2,inner.bottom-boxH,inner.centerX()+boxW/2,inner.bottom,p);
        c.drawCircle(inner.centerX(),inner.centerY(),dp(2),p);
        for(int i=0;i<11;i++)drawPlayer(c,inner,i);
    }
    private int findPlayer(float px,float py){
        RectF f=field();
        RectF inner=new RectF(f.left+dp(11),f.top+dp(11),f.right-dp(11),f.bottom-dp(11));
        float max=dp(32),nearest=max*max;
        int best=-1;
        for(int i=10;i>=0;i--){
            float dx=px-(inner.left+x[i]*inner.width());
            float dy=py-(inner.top+y[i]*inner.height());
            float dist=dx*dx+dy*dy;
            if(dist<nearest){nearest=dist;best=i;}
        }
        return best;
    }
    private void editPlayer(int index){
        Context ctx=getContext();
        LinearLayout layout=new LinearLayout(ctx);
        layout.setPadding(dp(20),dp(8),dp(20),0);
        layout.setOrientation(LinearLayout.VERTICAL);
        EditText player=new EditText(ctx);player.setHint("Ad (istəyə bağlı)");
        player.setSingleLine(true);player.setText(names[index]);layout.addView(player);
        EditText no=new EditText(ctx);no.setHint("Forma nömrəsi");
        no.setSingleLine(true);no.setText(numbers[index]);layout.addView(no);
        new AlertDialog.Builder(ctx).setTitle("Mövqe "+(index+1))
            .setView(layout).setNegativeButton("Ləğv et",null)
            .setPositiveButton("Saxla",(d,which)->{
                names[index]=player.getText().toString().trim();
                numbers[index]=no.getText().toString().trim();
                if(numbers[index].isEmpty())numbers[index]=String.valueOf(index+1);
                if(numbers[index].length()>3)numbers[index]=numbers[index].substring(0,3);
                if(names[index].length()>30)names[index]=names[index].substring(0,30);
                save();invalidate();
            }).show();
    }
    @Override public boolean onTouchEvent(MotionEvent event){
        int action=event.getActionMasked();
        if(action==MotionEvent.ACTION_DOWN){
            dragging=findPlayer(event.getX(),event.getY());
            if(dragging<0)return false;
            downX=event.getX();downY=event.getY();changed=false;
            pressedAt=System.currentTimeMillis();
            getParent().requestDisallowInterceptTouchEvent(true);
            invalidate();return true;
        }
        if(action==MotionEvent.ACTION_MOVE&&dragging>=0){
            float dx=event.getX()-downX,dy=event.getY()-downY;
            if(Math.abs(dx)>dp(8)||Math.abs(dy)>dp(8))changed=true;
            if(changed){
                RectF f=field();
                RectF inner=new RectF(f.left+dp(11),f.top+dp(11),f.right-dp(11),f.bottom-dp(11));
                x[dragging]=clamp((event.getX()-inner.left)/inner.width(),.07f,.93f);
                y[dragging]=clamp((event.getY()-inner.top)/inner.height(),.08f,.92f);
                invalidate();
            }
            return true;
        }
        if((action==MotionEvent.ACTION_UP||action==MotionEvent.ACTION_CANCEL)&&dragging>=0){
            int selected=dragging;dragging=-1;getParent().requestDisallowInterceptTouchEvent(false);
            if(changed)save();
            else if(action==MotionEvent.ACTION_UP&&System.currentTimeMillis()-pressedAt<850)editPlayer(selected);
            invalidate();return true;
        }
        return super.onTouchEvent(event);
    }
}
