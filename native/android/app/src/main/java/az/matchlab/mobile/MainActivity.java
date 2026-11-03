package az.matchlab.mobile;

import android.app.Activity;
import android.app.AlertDialog;
import android.graphics.drawable.ColorDrawable;
import android.media.ToneGenerator;
import android.media.AudioManager;
import android.content.ClipboardManager;
import android.content.ClipData;
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
    private static final String[] LEAGUES={"all","aze.1","eng.1","esp.1","ger.1","ita.1","fra.1","uefa.champions","uefa.europa","uefa.europa.conf","tur.1","por.1","ned.1","sco.1","bel.1","usa.1","ksa.1","eng.2","arg.1","bra.1","jpn.1","mex.1"};
    private static final String[] NAMES={"Bütün liqalar","Azərbaycan Premyer Liqası","Premier League","La Liga","Bundesliga","Serie A","Ligue 1","Çempionlar Liqası","Avropa Liqası","Konfrans Liqası","Süper Lig","Primeira Liga","Eredivisie","Scottish Premiership","Belgian Pro League","MLS","Saudi Pro League","Championship","Argentina Primera","Brasileirão","J1 League","Liga MX"};
    private final ExecutorService network=Executors.newFixedThreadPool(3);
    private final Handler ui=new Handler(Looper.getMainLooper());
    private LinearLayout body, nav, page;
    private ScrollView contentScroll;
    private int bottomInset=-1,topInset=-1;
    private TextView header, status;
    private String screen="matches", league="all", kind="all", searchText="";
    private Calendar day=Calendar.getInstance(TimeZone.getTimeZone("Asia/Baku"));
    private int generation=0, formation=0;
    private String matchMode="all";
    private final Set<String> collapsedLeagues=new HashSet<>();
    private int searchOffset=0;
    private JSONArray searchRows=new JSONArray();
    private boolean standingsExpanded=false;
    private final String[] formations={"4-3-3","4-2-3-1","4-4-2","3-5-2","3-4-3","4-1-4-1","5-3-2","4-2-2-2"};
    private JSONArray matches=new JSONArray();
    private LinearLayout searchResults;
    private Runnable searchPending;
    private String matchLeague="all",tableLeague="eng.1";
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
        matchLeague=prefs.getString("matchleague","all");
        tableLeague=prefs.getString("tableleague","eng.1");
        league=matchLeague;
        matchMode=prefs.getString("matchmode","all");
        formation=prefs.getInt("tactic_formation",0);
        if(formation<0||formation>=formations.length)formation=0;
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
    private String networkMessage(Exception error){
        if(error instanceof java.net.UnknownHostException)
            return "İnternet və ya server bağlantısı yoxdur. Wi-Fi/mobil interneti yoxla.";
        if(error instanceof java.net.SocketTimeoutException)
            return "Server gec cavab verir. Bir qədər sonra təkrar yoxla.";
        String message=error==null?"":error.getMessage();
        if(message!=null&&message.startsWith("HTTP "))return "Server cavab vermədi ("+message+").";
        return "Real məlumatları yükləmək mümkün olmadı. Bağlantını yoxla.";
    }
    private void retry(String target){
        Button b=button("↻  Yenidən yoxla");
        b.setTextColor(ACCENT);
        b.setOnClickListener(v->navigate(target));
        card(b);
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
        if(name.equals("matches"))league=matchLeague;
        else if(name.equals("standings"))league=tableLeague;
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
        if(!standings){
            LinearLayout dateBar=row();
            Button previous=button("‹");previous.setContentDescription("Əvvəlki gün");
            previous.setOnClickListener(v->{day.add(Calendar.DATE,-1);navigate("matches");});
            dateBar.addView(previous,new LinearLayout.LayoutParams(dp(45),dp(42)));
            TextView current=text(new SimpleDateFormat("EEE, d MMM",new Locale("az")).format(day.getTime()),13,INK,true);
            current.setGravity(Gravity.CENTER);
            dateBar.addView(current,new LinearLayout.LayoutParams(0,dp(42),1));
            Button next=button("›");next.setContentDescription("Növbəti gün");
            next.setOnClickListener(v->{day.add(Calendar.DATE,1);navigate("matches");});
            dateBar.addView(next,new LinearLayout.LayoutParams(dp(45),dp(42)));
            Button today=button("Bu gün");
            today.setOnClickListener(v->{day=Calendar.getInstance(TimeZone.getTimeZone("Asia/Baku"));navigate("matches");});
            dateBar.addView(today,new LinearLayout.LayoutParams(dp(76),dp(42)));
            card(dateBar);
            LinearLayout chips=row();
            String[][] types={{"all","Hamısı"},{"live","● Canlı"},{"favorites","☆ Seçilmiş"}};
            for(String[] type:types){
                boolean selected=matchMode.equals(type[0]);
                Button tab=button(type[1]);
                tab.setTextColor(selected?BG:MUTED);
                tab.setBackground(shape(selected?ACCENT:RAISED,13));
                LinearLayout.LayoutParams w=new LinearLayout.LayoutParams(0,dp(42),1);
                w.rightMargin=dp(5);
                chips.addView(tab,w);
                tab.setOnClickListener(v->{
                    if(!matchMode.equals(type[0])){
                        matchMode=type[0];prefs.edit().putString("matchmode",matchMode).apply();
                        navigate("matches");
                    }
                });
            }
            card(chips);
            LinearLayout controls=row();
            TextView label=single(league.equals("all")?"Bütün liqalar":"Liqa: "+leagueLabel(league),12,MUTED,true);
            controls.addView(label,new LinearLayout.LayoutParams(0,dp(42),1));
            Button choose=button("Filtrlə  ⌄");
            choose.setOnClickListener(v->showLeaguePicker(choose,false));
            controls.addView(choose);
            card(controls);
            if(!league.equals("all")){
                TextView note=text("Bu liqa seçimi yalnız bu ekranın filtridir. “Bütün liqalar” seçərək ümumi matçlara qayıt.",10,MUTED,false);
                card(note);
            }
            return;
        }
        LinearLayout controls=row();
        TextView hint=single(leagueLabel(league),12,ACCENT,true);
        controls.addView(hint,new LinearLayout.LayoutParams(0,dp(42),1));
        Button choose=button("Liqa  ⌄");
        choose.setOnClickListener(v->showLeaguePicker(choose,true));
        controls.addView(choose);
        card(controls);
    }
    private String leagueLabel(String id){
        int at=Arrays.asList(LEAGUES).indexOf(id);
        return at<0?id:NAMES[at];
    }
    private void themedPicker(String title,ArrayList<String> ids,ArrayList<String> labels,boolean standings){
        LinearLayout box=column();box.setPadding(dp(16),dp(12),dp(16),dp(12));box.setBackground(shape(CARD,18));
        TextView heading=text(title,19,INK,true);box.addView(heading);gap(box,12);
        EditText search=new EditText(this);search.setSingleLine(true);search.setHint("Liqa axtar…");
        search.setTextColor(INK);search.setHintTextColor(MUTED);search.setBackground(shape(RAISED,12));
        search.setPadding(dp(12),0,dp(12),0);box.addView(search,new LinearLayout.LayoutParams(-1,dp(48)));
        ScrollView scroll=new ScrollView(this);LinearLayout results=column();scroll.addView(results);
        LinearLayout.LayoutParams scrollParams=new LinearLayout.LayoutParams(-1,0,1);scrollParams.topMargin=dp(10);
        box.addView(scroll,scrollParams);
        AlertDialog dialog=new AlertDialog.Builder(this).setView(box).create();
        Runnable update=()->{
            results.removeAllViews();
            String q=search.getText().toString().toLowerCase(Locale.ROOT);
            for(int i=0;i<labels.size();i++){
                final String id=ids.get(i),label=labels.get(i);
                if(!label.toLowerCase(Locale.ROOT).contains(q))continue;
                TextView item=text((id.equals(league)?"✓  ":"   ")+label,15,id.equals(league)?ACCENT:INK,id.equals(league));
                item.setPadding(dp(12),dp(14),dp(12),dp(14));item.setBackground(shape(RAISED,10));
                LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(-1,-2);p.bottomMargin=dp(5);results.addView(item,p);
                item.setOnClickListener(v->{
                    dialog.dismiss();
                    if(id.equals("__more__")){showAllLeaguesPicker(standings);return;}
                    league=id;if(standings)tableLeague=id;else matchLeague=id;
                    prefs.edit().putString(standings?"tableleague":"matchleague",id).apply();
                    navigate(standings?"standings":"matches");
                });
            }
            if(results.getChildCount()==0)results.addView(text("Uyğun liqa tapılmadı",13,MUTED,false));
        };
        search.addTextChangedListener(new android.text.TextWatcher(){
            public void beforeTextChanged(CharSequence s,int start,int count,int after){}
            public void onTextChanged(CharSequence s,int start,int before,int count){update.run();}
            public void afterTextChanged(android.text.Editable e){}
        });
        update.run();dialog.show();
        if(dialog.getWindow()!=null){dialog.getWindow().setBackgroundDrawable(new ColorDrawable(Color.TRANSPARENT));
            dialog.getWindow().setLayout(getResources().getDisplayMetrics().widthPixels-dp(28),Math.min(dp(620),getResources().getDisplayMetrics().heightPixels-dp(110)));}
    }
    private void showLeaguePicker(View anchor,boolean standings){
        ArrayList<String> ids=new ArrayList<>(),labels=new ArrayList<>();
        for(int i=standings?1:0;i<LEAGUES.length;i++){ids.add(LEAGUES[i]);labels.add(NAMES[i]);}
        ids.add("__more__");labels.add("＋  Bütün liqalar");
        themedPicker(standings?"Turnir cədvəli":"Matç filtri",ids,labels,standings);
    }
    private void showAllLeaguesPicker(boolean standings){
        fetch("/api/leagues",(data,error)->{
            if(isFinishing()||isDestroyed())return;
            if(error!=null||data==null){Toast.makeText(this,"Liqa kataloqu yüklənmədi",Toast.LENGTH_LONG).show();return;}
            JSONArray items=data.optJSONArray("items");if(items==null)return;
            ArrayList<String> labels=new ArrayList<>(),ids=new ArrayList<>();
            for(int i=0;i<items.length();i++){
                JSONObject item=items.optJSONObject(i);if(item==null)continue;
                String id=item.optString("id"),name=item.optString("name");
                if(id.isEmpty()||name.isEmpty())continue;ids.add(id);labels.add(name);
            }
            themedPicker("Bütün yarışlar",ids,labels,standings);
        });
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
    private boolean matchVisible(JSONObject match){
        String state=match.optString("state","");
        if("live".equals(matchMode))return "live".equals(state)&&!match.optBoolean("stale");
        if("favorites".equals(matchMode))return prefs.contains("fav_"+match.optString("id"));
        return true;
    }
    private void renderLiveMatches(JSONObject data){
        matches=data.optJSONArray("items");if(matches==null)matches=new JSONArray();
        page.removeAllViews();filters(false);
        if(data.optBoolean("partial")||data.optBoolean("stale"))
            banner("Mənbənin bəzi liqaları əlçatan deyil. Köhnə məlumat canlı göstərilmir.",RED);
        int count=0,live=0;
        LinkedHashMap<String,ArrayList<JSONObject>> groups=new LinkedHashMap<>();
        for(int i=0;i<matches.length();i++){
            JSONObject m=matches.optJSONObject(i);if(m==null||!matchVisible(m))continue;
            count++;
            if("live".equals(m.optString("state"))&&!m.optBoolean("stale"))live++;
            String group=m.optString("leagueName",leagueLabel(m.optString("league","")));
            if(group.trim().isEmpty())group="Digər yarışlar";
            groups.computeIfAbsent(group,k->new ArrayList<>()).add(m);
        }
        banner(count+" matç · "+live+" canlı  |  "+data.optString("source","Mənbə yoxlanır"),ACCENT);
        String note=data.optString("message","");
        if(!note.isEmpty()&&(count==0||data.optBoolean("stale")))
            info(note,!data.optBoolean("available"));
        if(count==0){
            if("favorites".equals(matchMode))info("Bu tarixdə seçilmiş oyun yoxdur. Matç kartlarındakı ☆ işarəsinə toxun.",false);
            else if("live".equals(matchMode))info("Hazırda təsdiqlənmiş canlı oyun yoxdur. “Hamısı” bölməsində bütün oyunlara bax.",false);
            else info(data.optBoolean("available")?"Seçilmiş tarixdə mənbələr oyun qaytarmadı.":"Matçlar mənbədən alınmadı.",!data.optBoolean("available"));
            return;
        }
        // Priority follows the actual fixture list, not a permanent hardcoded league panel.
        for(Map.Entry<String,ArrayList<JSONObject>> group:groups.entrySet()){
            String name=group.getKey();
            boolean collapsed=collapsedLeagues.contains(name);
            LinearLayout heading=row();
            heading.setPadding(dp(12),dp(9),dp(10),dp(9));
            TextView title=single(name,13,INK,true);
            heading.addView(title,new LinearLayout.LayoutParams(0,dp(29),1));
            TextView meta=single(group.getValue().size()+" oyun  "+(collapsed?"⌄":"⌃"),11,ACCENT,true);
            heading.addView(meta);
            heading.setBackground(shape(RAISED,12));
            heading.setClickable(true);
            heading.setContentDescription(name+" liqası, "+group.getValue().size()+" oyun");
            heading.setOnClickListener(v->{
                if(!collapsedLeagues.add(name))collapsedLeagues.remove(name);
                renderLiveMatches(data);
            });
            LinearLayout.LayoutParams h=new LinearLayout.LayoutParams(-1,-2);
            h.topMargin=dp(7);h.bottomMargin=dp(5);page.addView(heading,h);
            if(!collapsed){
                for(JSONObject m:group.getValue())matchRow(m,false);
            }
        }
    }
    private void loadMatches(boolean reset){
        int token=generation;
        if(reset){filters(false);banner("Real matçlar yüklənir…",MUTED);}
        fetch("/api/live?league="+encode(league)+"&date="+date(),(json,error)->{
            if(token!=generation||!screen.equals("matches"))return;
            if(error!=null||json==null){
                page.removeAllViews();filters(false);
                status.setTextColor(RED);
                info(networkMessage(error),true);retry("matches");return;
            }
            status.setTextColor(json.optBoolean("available")?ACCENT:RED);
            renderLiveMatches(json);
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
        if("all".equals(league))league="eng.1";
        filters(true);
        info("Turnir cədvəli mənbədən alınır…",false);
        int token=generation;
        String requestLeague=league;
        fetch("/api/standings?league="+encode(requestLeague),(data,error)->{
            if(token!=generation||!screen.equals("standings"))return;
            page.removeAllViews();
            filters(true);
            if(error!=null){banner(networkMessage(error),RED);retry("standings");return;}
            if(data.optBoolean("stale"))banner("Bu cədvəl cari olmaya bilər — mənbə köhnəlmiş məlumat qaytardı.",RED);
            if(data.optBoolean("partial"))banner("Bəzi cədvəl məlumatları mənbədən alınmadı.",RED);
            JSONArray rows=data.optJSONArray("items");
            if(rows==null||rows.length()==0){
                banner(data.optString("message","Cədvəl mövcud deyil."),RED);
                if("aze.1".equals(requestLeague))externalLink("Rəsmi PFL saytı","https://pfl.az/");
                return;
            }
            section(leagueLabel(requestLeague));
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
        section("DÜNYA FUTBOL ARXİVİ");
        info("Futbolçu, klub və məşqçiləri real reyestrdə axtar. Sonuçlar yalnız mənbədən alınır.",false);
        LinearLayout bar=row();
        EditText query=new EditText(this);
        query.setSingleLine(true);
        query.setHint("Ad, klub, ölkə…");query.setHintTextColor(MUTED);
        query.setTextColor(INK);query.setTextSize(15);query.setText(searchText);
        query.setImeOptions(android.view.inputmethod.EditorInfo.IME_ACTION_SEARCH);
        query.setBackground(shape(RAISED,13));query.setPadding(dp(12),dp(8),dp(10),dp(8));
        bar.addView(query,new LinearLayout.LayoutParams(0,dp(48),1));
        Button search=button("⌕  Axtar");search.setTextColor(BG);search.setBackground(shape(ACCENT,12));
        LinearLayout.LayoutParams buttonParams=new LinearLayout.LayoutParams(dp(89),dp(48));buttonParams.leftMargin=dp(8);
        bar.addView(search,buttonParams);page.addView(bar);
        gap(page,9);
        LinearLayout types=row();
        String[][] names={{"all","Hamısı"},{"players","Oyunçular"},{"teams","Klublar"},{"coaches","Məşqçilər"}};
        for(String[] entry:names){
            boolean selected=entry[0].equals(kind);
            Button filter=button(entry[1]);filter.setTextSize(10);
            filter.setMinHeight(dp(38));filter.setMinimumHeight(dp(38));
            filter.setTextColor(selected?BG:MUTED);
            filter.setBackground(shape(selected?ACCENT:RAISED,11));
            LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(0,dp(39),1);p.rightMargin=dp(4);
            types.addView(filter,p);
            filter.setOnClickListener(v->{
                if(!kind.equals(entry[0])){
                    kind=entry[0];
                    searchText=query.getText().toString().trim();
                    navigate("search");
                }
            });
        }
        page.addView(types);
        gap(page,10);
        searchResults=column();
        page.addView(searchResults);
        final Runnable searchNow=()->{
            if(searchPending!=null)ui.removeCallbacks(searchPending);
            searchText=query.getText().toString().trim();
            loadSearch(searchText,kind,0);
        };
        search.setOnClickListener(v->searchNow.run());
        query.setOnEditorActionListener((v,action,event)->{
            if(action==android.view.inputmethod.EditorInfo.IME_ACTION_SEARCH){searchNow.run();return true;}
            return false;
        });
        query.addTextChangedListener(new android.text.TextWatcher(){
            @Override public void beforeTextChanged(CharSequence t,int start,int count,int after){}
            @Override public void onTextChanged(CharSequence t,int start,int before,int count){
                if(searchPending!=null)ui.removeCallbacks(searchPending);
                String q=t.toString().trim();
                if(q.length()>=3){
                    searchPending=()->{searchText=q;loadSearch(q,kind,0);};
                    ui.postDelayed(searchPending,550);
                }else{
                    searchText=q;
                    searchResults.removeAllViews();
                    renderQuickSearch(query,searchNow);
                }
            }
            @Override public void afterTextChanged(android.text.Editable e){}
        });
        if(searchText.length()>=2)loadSearch(searchText,kind,0);
        else renderQuickSearch(query,searchNow);
    }
    private void renderQuickSearch(EditText query,Runnable action){
        if(searchResults==null)return;
        searchResults.removeAllViews();
        TextView title=text("SÜRƏTLİ AXTARIŞ",11,MUTED,true);searchResults.addView(title);
        gap(searchResults,7);
        // Examples are search terms, not claimed search results.
        for(String hint:new String[]{"Qarabağ","Azərbaycan","Real Madrid","Mbappé","Barcelona","Neftçi"}){
            TextView term=single("⌕   "+hint,13,INK,false);
            term.setPadding(dp(13),dp(9),dp(13),dp(9));term.setBackground(shape(CARD,10));
            LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(-1,-2);p.bottomMargin=dp(6);
            searchResults.addView(term,p);
            term.setOnClickListener(v->{query.setText(hint);query.setSelection(hint.length());action.run();});
        }
        gap(searchResults,7);
        TextView note=text("Adın üzərinə toxunaraq arxivdə axtarış et. Yuxarıdakı nümunələr nəticə deyil.",11,MUTED,false);
        searchResults.addView(note);
    }
    private void loadSearch(String q,String requestedKind,int offset){
        if(searchResults==null||!screen.equals("search"))return;
        if(q.trim().isEmpty()){
            searchResults.removeAllViews();
            info("Axtarış üçün ad yaz.",false);return;
        }
        ((InputMethodManager)getSystemService(INPUT_METHOD_SERVICE))
            .hideSoftInputFromWindow(page.getWindowToken(),0);
        final int token=generation;
        final String query=q.trim();
        if(offset==0){searchResults.removeAllViews();searchRows=new JSONArray();}
        TextView waiting=text(offset==0?"Reyestr axtarılır…":"Daha çox nəticə alınır…",12,MUTED,false);
        searchResults.addView(waiting);
        fetch("/api/search?q="+encode(query)+"&kind="+requestedKind+"&offset="+offset,(json,error)->{
            if(token!=generation||!screen.equals("search")||!query.equals(searchText)||!requestedKind.equals(kind))return;
            searchResults.removeView(waiting);
            if(error!=null||json==null){
                searchResults.addView(text(networkMessage(error),12,RED,false));return;
            }
            JSONArray arr=json.optJSONArray("items");
            if(arr==null||arr.length()==0){
                if(offset==0)searchResults.addView(text("Bu sorğu üçün təsdiqlənmiş nəticə tapılmadı.",12,MUTED,false));
                return;
            }
            if(offset==0){
                TextView source=text("Mənbə: "+json.optString("source","bilinmir"),10,MUTED,false);
                source.setPadding(dp(2),dp(5),0,dp(7));searchResults.addView(source);
            }
            for(int i=0;i<Math.min(arr.length(),75);i++){
                JSONObject item=arr.optJSONObject(i);if(item==null)continue;
                LinearLayout row=row();row.setPadding(dp(11),dp(10),dp(11),dp(10));
                row.setBackground(shape(CARD,12));
                String label=item.optString("name","—");
                TextView avatar=fixed(label.isEmpty()?"•":label.substring(0,1).toUpperCase(),16,ACCENT,true,39);
                row.addView(avatar);
                LinearLayout detail=column();
                detail.addView(single(label,14,INK,true));
                String category=item.optString("kind","").replace("players","Futbolçu").replace("teams","Klub").replace("coaches","Məşqçi");
                detail.addView(single(category+" · "+item.optString("country","Məlum deyil"),11,MUTED,false));
                row.addView(detail,new LinearLayout.LayoutParams(0,-2,1));
                row.addView(text("›",22,MUTED,true));
                row.setOnClickListener(v->openProfile(item.optString("id","")));
                LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(-1,-2);p.bottomMargin=dp(6);
                searchResults.addView(row,p);
            }
            if(!json.isNull("nextOffset")){
                int next=json.optInt("nextOffset",-1);
                if(next>offset){
                    Button more=button("Daha "+(next-offset)+" nəticə göstər");
                    more.setOnClickListener(v->{searchResults.removeView(more);loadSearch(query,requestedKind,next);});
                    searchResults.addView(more);
                }
            }
        });
    }
    private void profileFact(String label,String value){
        if(value==null||value.trim().isEmpty()||value.equalsIgnoreCase("null")||value.equalsIgnoreCase("unknown")||value.equalsIgnoreCase("unverified"))return;
        LinearLayout line=row();TextView a=text(label,12,MUTED,true);line.addView(a,new LinearLayout.LayoutParams(0,-2,1));
        TextView b=text(value,13,INK,false);b.setGravity(Gravity.RIGHT);line.addView(b,new LinearLayout.LayoutParams(0,-2,2));card(line);
    }
    private void externalLink(String label,String url){
        if(url==null||!url.startsWith("https://"))return;
        Button b=button("↗  "+label);b.setTextColor(ACCENT);
        b.setOnClickListener(v->{try{startActivity(new Intent(Intent.ACTION_VIEW,android.net.Uri.parse(url)));}catch(Exception e){Toast.makeText(this,"Keçid açıla bilmədi",Toast.LENGTH_SHORT).show();}});
        card(b);
    }
    private void openProfile(String id){
        navigate("profile");int token=generation;info("Profil yüklənir…",false);
        fetch("/api/profile?id="+encode(id),(data,error)->{
            if(token!=generation||!screen.equals("profile"))return;
            page.removeAllViews();
            if(error!=null){info(networkMessage(error),true);retry("search");return;}
            JSONObject p=data.optJSONObject("profile");if(p==null){info("Profil tapılmadı",true);return;}
            section(p.optString("name","—"));
            String kind=p.optString("kind"),name=p.optString("name");
            LinearLayout hero=row();
            TeamBadge badge=new TeamBadge(this,name,p.optString("image"),70);
            hero.addView(badge,new LinearLayout.LayoutParams(dp(70),dp(70)));
            LinearLayout caption=column();caption.setPadding(dp(15),0,0,0);
            caption.addView(text(name,19,INK,true));
            caption.addView(text(("teams".equals(kind)?"Klub":("coaches".equals(kind)?"Məşqçi":"Futbolçu"))+" · "+p.optString("country",""),12,MUTED,false));
            hero.addView(caption,new LinearLayout.LayoutParams(0,-2,1));card(hero);
            section("Ümumi məlumat");
            profileFact("Ölkə",p.optString("country"));
            profileFact("Doğum tarixi",p.optString("birth"));
            profileFact("Vəfat tarixi",p.optString("death"));
            profileFact("Mövqe",p.optString("position"));
            profileFact("Haqqında",p.optString("description"));
            for(String k:new String[]{"clubs","coached","awards"}){
                JSONArray arr=p.optJSONArray(k);if(arr==null||arr.length()==0)continue;
                section(k.equals("clubs")?"Klub karyerası":k.equals("coached")?"Məşqçilik karyerası":"Nailiyyətlər");
                for(int i=0;i<Math.min(45,arr.length());i++){
                    Object o=arr.opt(i);JSONObject obj=o instanceof JSONObject?(JSONObject)o:null;
                    String label=obj==null?String.valueOf(o):obj.optString("name",String.valueOf(o));
                    if(!label.isEmpty())info("• "+label,false);
                }
            }
            section("Mənbələr və keçidlər");
            String qid=p.optString("wikidataId",p.optString("qid",""));
            if(qid.matches("Q[1-9][0-9]{0,11}")){
                externalLink("Wikidata profili","https://www.wikidata.org/wiki/"+qid);
                externalLink("Wikipedia məqalələri","https://www.wikidata.org/wiki/Special:SiteLinks/"+qid);
            }
            String url=p.optString("wikipediaUrl",p.optString("url",""));
            if(url.startsWith("https://"))externalLink("Mənbə səhifəsi",url);
            profileFact("Məlumat mənbəyi",p.optString("source"));
            if("teams".equals(kind)){
                externalLink("Klubun rəsmi saytı — axtar","https://www.google.com/search?q="+encode(name+" official football club website"));
                externalLink("Klubun oyunları və nəticələri","https://www.google.com/search?q="+encode(name+" fixtures results"));
                externalLink("Klubun heyəti və transferləri","https://www.google.com/search?q="+encode(name+" squad transfers"));
            }else{
                externalLink("Mövsüm statistikası — axtar","https://www.google.com/search?q="+encode(name+" football statistics 2026"));
                externalLink("Karyera və transfer tarixçəsi","https://www.google.com/search?q="+encode(name+" football career transfers"));
            }
            externalLink("Wikipedia-da axtar","https://en.wikipedia.org/w/index.php?search="+encode(name));
            if(qid.isEmpty()&&url.isEmpty())info("Bu profil üçün təsdiqlənmiş birbaşa Wikipedia bağlantısı yoxdur.",false);
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
            if(error!=null){banner(networkMessage(error),RED);return;}
            if(!data.optBoolean("available"))
                banner(data.optString("message","Detallar mövcud deyil."),RED);
            if(data.optBoolean("partial"))banner("Mənbənin bəzi hissələri əlçatan deyil.",RED);
            JSONArray stats=data.optJSONArray("statistics");
            if(stats!=null&&stats.length()>0){
                section("MATÇ STATİSTİKASI");
                for(int i=0;i<Math.min(stats.length(),32);i++){
                    JSONObject stat=stats.optJSONObject(i);
                    if(stat==null)continue;
                    LinearLayout block=column();
                    block.setPadding(dp(10),dp(9),dp(10),dp(9));
                    LinearLayout line=row();
                    line.addView(fixed(val(stat,"home"),12,INK,true,48));
                    TextView title=single(stat.optString("name",stat.optString("label","Statistika")),11,MUTED,false);
                    title.setGravity(Gravity.CENTER);line.addView(title,new LinearLayout.LayoutParams(0,-2,1));
                    line.addView(fixed(val(stat,"away"),12,INK,true,48));
                    block.addView(line);
                    double left=statNumber(val(stat,"home")),right=statNumber(val(stat,"away"));
                    if(left>=0&&right>=0&&left+right>0){
                        LinearLayout bar=row();bar.setBackground(shape(RAISED,4));
                        int leftWeight=Math.max(1,(int)Math.round(1000*left/(left+right)));
                        View h=new View(this);h.setBackground(shape(ACCENT,4));
                        bar.addView(h,new LinearLayout.LayoutParams(0,dp(5),leftWeight));
                        View a=new View(this);a.setBackground(shape(Color.rgb(97,122,145),4));
                        bar.addView(a,new LinearLayout.LayoutParams(0,dp(5),1001-leftWeight));
                        LinearLayout.LayoutParams bp=new LinearLayout.LayoutParams(-1,dp(5));bp.topMargin=dp(7);
                        block.addView(bar,bp);
                    }
                    block.setBackgroundColor(i%2==0?CARD:RAISED);
                    page.addView(block);
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
    private double statNumber(String raw){
        if(raw==null)return -1;
        String value=raw.trim().replace("%","").replace(",",".");
        if(!value.matches("[0-9]+(\\.[0-9]+)?"))return -1;
        try{return Double.parseDouble(value);}catch(NumberFormatException e){return -1;}
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
        section("TAKTİKA STUDİYASI");
        banner("İnteraktiv məşq lövhəsi · 11 mövqe · Yerli yaddaş",ACCENT);
        LinearLayout presets=row();
        TextView label=single("Düzülüş",12,MUTED,true);presets.addView(label,new LinearLayout.LayoutParams(0,dp(44),1));
        Button choose=button(formations[formation]+"   ⌄");
        choose.setOnClickListener(v->{
            new AlertDialog.Builder(this).setTitle("Taktiki düzülüş")
                .setSingleChoiceItems(formations,formation,(dialog,index)->{
                    formation=index;prefs.edit().putInt("tactic_formation",formation).apply();
                    dialog.dismiss();navigate("tactics");
                }).setNegativeButton("Bağla",null).show();
        });presets.addView(choose);
        card(presets);
        PitchView pitch=new PitchView(this,formations[formation]);
        LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(-1,dp(460));
        p.bottomMargin=dp(9);page.addView(pitch,p);
        LinearLayout actions=row();
        Button reset=button("↺ Sıfırla");
        reset.setOnClickListener(v->{
            new AlertDialog.Builder(this).setTitle("Düzülüşü sıfırla?")
                .setMessage("Bu düzülüşdə etdiyin mövqe və ad dəyişiklikləri silinəcək.")
                .setNegativeButton("Ləğv et",null)
                .setPositiveButton("Sıfırla",(d,w)->pitch.reset()).show();
        });
        actions.addView(reset,new LinearLayout.LayoutParams(0,dp(46),1));
        Button share=button("📋 Mətn kimi paylaş");
        LinearLayout.LayoutParams space=new LinearLayout.LayoutParams(0,dp(46),1);space.leftMargin=dp(8);
        share.setOnClickListener(v->{
            Intent intent=new Intent(Intent.ACTION_SEND);
            intent.setType("text/plain");
            intent.putExtra(Intent.EXTRA_TEXT,pitch.exportText());
            startActivity(Intent.createChooser(intent,"Taktikanı paylaş"));
        });
        actions.addView(share,space);page.addView(actions);
        gap(page,8);
        LinearLayout tools=row();
        Button grid=button("▦ Tor");grid.setOnClickListener(v->pitch.toggleGrid());tools.addView(grid,new LinearLayout.LayoutParams(0,dp(44),1));
        Button lines=button("⌁ Xətlər");lines.setOnClickListener(v->pitch.toggleLines());tools.addView(lines,new LinearLayout.LayoutParams(0,dp(44),1));
        Button arrows=button("➜ Oxlar");arrows.setOnClickListener(v->pitch.toggleArrows());tools.addView(arrows,new LinearLayout.LayoutParams(0,dp(44),1));
        Button clear=button("✕ Oxları sil");clear.setOnClickListener(v->pitch.clearArrows());tools.addView(clear,new LinearLayout.LayoutParams(0,dp(44),1));
        page.addView(tools);
        gap(page,9);
        info("Oxlar alətini aktivləşdirib meydançada başlanğıc və bitiş nöqtəsinə toxun. Oxlar saxlanılır.",false);
        info("Oyunçunu sürüşdürərək mövqeyini dəyiş. Ad və nömrəni dəyişmək üçün oyunçuya qısa toxun. Dəyişikliklər avtomatik saxlanılır.",false);
        info("Bu plan sənin öz taktiki layihəndir. Real matç heyəti və təsdiqlənmiş formasiya kimi təqdim edilmir.",false);
    }
    private void showSettings(){
        section("MATCHLAB AZ Native 0.9.49");
        section("Bildiriş və səs idarəetməsi");
        for(String[] setting:new String[][]{{"notif_goals","Qol bildirişləri"},{"notif_kickoff","Matç başlanğıcı"},{"notif_halftime","Fasilə"},{"notif_final","Matçın bitməsi"},{"notif_cards","Qırmızı kart"},{"notif_yellow_cards","Sarı kart"},{"notif_assists","Assist"},{"notif_penalties","Penalti"},{"notif_lineups","Heyətlər açıqlananda"},{"notif_corners","Künc zərbəsi"},{"notif_favorites","Yalnız seçilmiş matçlar"},{"sound_enabled","Tətbiqdaxili səs"},{"sound_vibrate","Vibrasiya"}}){
            Switch toggle=new Switch(this);toggle.setText(setting[1]);toggle.setTextSize(13);toggle.setTextColor(INK);
            toggle.setChecked(prefs.getBoolean(setting[0],false));toggle.setPadding(dp(9),dp(9),dp(9),dp(9));
            toggle.setOnCheckedChangeListener((view,checked)->prefs.edit().putBoolean(setting[0],checked).apply());card(toggle);
        }
        section("Bildiriş səslərinin sınağı");
        String[][] previews={{"Qol","TONE_PROP_ACK"},{"Matç başlanğıcı","TONE_PROP_BEEP"},{"Kart","TONE_PROP_NACK"},{"Matçın bitməsi","TONE_PROP_PROMPT"}};
        for(int i=0;i<previews.length;i++){
            final int toneId=i==0?ToneGenerator.TONE_PROP_ACK:i==1?ToneGenerator.TONE_PROP_BEEP:i==2?ToneGenerator.TONE_PROP_NACK:ToneGenerator.TONE_PROP_PROMPT;
            Button soundTest=button("♪ "+previews[i][0]+" səsini sına");
            soundTest.setOnClickListener(v->{
                if(!prefs.getBoolean("sound_enabled",false)){Toast.makeText(this,"Əvvəlcə tətbiqdaxili səsi aktivləşdir",Toast.LENGTH_SHORT).show();return;}
                ToneGenerator tg=new ToneGenerator(AudioManager.STREAM_NOTIFICATION,65);
                tg.startTone(toneId,220);ui.postDelayed(tg::release,350);
            });
            card(soundTest);
        }
                info("Bu seçimlər yerli yaddaşa yazılır. Real hadisə bildirişlərinin avtomatik gəlməsi ayrıca bildiriş mühərriki tələb edir; hələ aktiv deyil.",false);
        info("Ekranlar yalnız Android Java komponentlərindən qurulub. Veb səhifə göstərilmir.",false);
        info("Canlı matçlar və profillər HTTPS JSON API-dən gəlir. Mənbələrdə boşluqlar ola bilər.",false);
        Button statusButton=button("Server vəziyyətini yoxla");
        statusButton.setOnClickListener(v->{
            fetch("/api/status",(json,error)->{
                if(error!=null){info(networkMessage(error),true);return;}
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
    @Override protected void onDestroy(){ui.removeCallbacks(refresh);if(searchPending!=null)ui.removeCallbacks(searchPending);network.shutdownNow();super.onDestroy();}
}
