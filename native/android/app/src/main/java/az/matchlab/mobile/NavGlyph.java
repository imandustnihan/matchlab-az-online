package az.matchlab.mobile;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.Path;
import android.view.View;

/** Small, original native vector icons for the MATCHLAB AZ navigation. */
public final class NavGlyph extends View {
    private final String kind;
    private final int color;
    private final Paint paint=new Paint(Paint.ANTI_ALIAS_FLAG);
    public NavGlyph(Context context,String kind,int color) {
        super(context);
        this.kind=kind;
        this.color=color;
        setImportantForAccessibility(View.IMPORTANT_FOR_ACCESSIBILITY_NO);
    }
    private void stroke(float width) {
        paint.setColor(color);
        paint.setStyle(Paint.Style.STROKE);
        paint.setStrokeWidth(width);
        paint.setStrokeCap(Paint.Cap.ROUND);
        paint.setStrokeJoin(Paint.Join.ROUND);
    }
    @Override protected void onDraw(Canvas raw) {
        super.onDraw(raw);
        final int saved=raw.save();
        float scale=Math.min(getWidth(),getHeight())/24f;
        raw.translate((getWidth()-24f*scale)/2f,(getHeight()-24f*scale)/2f);
        raw.scale(scale,scale);
        paint.setColor(color);
        paint.setStyle(Paint.Style.FILL);
        switch(kind) {
            case "matches":
                stroke(1.7f);
                raw.drawCircle(12,12,9,paint);
                Path pent=new Path();
                pent.moveTo(12,7);pent.lineTo(16.2f,10.2f);pent.lineTo(14.7f,15);
                pent.lineTo(9.3f,15);pent.lineTo(7.8f,10.2f);pent.close();
                raw.drawPath(pent,paint);
                raw.drawLine(8.8f,9.8f,5.2f,7.3f,paint);
                raw.drawLine(15.2f,9.8f,18.8f,7.3f,paint);
                raw.drawLine(10,15,8,20,paint);
                raw.drawLine(14,15,16,20,paint);
                break;
            case "standings":
                stroke(1.8f);
                raw.drawLine(4,4,20,4,paint);
                for(int i=0;i<3;i++) {
                    float y=8+i*5.4f;
                    raw.drawLine(4,y,7,y,paint);
                    raw.drawLine(10,y,20,y,paint);
                }
                break;
            case "search":
                stroke(2f);
                raw.drawCircle(10.5f,10.5f,6.4f,paint);
                raw.drawLine(15.5f,15.5f,20.7f,20.7f,paint);
                break;
            case "favorites":
                stroke(1.8f);
                Path star=new Path();
                for(int i=0;i<10;i++) {
                    double a=-Math.PI/2 + i*Math.PI/5;
                    float radius=i%2==0?9.5f:4.5f;
                    float x=12+(float)Math.cos(a)*radius;
                    float y=12+(float)Math.sin(a)*radius;
                    if(i==0)star.moveTo(x,y);else star.lineTo(x,y);
                }
                star.close();raw.drawPath(star,paint);
                break;
            case "tactics":
                stroke(1.6f);
                raw.drawRoundRect(3,3,21,21,2,2,paint);
                raw.drawLine(3,12,21,12,paint);
                raw.drawCircle(12,12,3,paint);
                raw.drawCircle(8,7,1,paint);
                raw.drawCircle(16,17,1,paint);
                break;
            default:raw.drawCircle(12,12,6,paint);
        }
        raw.restoreToCount(saved);
    }
}
