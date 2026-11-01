package az.matchlab.mobile;
import android.content.Context;
import android.graphics.*;
import android.view.View;
public final class PitchView extends View {
    private final Paint p=new Paint(3);
    private final String formation;
    public PitchView(Context context,String formation){super(context);this.formation=formation;setLayerType(View.LAYER_TYPE_SOFTWARE,null);}
    @Override protected void onDraw(Canvas canvas){
        super.onDraw(canvas);
        float w=getWidth(),h=getHeight(),left=20,top=15,right=w-20,bottom=h-15;
        p.setStyle(Paint.Style.FILL);p.setColor(Color.rgb(23,96,69));canvas.drawRoundRect(left,top,right,bottom,16,16,p);
        p.setColor(Color.argb(180,235,245,235));p.setStyle(Paint.Style.STROKE);p.setStrokeWidth(2.5f);
        canvas.drawRect(left+8,top+8,right-8,bottom-8,p);
        float cx=w/2,cy=h/2;
        canvas.drawLine(left+8,cy,right-8,cy,p);canvas.drawCircle(cx,cy,45,p);
        canvas.drawRect(cx-w*.2f,top+8,cx+w*.2f,top+h*.17f,p);
        canvas.drawRect(cx-w*.2f,bottom-h*.17f,cx+w*.2f,bottom-8,p);
        String[] parts=formation.split("-");
        int[] layers=new int[parts.length+1];layers[0]=1;
        for(int i=0;i<parts.length;i++)try{layers[i+1]=Integer.parseInt(parts[i]);}catch(Exception ignored){}
        int n=1;
        for(int r=0;r<layers.length;r++){
            float y=bottom-45-r*(h-110)/(layers.length-1);
            for(int c=0;c<layers[r];c++){
                float x=left+((c+1f)/(layers[r]+1f))*(right-left);
                p.setStyle(Paint.Style.FILL);p.setColor(Color.rgb(155,236,118));
                canvas.drawCircle(x,y,17,p);
                p.setColor(Color.rgb(10,25,29));p.setTextSize(14);p.setTypeface(Typeface.create(Typeface.DEFAULT,Typeface.BOLD));
                p.setTextAlign(Paint.Align.CENTER);canvas.drawText(String.valueOf(n++),x,y+5,p);
            }
        }
    }
}
