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
import android.view.View;
import android.view.ViewGroup;
import android.content.Intent;
import android.provider.Settings;
import android.view.inputmethod.InputMethodManager;
import android.widget.*;
import org.json.*;
import java.io.*;
import java.net.*;
import java.text.*;
import java.util.*;
import java.util.concurrent.*;

public final class MainActivity extends Activity {
    private static final String BASE="https://matchlab-az-online.onrender.com";
    private static final int BG=Color.rgb(8,16,27), CARD=Color.rgb(18,32,47), RAISED=Color.rgb(30,48,65),
        INK=Color.rgb(241,248,253), MUTED=Color.rgb(167,184,198), ACCENT=Color.rgb(155,236,118), RED=Color.rgb(248,133,130);
    private static final String[] LEAGUES={"all","eng.1","esp.1","ger.1","ita.1","fra.1","uefa.champions","uefa.europa","tur.1","por.1","ned.1"};
    private static final String[] NAMES={"Bütün liqalar","Premier League","La Liga","Bundesliga","Serie A","Ligue 1","Champions League","Europa League","Süper Lig","Primeira Liga","Eredivisie"};
    private final ExecutorService network=Executors.newFixedThreadPool(3);
    private final Handler ui=new Handler(Looper.getMainLooper());
    private LinearLayout body, nav, page;
    private ScrollView contentScroll;
    private int bottomInset=-1,topInset=-1;
    private TextView header, status;
    private String screen="matches", league="all", kind="all", searchText="";
    private Calendar day=Calendar.getInstance(TimeZone.getTimeZone("Asia/Baku"));
    private int generation=0, formation=0;
    private boolean standingsExpanded=false;
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
        t.setIncludeFontPadding(false);
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
        LinearLayout wrapper=column();wrapper.setPadding(dp(11),dp(9),dp(11),dp(9));wrapper.setBackground(shape(CARD,12));
        wrapper.addView(v);
        LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(-1,-2);lp.bottomMargin=dp(7);
        page.addView(wrapper,lp);
    }
    private void info(String message,boolean error){
        TextView t=text(message,12,error?RED:MUTED,false);t.setPadding(dp(4),dp(6),dp(4),dp(6));card(t);
    }
    private void section(String label){
        TextView t=text(label,13,ACCENT,true);t.setLetterSpacing(.045f);t.setPadding(dp(3),dp(10),0,dp(8));
        page.addView(t);
    }
    private Button button(String label){
        Button b=new Button(this);b.setText(label);b.setTextSize(12);b.setAllCaps(false);
        b.setTextColor(INK);b.setBackground(shape(RAISED,11));
        b.setMinHeight(dp(42));b.setMinimumHeight(dp(42));b.setPadding(dp(8),dp(7),dp(8),dp(7));return b;
    }

    private String val(JSONObject object,String key){
        if(object==null||object.isNull(key))return "—";
        String t=object.optString(key,"").trim();
        return t.isEmpty()||t.equalsIgnoreCase("null")?"—":t;
    }
    private void line(ViewGroup parent){
        View border=new View(this);border.setBackgroundColor(Color.rgb(41,59,74));
        parent.addView(border,new LinearLayout.LayoutParams(-1,dp(1)));
    }
    private TextView fixed(String value,int size,int color,boolean bold,int width){
        TextView t=text(value,size,color,bold);t.setGravity(Gravity.CENTER);
        t.setSingleLine(true);t.setEllipsize(android.text.TextUtils.TruncateAt.END);
        t.setMinWidth(dp(width));t.setMaxWidth(dp(width));
        t.setLayoutParams(new LinearLayout.LayoutParams(dp(width),-2));
        return t;
    }
    private TextView single(String value,int size,int color,boolean bold){
        TextView t=text(value,size,color,bold);
        t.setMaxLines(1);t.setEllipsize(android.text.TextUtils.TruncateAt.END);
        return t;
    }
    private void banner(String label,int tint){
        TextView view=text(label,11,tint,true);
        view.setPadding(dp(11),dp(9),dp(11),dp(9));
        view.setBackground(shape(Color.rgb(26,43,54),9));
        LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(-1,-2);lp.bottomMargin=dp(9);
        page.addView(view,lp);
    }
    private String stateLabel(JSONObject match,boolean saved){
        if(saved)return "SAXLANMIŞ · CANLI DEYİL";
        String state=match.optString("state");
        if(match.optBoolean("stale"))return "KÖHNƏ MƏLUMAT";
        if("live".equals(state))return "● CANLI";
        if("final".equals(state))return "BİTİB";
        if("scheduled".equals(state))return "GÖZLƏNİLİR";
        return state.isEmpty()?"MƏLUM DEYİL":state.toUpperCase(Locale.ROOT);
    }

    private void showShell(){
        body=column();body.setBackgroundColor(BG);
        if(Build.VERSION.SDK_INT>=30)getWindow().setDecorFitsSystemWindows(false);
        else body.setFitsSystemWindows(true);
        LinearLayout top=row();top.setPadding(dp(13),dp(6),dp(9),dp(6));
        LinearLayout brandBox=column();
        TextView brand=text("MATCHLAB AZ",10,ACCENT,true);brand.setLetterSpacing(.13f);
        brandBox.addView(brand);
        header=text("Canlı matçlar",18,INK,true);brandBox.addView(header);
        top.addView(brandBox,new LinearLayout.LayoutParams(0,-2,1));
        status=text("●",16,ACCENT,true);top.addView(status);
        TextView menu=text("⋮",26,INK,true);menu.setGravity(Gravity.CENTER);
        menu.setContentDescription("Tətbiq menyusu");menu.setClickable(true);
        menu.setOnClickListener(v->showMenu(menu));
        top.addView(menu,new LinearLayout.LayoutParams(dp(48),dp(52)));
        top.setBackgroundColor(Color.rgb(13,28,42));
        body.addView(top,new LinearLayout.LayoutParams(-1,dp(62)));
        ScrollView scroll=new ScrollView(this);contentScroll=scroll;scroll.setFillViewport(false);
        scroll.setClipToPadding(false);
        page=column();page.setPadding(dp(12),dp(6),dp(12),dp(16));scroll.addView(page);
        body.addView(scroll,new LinearLayout.LayoutParams(-1,0,1));
        nav=row();nav.setBackgroundColor(Color.rgb(14,30,46));
        nav.setMinimumHeight(dp(62));
        body.addView(nav,new LinearLayout.LayoutParams(-1,dp(64)));
        if(Build.VERSION.SDK_INT>=30){
            body.setOnApplyWindowInsetsListener((v,insets)->{
                android.graphics.Insets sys=insets.getInsets(WindowInsets.Type.systemBars()|WindowInsets.Type.displayCutout());
                if(sys.top!=topInset||sys.bottom!=bottomInset){
                    topInset=sys.top;bottomInset=sys.bottom;
                    body.setPadding(sys.left,sys.top,sys.right,sys.bottom);
                }
                return insets;
            });
        }
        setContentView(body);
        if(Build.VERSION.SDK_INT>=30)body.requestApplyInsets();
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
            NavGlyph glyph=new NavGlyph(this,item[0],active?ACCENT:MUTED);
            cell.addView(glyph,new LinearLayout.LayoutParams(dp(22),dp(22)));
            TextView label=text(item[2],10,active?ACCENT:MUTED,active);label.setGravity(Gravity.CENTER);
            cell.addView(label);
            cell.setPadding(dp(1),dp(5),dp(1),dp(5));
            cell.setMinimumHeight(dp(56));
            if(active)cell.setBackground(shape(Color.rgb(29,55,48),10));
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
            HorizontalScrollView dates=new HorizontalScrollView(this);dates.setHorizontalScrollBarEnabled(false);
            dates.addView(r);card(dates);
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
                conn.setRequestProperty("User-Agent","MATCHLABAZ-Native/0.9.47");
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
        if(reset){filters(false);banner("Real mənbələr yoxlanır · Yeni nəticələr yüklənir…",MUTED);}
        fetch("/api/live?league="+encode(league)+"&date="+date(),(json,error)->{
            if(token!=generation||!screen.equals("matches"))return;
            if(error!=null){status.setTextColor(RED);status.setText("●");if(reset){page.removeAllViews();filters(false);}info("Bağlantı yoxdur: "+error.getMessage(),true);return;}
            status.setTextColor(json.optBoolean("available")?ACCENT:RED);
            status.setText("●");
            matches=json.optJSONArray("items");if(matches==null)matches=new JSONArray();
            page.removeAllViews();filters(false);
            if(json.has("checkedAt"))banner("Son yoxlama: "+json.optString("checkedAt").replace("T"," ").replace("+00:00"," UTC"),MUTED);
            if(json.optBoolean("partial")||json.optBoolean("stale"))info("Bəzi mənbələr əlçatan deyil. Köhnə nəticələr canlı kimi göstərilmir.",true);
            String message=json.optString("message");if(!message.isEmpty())info(message,!json.optBoolean("available"));
            if(matches.length()==0){info(json.optBoolean("available")?"Bu tarix üçün matç yoxdur.":"Nəticələr mənbədən alınmadı.",!json.optBoolean("available"));return;}
            int liveCount=json.optInt("liveCount",0);
            banner(matches.length()+" real matç  ·  "+liveCount+" canlı  ·  "+json.optString("source","mənbə yoxdur"),ACCENT);
            String previous="";
            for(int i=0;i<Math.min(matches.length(),100);i++){
                JSONObject m=matches.optJSONObject(i);if(m==null)continue;
                String group=m.optString("leagueName",m.optString("league"));
                if(!group.equals(previous)){section(group);previous=group;}
                matchRow(m,false);
            }
        });
    }
    private void matchRow(JSONObject m,boolean saved){
        LinearLayout wrapper=column();
        wrapper.setBackground(shape(CARD,12));
        wrapper.setPadding(dp(10),dp(9),dp(10),dp(9));
        String state=m.optString("state");
        boolean live=!saved&&!m.optBoolean("stale")&&"live".equals(state);
        LinearLayout top=row();
        TextView phase=single(stateLabel(m,saved),10,live?ACCENT:MUTED,true);
        top.addView(phase,new LinearLayout.LayoutParams(0,-2,1));
        String provider=m.optString("source");
        if(!provider.isEmpty())top.addView(single(provider,10,MUTED,false));
        wrapper.addView(top);
        gap(wrapper,6);
        LinearLayout body=row();
        LinearLayout teams=column();
        JSONObject home=m.optJSONObject("home"),away=m.optJSONObject("away");
        for(JSONObject team:new JSONObject[]{home,away}){
            LinearLayout teamRow=row();
            String name=val(team,"name");
            TeamBadge badge=new TeamBadge(this,name,team==null?"":team.optString("image"),27);
            LinearLayout.LayoutParams bp=new LinearLayout.LayoutParams(dp(27),dp(27));bp.rightMargin=dp(8);
            teamRow.addView(badge,bp);
            teamRow.addView(single(name,13,INK,true),new LinearLayout.LayoutParams(0,-2,1));
            teams.addView(teamRow);
            if(team==home)gap(teams,5);
        }
        body.addView(teams,new LinearLayout.LayoutParams(0,-2,1));
        LinearLayout scoreBlock=column();scoreBlock.setGravity(Gravity.CENTER);
        String score="scheduled".equals(state)?"– : –":val(m,"homeScore")+" : "+val(m,"awayScore");
        TextView result=single(score,17,live?ACCENT:INK,true);
        result.setGravity(Gravity.CENTER);
        scoreBlock.addView(result);
        String time=val(m,"minute");
        if(!"—".equals(time)&&live){
            TextView minute=text(time,10,ACCENT,true);minute.setGravity(Gravity.CENTER);scoreBlock.addView(minute);
        }
        body.addView(scoreBlock,new LinearLayout.LayoutParams(dp(82),-2));
        String id=m.optString("id");
        TextView star=fixed(prefs.contains("fav_"+id)?"★":"☆",23,ACCENT,false,40);
        star.setContentDescription("Seçilmişlərə əlavə et və ya çıxart");
        star.setMinHeight(dp(44));star.setClickable(true);
        star.setOnClickListener(v->{
            if(prefs.contains("fav_"+id))prefs.edit().remove("fav_"+id).apply();
            else prefs.edit().putString("fav_"+id,m.toString()).apply();
            star.setText(prefs.contains("fav_"+id)?"★":"☆");
        });
        body.addView(star);
        wrapper.addView(body);
        wrapper.setOnClickListener(v->{currentMatch=m;navigate("details");});
        wrapper.setContentDescription(val(home,"name")+" "+score+" "+val(away,"name")+", "+stateLabel(m,saved));
        LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(-1,-2);lp.bottomMargin=dp(6);
        page.addView(wrapper,lp);
    }
    private void standingsHeader(boolean wide){
        LinearLayout line=row();
        line.setPadding(dp(7),dp(8),dp(7),dp(8));
        line.addView(fixed("#",10,MUTED,true,24));
        TextView name=single("KLUB",10,MUTED,true);
        name.setPadding(dp(8),0,0,0);
        line.addView(name,new LinearLayout.LayoutParams(0,-2,1));
        if(wide){
            line.addView(fixed("O",10,MUTED,true,26));
            line.addView(fixed("Q",10,MUTED,true,26));
            line.addView(fixed("H",10,MUTED,true,26));
            line.addView(fixed("M",10,MUTED,true,26));
            line.addView(fixed("QF",10,MUTED,true,35));
        }else{
            line.addView(fixed("O",10,MUTED,true,28));
            line.addView(fixed("QF",10,MUTED,true,40));
        }
        line.addView(fixed("XAL",10,ACCENT,true,38));
        line.setBackground(shape(Color.rgb(25,44,58),9));
        page.addView(line);
    }
    private void standingRow(JSONObject r,int index,boolean wide){
        LinearLayout container=column();
        LinearLayout line=row();
        line.setPadding(dp(4),dp(9),dp(5),dp(9));
        int rank=r.optInt("rank",index+1);
        int tint=rank<=4?ACCENT:rank>=18?RED:MUTED;
        line.addView(fixed(String.valueOf(rank),11,tint,true,24));
        String club=val(r,"name");
        TeamBadge badge=new TeamBadge(this,club,r.optString("image"),24);
        LinearLayout.LayoutParams badgeParams=new LinearLayout.LayoutParams(dp(24),dp(24));
        badgeParams.leftMargin=dp(6);badgeParams.rightMargin=dp(5);
        line.addView(badge,badgeParams);
        TextView clubName=single(club,12,INK,true);
        line.addView(clubName,new LinearLayout.LayoutParams(0,-2,1));
        if(wide){
            for(String key:new String[]{"played","win","draw","loss"}){
                line.addView(fixed(val(r,key),11,MUTED,false,26));
            }
            line.addView(fixed(val(r,"gd"),11,MUTED,false,35));
        }else{
            line.addView(fixed(val(r,"played"),11,MUTED,false,28));
            line.addView(fixed(val(r,"gd"),11,MUTED,false,40));
        }
        line.addView(fixed(val(r,"points"),12,INK,true,38));
        container.addView(line);
        String form=r.optString("form","").trim();
        if(!form.isEmpty()||r.has("gf")||r.has("ga")){
            LinearLayout more=row();
            more.setPadding(dp(39),0,dp(6),dp(7));
            String gf=val(r,"gf"),ga=val(r,"ga");
            String text="Qol "+gf+" : "+ga;
            if(!form.isEmpty())text+="   ·   Son 5: "+form;
            more.addView(single(text,10,MUTED,false));
            container.addView(more);
        }
        container.setBackgroundColor(index%2==0?Color.rgb(18,32,47):Color.rgb(23,39,54));
        page.addView(container);
        line(container);
    }
    private void showStandings(){
        filters(true);
        info("Turnir cədvəli mənbədən alınır…",false);
        int token=generation;
        String requestLeague=league;
        fetch("/api/standings?league="+encode(requestLeague),(data,error)->{
            if(token!=generation||!screen.equals("standings"))return;
            page.removeAllViews();
            filters(true);
            if(error!=null){banner("Cədvəl alınmadı: "+error.getMessage(),RED);return;}
            if(data.optBoolean("stale"))banner("Bu cədvəl cari olmaya bilər — mənbə köhnəlmiş məlumat qaytardı.",RED);
            if(data.optBoolean("partial"))banner("Bəzi cədvəl məlumatları mənbədən alınmadı.",RED);
            JSONArray rows=data.optJSONArray("items");
            if(rows==null||rows.length()==0){
                banner(data.optString("message","Cədvəl mövcud deyil."),RED);return;
            }
            section(NAMES[Math.max(1,Arrays.asList(LEAGUES).indexOf(requestLeague))]);
            LinearLayout toolbar=row();
            TextView lead=single(rows.length()+" klub · Mənbə: "+data.optString("source","məlum deyil"),11,MUTED,false);
            toolbar.addView(lead,new LinearLayout.LayoutParams(0,-2,1));
            Button toggle=button(standingsExpanded?"Sadə":"Ətraflı");
            toggle.setContentDescription("Cədvəl görünüşünü dəyiş");
            toggle.setOnClickListener(v->{standingsExpanded=!standingsExpanded;navigate("standings");});
            toolbar.addView(toggle);
            page.addView(toolbar);
            gap(page,8);
            standingsHeader(standingsExpanded);
            String lastGroup="";
            for(int i=0;i<Math.min(rows.length(),50);i++){
                JSONObject r=rows.optJSONObject(i);if(r==null)continue;
                String group=r.optString("group","");
                if(!group.isEmpty()&&!group.equals(lastGroup)){
                    section(group);
                    standingsHeader(standingsExpanded);
                    lastGroup=group;
                }
                standingRow(r,i,standingsExpanded);
            }
            gap(page,10);
            info("O: Oyun · Q: Qələbə · H: Heç-heçə · M: Məğlubiyyət · QF: Qol fərqi · XAL: Toplanan xal",false);
            info("Yaşıl sıralar vizual vurğudur, yüksəlmə/düşmə zonası üçün rəsmi təminat deyil.",false);
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
        ((InputMethodManager)getSystemService(INPUT_METHOD_SERVICE)).hideSoftInputFromWindow(page.getWindowToken(),0);
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
            for(int i=0;i<Math.min(arr.length(),75);i++){
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
        JSONObject match=currentMatch;
        JSONObject home=match.optJSONObject("home"),away=match.optJSONObject("away");
        String homeName=val(home,"name"),awayName=val(away,"name");
        section(match.optString("leagueName","MATÇ MƏRKƏZİ"));
        LinearLayout hero=column();
        hero.setPadding(dp(13),dp(15),dp(13),dp(15));
        hero.setBackground(shape(CARD,16));
        LinearLayout teams=row();
        for(JSONObject side:new JSONObject[]{home,away}){
            LinearLayout team=column();team.setGravity(Gravity.CENTER);
            String name=val(side,"name");
            TeamBadge badge=new TeamBadge(this,name,side==null?"":side.optString("image"),42);
            LinearLayout.LayoutParams badgeLayout=new LinearLayout.LayoutParams(dp(42),dp(42));badgeLayout.gravity=Gravity.CENTER_HORIZONTAL;
            team.addView(badge,badgeLayout);gap(team,7);
            TextView label=single(name,12,INK,true);label.setGravity(Gravity.CENTER);team.addView(label);
            teams.addView(team,new LinearLayout.LayoutParams(0,-2,1));
            if(side==home){
                TextView score=single("scheduled".equals(match.optString("state"))?"– : –":val(match,"homeScore")+" : "+val(match,"awayScore"),22,INK,true);
                score.setGravity(Gravity.CENTER);teams.addView(score,new LinearLayout.LayoutParams(dp(96),-2));
            }
        }
        hero.addView(teams);gap(hero,12);
        TextView status=text(stateLabel(match,false)+" · "+match.optString("source",""),11,MUTED,true);
        status.setGravity(Gravity.CENTER);hero.addView(status);
        page.addView(hero);gap(page,11);
        String[] parts=match.optString("id").split(":",3);
        if(parts.length!=3||!Arrays.asList("espn","sportsdb","open").contains(parts[0])){
            banner("Bu matç üçün doğrulanmış hadisə mənbəyi yoxdur.",MUTED);return;
        }
        final int token=generation;
        info("Mənbədən real matç məlumatları alınır…",false);
        fetch("/api/match-detail?provider="+parts[0]+"&league="+encode(parts[1])+"&id="+encode(parts[2]),(data,error)->{
            if(token!=generation||!screen.equals("details"))return;
            // Remove only the last progress card; keep the score header.
            if(page.getChildCount()>3)page.removeViewAt(page.getChildCount()-1);
            if(error!=null){banner("Məlumat alınmadı: "+error.getMessage(),RED);return;}
            if(!data.optBoolean("available"))
                banner(data.optString("message","Detallar mövcud deyil."),RED);
            if(data.optBoolean("partial"))banner("Mənbənin bəzi hissələri əlçatan deyil.",RED);
            JSONArray stats=data.optJSONArray("statistics");
            if(stats!=null&&stats.length()>0){
                section("MATÇ STATİSTİKASI");
                for(int i=0;i<Math.min(stats.length(),32);i++){
                    JSONObject stat=stats.optJSONObject(i);
                    if(stat==null)continue;
                    LinearLayout line=row();
                    line.setPadding(dp(9),dp(8),dp(9),dp(8));
                    line.addView(fixed(val(stat,"home"),12,INK,true,48));
                    TextView title=single(stat.optString("name",stat.optString("label","Statistika")),11,MUTED,false);
                    title.setGravity(Gravity.CENTER);line.addView(title,new LinearLayout.LayoutParams(0,-2,1));
                    line.addView(fixed(val(stat,"away"),12,INK,true,48));
                    line.setBackgroundColor(i%2==0?CARD:RAISED);
                    page.addView(line);
                }
            }else info("Mənbədə təsdiqlənmiş statistika yoxdur.",false);
            JSONObject lineup=data.optJSONObject("lineup");
            if(lineup!=null){
                section("TƏSDİQLƏNMİŞ HEYƏTLƏR");
                for(String side:new String[]{"home","away"}){
                    JSONObject squad=lineup.optJSONObject(side);
                    if(squad==null)continue;
                    JSONArray starters=squad.optJSONArray("starters");
                    JSONArray subs=squad.optJSONArray("substitutes");
                    if((starters==null||starters.length()==0)&&(subs==null||subs.length()==0))continue;
                    String team=side.equals("home")?homeName:awayName;
                    section(team+" · "+(squad.optBoolean("formationVerified")?squad.optString("formation",""):"Düzülüş təsdiqlənməyib"));
                    if(squad.optBoolean("incomplete"))banner("Heyət mənbədə natamamdır.",RED);
                    addSquad("İlk 11",starters);
                    addSquad("Ehtiyatlar",subs);
                }
            }
            JSONArray events=data.optJSONArray("events");
            if(events!=null&&events.length()>0){
                section("MATÇ HADİSƏLƏRİ");
                for(int i=0;i<Math.min(events.length(),60);i++){
                    JSONObject event=events.optJSONObject(i);if(event==null)continue;
                    String when=event.optString("clock",event.optString("minute",""));
                    String title=event.optString("text",event.optString("type",""));
                    LinearLayout line=row();line.setPadding(dp(6),dp(8),dp(6),dp(8));
                    line.addView(fixed(when,11,ACCENT,true,50));
                    line.addView(text(title.isEmpty()?"Təfsilat yoxdur":title,12,INK,false),new LinearLayout.LayoutParams(0,-2,1));
                    card(line);
                }
            }else info("Mənbədə təsdiqlənmiş hadisə siyahısı yoxdur.",false);
            String note=data.optString("message","");
            if(!note.isEmpty()&&data.optBoolean("available"))info(note,false);
        });
    }
    private void addSquad(String label,JSONArray entries){
        if(entries==null||entries.length()==0)return;
        TextView h=text(label+" · "+entries.length(),12,MUTED,true);
        h.setPadding(dp(6),dp(7),0,dp(4));page.addView(h);
        for(int i=0;i<Math.min(entries.length(),22);i++){
            JSONObject player=entries.optJSONObject(i);if(player==null)continue;
            LinearLayout line=row();line.setPadding(dp(7),dp(6),dp(7),dp(6));
            line.addView(fixed(val(player,"number"),11,ACCENT,true,28));
            String detail=val(player,"name");
            if(!"—".equals(val(player,"position")))detail+=" · "+val(player,"position");
            line.addView(single(detail,12,INK,false),new LinearLayout.LayoutParams(0,-2,1));
            page.addView(line);
            line(line);
        }
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
        LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(-1,dp(395));lp.bottomMargin=dp(12);page.addView(pitch,lp);
        info("Düzülüş yerli olaraq çəkilir. Təsdiqlənməmiş oyunçu adları göstərilmir.",false);
    }
    private void showSettings(){
        section("MATCHLAB AZ Native 0.9.47");
        info("Ekranlar yalnız Android Java komponentlərindən qurulub. Veb səhifə göstərilmir.",false);
        info("Canlı matçlar və profillər HTTPS JSON API-dən gəlir. Mənbələrdə boşluqlar ola bilər.",false);
        Button statusButton=button("Server vəziyyətini yoxla");
        statusButton.setOnClickListener(v->{
            fetch("/api/status",(json,error)->{
                if(error!=null){info("Bağlantı: "+error.getMessage(),true);return;}
                info("Versiya: "+json.optString("version")+" · Arxiv: "+(json.optJSONObject("world")!=null?json.optJSONObject("world").optString("total","—"):"—"),false);
            });
        });card(statusButton);
    }

    private void showMenu(View anchor){
        PopupMenu popup=new PopupMenu(this,anchor);
        popup.getMenu().add(0,1,0,"Canlı matçlar");
        popup.getMenu().add(0,2,1,"Axtarış");
        popup.getMenu().add(0,3,2,"Seçilmişlər");
        popup.getMenu().add(0,4,3,"Tənzimləmələr və server");
        popup.getMenu().add(0,5,4,"Android tətbiq məlumatları");
        popup.setOnMenuItemClickListener(item->{
            switch(item.getItemId()){
                case 1:navigate("matches");return true;
                case 2:navigate("search");return true;
                case 3:navigate("favorites");return true;
                case 4:navigate("settings");return true;
                case 5:
                    Intent intent=new Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS,
                        android.net.Uri.parse("package:"+getPackageName()));
                    try{startActivity(intent);}
                    catch(Exception ex){Toast.makeText(this,"Tətbiq məlumatları açılmadı",Toast.LENGTH_SHORT).show();}
                    return true;
                default:return false;
            }
        });
        popup.show();
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
