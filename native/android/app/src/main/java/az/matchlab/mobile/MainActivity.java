package az.matchlab.mobile;

import android.app.Activity;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.content.Context;
import android.content.SharedPreferences;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.view.Gravity;
import android.view.WindowInsets;
import android.os.Build;
import android.graphics.Rect;
import android.view.View;
import android.view.ViewGroup;
import android.widget.*;
import org.json.*;
import java.io.*;
import java.net.*;
import java.text.*;
import java.util.*;
import java.util.concurrent.*;

public final class MainActivity extends Activity {
    private static final String BASE="https://matchlab-az-online.onrender.com";
    private static final int BG=Color.rgb(9,19,31), CARD=Color.rgb(22,38,54), RAISED=Color.rgb(30,49,66),
        INK=Color.rgb(241,248,253), MUTED=Color.rgb(167,184,198), ACCENT=Color.rgb(155,236,118), RED=Color.rgb(248,133,130);
    private static final String[] LEAGUES={"all","eng.1","esp.1","ger.1","ita.1","fra.1","uefa.champions","uefa.europa","tur.1","por.1","ned.1"};
    private static final String[] NAMES={"Bütün liqalar","Premier League","La Liga","Bundesliga","Serie A","Ligue 1","Champions League","Europa League","Süper Lig","Primeira Liga","Eredivisie"};
    private final ExecutorService network=Executors.newSingleThreadExecutor();
    private final Handler ui=new Handler(Looper.getMainLooper());
    private LinearLayout body, nav, page;
    private ScrollView contentScroll;
    private int bottomInset=0;
    private TextView header, status;
    private String screen="matches", league="all", kind="all", searchText="";
    private Calendar day=Calendar.getInstance(TimeZone.getTimeZone("Asia/Baku"));
    private int generation=0, formation=0;
    private final String[] formations={"4-3-3","4-2-3-1","4-4-2","3-5-2"};
    private JSONArray matches=new JSONArray();
    private JSONObject currentMatch=null;
    private SharedPreferences prefs;
    private final Runnable refresh=new Runnable(){
        @Override public void run(){
            if("matches".equals(screen)) loadMatches(false);
            ui.postDelayed(this,30000);
        }
    };

    @Override public void onCreate(Bundle saved){
        super.onCreate(saved);
        getWindow().setStatusBarColor(BG);getWindow().setNavigationBarColor(BG);
        prefs=getSharedPreferences("matchlab_native",MODE_PRIVATE);
        showShell();
        navigate("matches");
        ui.postDelayed(refresh,30000);
    }
    private int dp(float n){return Math.round(n*getResources().getDisplayMetrics().density);}
    private GradientDrawable shape(int bg,int radius){
        GradientDrawable d=new GradientDrawable();d.setColor(bg);d.setCornerRadius(dp(radius));return d;
    }
    private TextView text(String s,int size,int color,boolean bold){
        TextView t=new TextView(this);t.setText(s);t.setTextSize(size);t.setTextColor(color);
        if(bold)t.setTypeface(Typeface.DEFAULT,Typeface.BOLD);
        t.setGravity(Gravity.CENTER_VERTICAL);
        return t;
    }
    private LinearLayout column(){
        LinearLayout l=new LinearLayout(this);l.setOrientation(LinearLayout.VERTICAL);return l;
    }
    private LinearLayout row(){
        LinearLayout l=new LinearLayout(this);l.setOrientation(LinearLayout.HORIZONTAL);l.setGravity(Gravity.CENTER_VERTICAL);return l;
    }
    private void gap(LinearLayout p,int h){View v=new View(this);p.addView(v,new LinearLayout.LayoutParams(1,dp(h)));}
    private void card(View v){
        LinearLayout wrapper=column();wrapper.setPadding(dp(15),dp(12),dp(15),dp(12));wrapper.setBackground(shape(CARD,14));
        wrapper.addView(v);
        LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(-1,-2);lp.bottomMargin=dp(11);
        page.addView(wrapper,lp);
    }
    private void info(String message,boolean error){
        TextView t=text(message,14,error?RED:MUTED,false);t.setPadding(dp(4),dp(8),dp(4),dp(8));card(t);
    }
    private void section(String label){
        TextView t=text(label,16,ACCENT,true);t.setPadding(dp(2),dp(13),0,dp(12));
        page.addView(t);
    }
    private Button button(String label){
        Button b=new Button(this);b.setText(label);b.setTextSize(12);b.setAllCaps(false);
        b.setTextColor(INK);b.setBackground(shape(RAISED,11));
        b.setMinHeight(0);b.setMinimumHeight(0);b.setPadding(dp(10),dp(8),dp(10),dp(8));return b;
    }
    private void showShell(){
        body=column();body.setBackgroundColor(BG);
        if(Build.VERSION.SDK_INT>=35){getWindow().setDecorFitsSystemWindows(true);}
        body.setFitsSystemWindows(true);
        LinearLayout top=row();top.setPadding(dp(18),dp(10),dp(18),dp(10));
        header=text("MATCHLAB AZ",21,INK,true);top.addView(header,new LinearLayout.LayoutParams(0,dp(49),1));
        status=text("●",16,ACCENT,true);top.addView(status);
        body.addView(top,new LinearLayout.LayoutParams(-1,dp(70)));
        ScrollView scroll=new ScrollView(this);contentScroll=scroll;scroll.setFillViewport(false);
        scroll.setClipToPadding(false);
        page=column();page.setPadding(dp(16),dp(6),dp(16),dp(24));scroll.addView(page);
        body.addView(scroll,new LinearLayout.LayoutParams(-1,0,1));
        nav=row();nav.setBackgroundColor(Color.rgb(14,30,46));
        nav.setMinimumHeight(dp(72));
        body.addView(nav,new LinearLayout.LayoutParams(-1,dp(72)));
        if(Build.VERSION.SDK_INT>=30){
            body.setOnApplyWindowInsetsListener((v,insets)->{
                android.graphics.Insets sys=insets.getInsets(WindowInsets.Type.navigationBars()|WindowInsets.Type.displayCutout());
                int newBottom=sys.bottom;
                if(newBottom!=bottomInset){bottomInset=newBottom;nav.setPadding(0,0,0,newBottom);nav.setLayoutParams(new LinearLayout.LayoutParams(-1,dp(72)+newBottom));}
                return insets;
            });
        }
        setContentView(body);
    }
    private void navigate(String name){
        screen=name;generation++;page.removeAllViews();
        if(contentScroll!=null)contentScroll.scrollTo(0,0);
        header.setText(name.equals("matches")?"Canlı matçlar":name.equals("standings")?"Turnir cədvəli":name.equals("search")?"Axtarış":name.equals("tactics")?"Taktika":name.equals("favorites")?"Seçilmişlər":name.equals("details")?"Matç mərkəzi":name.equals("profile")?"Futbol profili":"Tənzimləmələr");
        nav.removeAllViews();
        String[][] items={{"matches","⚽","Matçlar"},{"standings","▤","Cədvəl"},{"search","⌕","Axtar"},{"favorites","☆","Seçilmiş"},{"tactics","▦","Taktika"}};
        for(String[] item:items){
            LinearLayout cell=column();cell.setGravity(Gravity.CENTER);
            boolean active=name.equals(item[0]);
            TextView icon=text(item[1],23,active?ACCENT:MUTED,true);icon.setGravity(Gravity.CENTER);
            TextView label=text(item[2],12,active?ACCENT:INK,active);label.setGravity(Gravity.CENTER);
            cell.addView(icon);cell.addView(label);
            cell.setPadding(dp(2),dp(8),dp(2),dp(8));
            cell.setContentDescription(item[2]);
            cell.setClickable(true);
            cell.setOnClickListener(v->navigate(item[0]));
            nav.addView(cell,new LinearLayout.LayoutParams(0,-1,1));
        }
        if(name.equals("matches"))loadMatches(true);
        else if(name.equals("standings"))showStandings();
        else if(name.equals("search"))showSearch();
        else if(name.equals("favorites"))showFavorites();
        else if(name.equals("tactics"))showTactics();
        else if(name.equals("details"))showDetails();
        else if(name.equals("settings"))showSettings();
    }
    private String date(){
        return new SimpleDateFormat("yyyy-MM-dd",Locale.US).format(day.getTime());
    }
    private Spinner spinner(String[] options,int selected,java.util.function.IntConsumer change){
        Spinner s=new Spinner(this);ArrayAdapter<String> adapter=new ArrayAdapter<>(this,android.R.layout.simple_spinner_dropdown_item,options);
        s.setAdapter(adapter);s.setSelection(Math.max(0,selected),false);
        s.setOnItemSelectedListener(new android.widget.AdapterView.OnItemSelectedListener(){
            boolean first=true;
            @Override public void onItemSelected(android.widget.AdapterView<?> parent,View v,int pos,long id){
                if(first){first=false;return;}change.accept(pos);
            }
            @Override public void onNothingSelected(android.widget.AdapterView<?> parent){}
        });
        return s;
    }
    private void filters(boolean standings){
        LinearLayout r=row();
        if(!standings){
            Button prev=button("‹");prev.setOnClickListener(v->{day.add(Calendar.DATE,-1);navigate("matches");});r.addView(prev);
            TextView date=text("  "+date()+"  ",14,INK,true);r.addView(date);
            Button next=button("›");next.setOnClickListener(v->{day.add(Calendar.DATE,1);navigate("matches");});r.addView(next);
            Button today=button("Bu gün");today.setOnClickListener(v->{day=Calendar.getInstance(TimeZone.getTimeZone("Asia/Baku"));navigate("matches");});
            r.addView(today);
            card(r);
        }
        int idx=Arrays.asList(LEAGUES).indexOf(league);
        if(standings&&idx==0){league="eng.1";idx=1;}
        final int offset=standings?1:0;
        String[] options=standings?Arrays.copyOfRange(NAMES,1,NAMES.length):NAMES;
        Spinner s=spinner(options,Math.max(0,idx-offset),p->{
            String next=LEAGUES[p+offset];if(next.equals(league))return;league=next;navigate(standings?"standings":"matches");
        });
        card(s);
    }
    private interface JsonCallback{void done(JSONObject json,Exception error);}
    private void fetch(String path,JsonCallback callback){
        network.execute(()->{
            JSONObject result=null;Exception error=null;
            try{
                URL url=new URL(BASE+path);
                HttpURLConnection conn=(HttpURLConnection)url.openConnection();
                conn.setConnectTimeout(10000);conn.setReadTimeout(26000);
                conn.setRequestProperty("Accept","application/json");
                conn.setRequestProperty("User-Agent","MATCHLABAZ-Native/0.9.30");
                int code=conn.getResponseCode();
                if(code<200||code>=300)throw new IOException("HTTP "+code);
                try(InputStream input=conn.getInputStream();ByteArrayOutputStream out=new ByteArrayOutputStream()){
                    byte[] buf=new byte[8192];int n;
                    while((n=input.read(buf))!=-1){out.write(buf,0,n);if(out.size()>2_000_000)throw new IOException("Response too large");}
                    result=new JSONObject(out.toString("UTF-8"));
                }finally{conn.disconnect();}
            }catch(Exception ex){error=ex;}
            JSONObject data=result;Exception failure=error;
            ui.post(()->callback.done(data,failure));
        });
    }
    private void loadMatches(boolean reset){
        int token=generation;
        if(reset){filters(false);info("Canlı nəticələr yüklənir…",false);}
        fetch("/api/live?league="+encode(league)+"&date="+date(),(json,error)->{
            if(token!=generation||!screen.equals("matches"))return;
            if(error!=null){status.setTextColor(RED);status.setText("●");if(reset){page.removeAllViews();filters(false);}info("Bağlantı yoxdur: "+error.getMessage(),true);return;}
            status.setTextColor(json.optBoolean("available")?ACCENT:RED);
            status.setText("●");
            matches=json.optJSONArray("items");if(matches==null)matches=new JSONArray();
            page.removeAllViews();filters(false);
            if(json.optBoolean("partial")||json.optBoolean("stale"))info("Bəzi mənbələr əlçatan deyil. Köhnə nəticələr canlı kimi göstərilmir.",true);
            String message=json.optString("message");if(!message.isEmpty())info(message,!json.optBoolean("available"));
            if(matches.length()==0){info(json.optBoolean("available")?"Bu tarix üçün matç yoxdur.":"Nəticələr mənbədən alınmadı.",!json.optBoolean("available"));return;}
            String previous="";
            for(int i=0;i<matches.length();i++){
                JSONObject m=matches.optJSONObject(i);if(m==null)continue;
                String group=m.optString("leagueName",m.optString("league"));
                if(!group.equals(previous)){section(group);previous=group;}
                matchRow(m,false);
            }
        });
    }
    private void matchRow(JSONObject m,boolean saved){
        LinearLayout line=row();
        LinearLayout teams=column();
        TextView home=text(m.optJSONObject("home")!=null?m.optJSONObject("home").optString("name","—"):"—",15,INK,true);
        TextView away=text(m.optJSONObject("away")!=null?m.optJSONObject("away").optString("name","—"):"—",15,INK,true);
        teams.addView(home);gap(teams,7);teams.addView(away);
        line.addView(teams,new LinearLayout.LayoutParams(0,-2,1));
        LinearLayout scores=column();scores.setGravity(Gravity.CENTER);
        String score=m.optString("state").equals("scheduled")?"— : —":m.optString("homeScore","—")+" : "+m.optString("awayScore","—");
        TextView scoreText=text(score,19,INK,true);scoreText.setGravity(Gravity.CENTER);scores.addView(scoreText);
        String st=saved?"Saxlanmış":m.optString("state").equals("live")?"● CANLI":m.optString("state").equals("final")?"Bitib":"Gözlənilir";
        TextView state=text(st,10,m.optString("state").equals("live")&&!saved?ACCENT:MUTED,false);
        state.setGravity(Gravity.CENTER);scores.addView(state);
        line.addView(scores);
        String id=m.optString("id");
        Button star=button(prefs.contains("fav_"+id)?"★":"☆");
        star.setTextColor(ACCENT);
        star.setOnClickListener(v->{
            if(prefs.contains("fav_"+id))prefs.edit().remove("fav_"+id).apply();
            else prefs.edit().putString("fav_"+id,m.toString()).apply();
            star.setText(prefs.contains("fav_"+id)?"★":"☆");
        });
        line.addView(star);
        line.setOnClickListener(v->{currentMatch=m;navigate("details");});
        card(line);
    }
    private void showStandings(){
        filters(true);info("Turnir cədvəli yüklənir…",false);
        int token=generation;
        fetch("/api/standings?league="+encode(league),(data,error)->{
            if(token!=generation||!screen.equals("standings"))return;
            page.removeAllViews();filters(true);
            if(error!=null){info("Cədvəl alınmadı: "+error.getMessage(),true);return;}
            JSONArray rows=data.optJSONArray("items");
            if(data.optBoolean("stale"))info("Cədvəl saxlanmış məlumatdır, cari olmaya bilər.",true);
            if(rows==null||rows.length()==0){info(data.optString("message","Cədvəl mövcud deyil."),true);return;}
            for(int i=0;i<rows.length();i++){
                JSONObject r=rows.optJSONObject(i);if(r==null)continue;
                LinearLayout line=row();
                TextView rank=text(r.optString("rank","—")+"  ",15,ACCENT,true);line.addView(rank);
                LinearLayout main=column();
                main.addView(text(r.optString("name","—"),15,INK,true));
                main.addView(text("O "+r.optString("played","—")+"   Q "+r.optString("win","—")+"   H "+r.optString("draw","—")+"   M "+r.optString("loss","—"),11,MUTED,false));
                line.addView(main,new LinearLayout.LayoutParams(0,-2,1));
                line.addView(text(r.optString("points","—")+" xal",15,INK,true));
                card(line);
            }
        });
    }
    private void showSearch(){
        EditText query=new EditText(this);query.setSingleLine(true);query.setHint("Futbolçu, klub, məşqçi…");
        query.setText(searchText);query.setTextColor(INK);query.setHintTextColor(MUTED);
        query.setTextSize(17);query.setMinHeight(dp(48));
        query.setImeOptions(android.view.inputmethod.EditorInfo.IME_ACTION_SEARCH);
        card(query);
        String[] types={"Hamısı","Futbolçular","Klublar","Məşqçilər"};
        Spinner typesSpinner=spinner(types,Arrays.asList(new String[]{"all","players","teams","coaches"}).indexOf(kind),i->kind=new String[]{"all","players","teams","coaches"}[i]);
        card(typesSpinner);
        Button go=button("⌕  Axtar");
        go.setOnClickListener(v->{searchText=query.getText().toString().trim();loadSearch(searchText,kind);});
        query.setOnEditorActionListener((v,action,event)->{
            if(action==android.view.inputmethod.EditorInfo.IME_ACTION_SEARCH){go.performClick();return true;}
            return false;
        });
        card(go);
        info("Futbol arxivi serverin məlumat bazasında axtarılır.",false);
    }
    private void loadSearch(String q,String kind){
        if(q.isEmpty()){info("Ad yaz və axtar.",true);return;}
        while(page.getChildCount()>4)page.removeViewAt(page.getChildCount()-1);
        info("Axtarılır: "+q,false);
        int token=generation;
        fetch("/api/search?q="+encode(q)+"&kind="+kind,(json,error)->{
            if(token!=generation||!screen.equals("search"))return;
            while(page.getChildCount()>4)page.removeViewAt(page.getChildCount()-1);
            if(error!=null){info("Axtarış alınmadı: "+error.getMessage(),true);return;}
            JSONArray arr=json.optJSONArray("items");
            if(arr==null||arr.length()==0){info("Nəticə tapılmadı.",false);return;}
            section("Nəticələr · "+arr.length());
            for(int i=0;i<arr.length();i++){
                JSONObject p=arr.optJSONObject(i);if(p==null)continue;
                LinearLayout c=column();
                c.addView(text(p.optString("name"),16,INK,true));
                c.addView(text(p.optString("country")+" · "+p.optString("kind"),12,MUTED,false));
                c.setOnClickListener(v->openProfile(p.optString("id")));
                card(c);
            }
        });
    }
    private void openProfile(String id){
        navigate("profile");
        int token=generation;info("Profil yüklənir…",false);
        fetch("/api/profile?id="+encode(id),(data,error)->{
            if(token!=generation||!screen.equals("profile"))return;
            page.removeAllViews();
            if(error!=null){info("Profil yüklənmədi: "+error.getMessage(),true);return;}
            JSONObject p=data.optJSONObject("profile");
            if(p==null){info("Təsdiqlənmiş profil tapılmadı.",true);return;}
            section(p.optString("name","—"));
            info(p.optString("kind")+" · "+p.optString("country"),false);
            for(String k:new String[]{"birth","death","position","description","source","lifeStatus","careerStatus"}){
                String value=p.optString(k);
                if(!value.isEmpty()&&!value.equals("null"))info(k+": "+value,false);
            }
            for(String k:new String[]{"clubs","coached","awards"}){
                JSONArray a=p.optJSONArray(k);if(a==null||a.length()==0)continue;
                section(k+" · "+a.length());
                for(int i=0;i<Math.min(a.length(),35);i++){
                    Object v=a.opt(i);info(v instanceof JSONObject?((JSONObject)v).optString("name",v.toString()):String.valueOf(v),false);
                }
            }
        });
    }
    private void showDetails(){
        if(currentMatch==null){info("Matç seçilməyib.",true);return;}
        JSONObject m=currentMatch;
        JSONObject h=m.optJSONObject("home"),a=m.optJSONObject("away");
        section((h!=null?h.optString("name"):"—")+"   "+m.optString("homeScore","—")+" : "+m.optString("awayScore","—")+"   "+(a!=null?a.optString("name"):"—"));
        info(m.optString("leagueName")+" · "+m.optString("state")+" · "+m.optString("source"),false);
        String[] id=m.optString("id").split(":",3);
        if(id.length!=3||!Arrays.asList("espn","sportsdb","open").contains(id[0])){info("Bu matç üçün hadisə mənbəyi yoxdur.",false);return;}
        int token=generation;info("Matç hadisələri alınır…",false);
        fetch("/api/match-detail?provider="+id[0]+"&league="+encode(id[1])+"&id="+encode(id[2]),(data,error)->{
            if(token!=generation||!screen.equals("details"))return;
            if(error!=null){info("Detallar alınmadı: "+error.getMessage(),true);return;}
            if(!data.optBoolean("available"))info(data.optString("message","Hadisələr mövcud deyil."),true);
            JSONArray events=data.optJSONArray("events");
            if(events!=null&&events.length()>0){
                section("Matç hadisələri");
                for(int i=0;i<Math.min(events.length(),70);i++){
                    JSONObject e=events.optJSONObject(i);if(e!=null)info(e.optString("minute",e.optString("clock"))+"  "+e.optString("text",e.optString("type")),false);
                }
            }
            JSONArray stats=data.optJSONArray("statistics");
            if(stats!=null&&stats.length()>0){
                section("Statistika");
                for(int i=0;i<Math.min(stats.length(),40);i++){
                    JSONObject s=stats.optJSONObject(i);if(s!=null)info(s.optString("name",s.optString("label"))+"  "+s.optString("home",s.optString("homeValue","—"))+" : "+s.optString("away",s.optString("awayValue","—")),false);
                }
            }
        });
    }
    private void showFavorites(){
        section("Seçilmiş matçlar");
        info("Bunlar saxlanmış məlumatlardır, canlı nəticə deyil.",false);
        int count=0;
        for(Map.Entry<String,?> entry:prefs.getAll().entrySet()){
            if(!entry.getKey().startsWith("fav_"))continue;
            try{matchRow(new JSONObject(String.valueOf(entry.getValue())),true);count++;}catch(Exception ignored){}
        }
        if(count==0)info("Seçilmiş matç yoxdur. ☆ düyməsinə toxun.",false);
    }
    private void showTactics(){
        section("Taktika studiyası");
        Spinner s=spinner(formations,formation,i->{formation=i;navigate("tactics");});card(s);
        PitchView pitch=new PitchView(this,formations[formation]);
        LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(-1,dp(530));lp.bottomMargin=dp(15);page.addView(pitch,lp);
        info("Düzülüş yerli olaraq çəkilir. Təsdiqlənməmiş oyunçu adları göstərilmir.",false);
    }
    private void showSettings(){
        section("MATCHLAB AZ Native 0.9.32");
        info("Bu proqramın ekranları Android-in öz interfeysidir. WebView və brauzer yoxdur.",false);
        info("Canlı matçlar və profillər HTTPS JSON API-dən gəlir. Mənbələrdə boşluqlar ola bilər.",false);
        Button statusButton=button("Server vəziyyətini yoxla");
        statusButton.setOnClickListener(v->{
            fetch("/api/status",(json,error)->{
                if(error!=null){info("Bağlantı: "+error.getMessage(),true);return;}
                info("Versiya: "+json.optString("version")+" · Arxiv: "+(json.optJSONObject("world")!=null?json.optJSONObject("world").optString("total","—"):"—"),false);
            });
        });card(statusButton);
    }
    private static String encode(String s){
        try{return java.net.URLEncoder.encode(s,"UTF-8");}catch(Exception ignored){return s;}
    }
    @Override public void onBackPressed(){
        if("details".equals(screen))navigate("matches");
        else if("profile".equals(screen))navigate("search");
        else if(!"matches".equals(screen))navigate("matches");
        else super.onBackPressed();
    }
    @Override protected void onDestroy(){ui.removeCallbacks(refresh);network.shutdownNow();super.onDestroy();}
}
