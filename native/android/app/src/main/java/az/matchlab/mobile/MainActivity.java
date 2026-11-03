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
    private final Map<String,String> scoreBaseline=new HashMap<>();
    private boolean hasScoreBaseline=false;
    private String historyLeague="eng.1",historySeason="2025-26",historyTeam="";
    private final Map<String,JSONObject> historyBundles=new HashMap<>();
    private int historyOffset=0;
    private int searchOffset=0;
    private JSONArray searchRows=new JSONArray();
    private boolean standingsExpanded=false;
    private final String[] formations={"4-3-3","4-2-3-1","4-4-2","3-5-2","3-4-3","4-1-4-1","5-3-2","4-2-2-2"};
    private JSONArray matches=new JSONArray();
    private LinearLayout searchResults;
    private Runnable searchPending;
    private String matchLeague="all",tableLeague="eng.1";
    private JSONObject currentMatch=null;
    private PitchView pendingExportPitch;
    private static final int EXPORT_TACTIC_PNG=957;
    @Override protected void onActivityResult(int requestCode,int resultCode,Intent data){
        super.onActivityResult(requestCode,resultCode,data);
        if(requestCode!=EXPORT_TACTIC_PNG)return;
        if(resultCode!=RESULT_OK||data==null||data.getData()==null||pendingExportPitch==null){
            pendingExportPitch=null;return;
        }
        try(java.io.OutputStream stream=getContentResolver().openOutputStream(data.getData())){
            if(stream==null)throw new IOException("Export stream could not be opened");
            android.graphics.Bitmap bitmap=pendingExportPitch.exportBitmap();
            boolean saved=bitmap.compress(android.graphics.Bitmap.CompressFormat.PNG,100,stream);
            bitmap.recycle();
            if(!saved)throw new IOException("PNG encoding failed");
            Toast.makeText(this,"Taktika PNG saxlandı",Toast.LENGTH_LONG).show();
        }catch(Exception ex){Toast.makeText(this,"PNG saxlanmadı: "+ex.getMessage(),Toast.LENGTH_LONG).show();}
        finally{pendingExportPitch=null;}
    }
    private SharedPreferences prefs;
    private final Runnable refresh=new Runnable(){
        @Override public void run(){
            if("matches".equals(screen)&&prefs.getBoolean("auto_refresh",true))loadMatches(false);
            ui.postDelayed(this,prefs.getInt("refresh_interval",30)*1000L);
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
        ui.postDelayed(refresh,prefs.getInt("refresh_interval",30)*1000L);
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
        LinearLayout wrapper=column();wrapper.setPadding(dp(9),dp(7),dp(9),dp(7));wrapper.setBackground(shape(CARD,10));
        wrapper.addView(v);
        LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(-1,-2);lp.bottomMargin=dp(5);
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
        b.setMinHeight(dp(38));b.setMinimumHeight(dp(38));b.setPadding(dp(6),dp(5),dp(6),dp(5));return b;
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
        ImageView oldLogo=new ImageView(this);
        oldLogo.setImageResource(R.drawable.ic_matchlab_legacy);
        oldLogo.setContentDescription("MATCHLAB AZ orijinal M loqosu");
        LinearLayout.LayoutParams logoSize=new LinearLayout.LayoutParams(dp(37),dp(37));
        logoSize.rightMargin=dp(10);top.addView(oldLogo,logoSize);
        LinearLayout brandBox=column();
        TextView brand=text("MATCHLAB AZ",9,ACCENT,true);brand.setLetterSpacing(.13f);
        brandBox.addView(brand);
        header=text("Canlı matçlar",16,INK,true);brandBox.addView(header);
        top.addView(brandBox,new LinearLayout.LayoutParams(0,-2,1));
        status=text("●",16,ACCENT,true);top.addView(status);
        TextView menu=text("⋮",26,INK,true);menu.setGravity(Gravity.CENTER);
        menu.setContentDescription("Tətbiq menyusu");menu.setClickable(true);
        menu.setOnClickListener(v->showMenu(menu));
        top.addView(menu,new LinearLayout.LayoutParams(dp(40),dp(45)));
        top.setBackgroundColor(Color.rgb(13,28,42));
        body.addView(top,new LinearLayout.LayoutParams(-1,dp(56)));
        ScrollView scroll=new ScrollView(this);contentScroll=scroll;scroll.setFillViewport(false);
        scroll.setClipToPadding(false);
        page=column();page.setPadding(dp(9),dp(4),dp(9),dp(12));scroll.addView(page);
        body.addView(scroll,new LinearLayout.LayoutParams(-1,0,1));
        nav=row();nav.setBackgroundColor(Color.rgb(14,30,46));
        nav.setMinimumHeight(dp(56));
        body.addView(nav,new LinearLayout.LayoutParams(-1,dp(59)));
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
        header.setText(name.equals("matches")?"Canlı matçlar":name.equals("standings")?"Turnir cədvəli":name.equals("search")?"Axtarış":name.equals("tactics")?"Taktika":name.equals("favorites")?"Seçilmişlər":name.equals("details")?"Matç mərkəzi":name.equals("profile")?"Futbol profili" :"history".equals(name)?"Tarixi futbol arxivi":"Tənzimləmələr");
        nav.removeAllViews();
        String[][] items={{"matches","⚽","Matçlar"},{"standings","▤","Cədvəl"},{"search","⌕","Axtar"},{"favorites","☆","Seçilmiş"},{"tactics","▦","Taktika"}};
        for(String[] item:items){
            LinearLayout cell=column();cell.setGravity(Gravity.CENTER);
            boolean active=name.equals(item[0]);
            NavGlyph glyph=new NavGlyph(this,item[0],active?ACCENT:MUTED);
            cell.addView(glyph,new LinearLayout.LayoutParams(dp(20),dp(20)));
            TextView label=text(item[2],9,active?ACCENT:MUTED,active);label.setGravity(Gravity.CENTER);
            cell.addView(label);
            cell.setPadding(dp(1),dp(4),dp(1),dp(4));
            cell.setMinimumHeight(dp(52));
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
        else if(name.equals("history"))showHistory();
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
            dateBar.addView(previous,new LinearLayout.LayoutParams(dp(40),dp(38)));
            TextView current=text(new SimpleDateFormat("EEE, d MMM",new Locale("az")).format(day.getTime()),13,INK,true);
            current.setGravity(Gravity.CENTER);
            dateBar.addView(current,new LinearLayout.LayoutParams(0,dp(38),1));
            Button next=button("›");next.setContentDescription("Növbəti gün");
            next.setOnClickListener(v->{day.add(Calendar.DATE,1);navigate("matches");});
            dateBar.addView(next,new LinearLayout.LayoutParams(dp(40),dp(38)));
            Button today=button("Bu gün");
            today.setOnClickListener(v->{day=Calendar.getInstance(TimeZone.getTimeZone("Asia/Baku"));navigate("matches");});
            dateBar.addView(today,new LinearLayout.LayoutParams(dp(66),dp(38)));
            card(dateBar);
            LinearLayout chips=row();
            String[][] types={{"all","Hamısı"},{"live","● Canlı"},{"favorites","☆ Seçilmiş"}};
            for(String[] type:types){
                boolean selected=matchMode.equals(type[0]);
                Button tab=button(type[1]);
                tab.setTextColor(selected?BG:MUTED);
                tab.setBackground(shape(selected?ACCENT:RAISED,13));
                LinearLayout.LayoutParams w=new LinearLayout.LayoutParams(0,dp(38),1);
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
            controls.addView(label,new LinearLayout.LayoutParams(0,dp(38),1));
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
                conn.setConnectTimeout(6500);conn.setReadTimeout(14500);
                conn.setRequestProperty("Accept","application/json");
                conn.setRequestProperty("User-Agent","MATCHLABAZ-Native/0.9.58");
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
    private void playMatchTone(String category){
        if(!prefs.getBoolean("sound_enabled",true))return;
        if(!prefs.getBoolean("notif_"+category,true))return;
        if(prefs.getInt("alert_tone_"+category,1)==0)return;
        int volume=prefs.getInt("sound_volume",90);
        if(volume<=0)return;
        int frequency="goals".equals(category)?ToneGenerator.TONE_PROP_ACK:
            "final".equals(category)?ToneGenerator.TONE_PROP_NACK:ToneGenerator.TONE_PROP_PROMPT;
        try{
            ToneGenerator generator=new ToneGenerator(AudioManager.STREAM_MUSIC,Math.min(100,Math.max(1,volume)));
            generator.startTone(frequency,"goals".equals(category)?400:260);
            ui.postDelayed(generator::release,650);
        }catch(RuntimeException ignored){}
    }
    private void checkLiveScoreChanges(JSONObject response){
        // Do not notify for an old cached snapshot, partial feed or first server response.
        if(!response.optBoolean("available")||response.optBoolean("stale")||response.optBoolean("partial"))return;
        JSONArray rows=response.optJSONArray("items");
        if(rows==null)return;
        Map<String,String> current=new HashMap<>();
        for(int i=0;i<rows.length();i++){
            JSONObject match=rows.optJSONObject(i);if(match==null)continue;
            String id=match.optString("id","");
            String state=match.optString("state","");
            if(id.isEmpty()||match.optBoolean("stale")||"scheduled".equals(state))continue;
            if(!match.has("homeScore")||match.isNull("homeScore")||!match.has("awayScore")||match.isNull("awayScore"))continue;
            int h=match.optInt("homeScore",-1),a=match.optInt("awayScore",-1);
            if(h<0||a<0)continue;
            String snapshot=h+":"+a+":"+state;current.put(id,snapshot);
            String old=scoreBaseline.get(id);
            if(!hasScoreBaseline||old==null)continue;
            if(prefs.getBoolean("notif_favorites",false)&&!prefs.contains("fav_"+id))continue;
            String[] previous=old.split(":");
            if(previous.length!=3)continue;
            try{
                if(h>Integer.parseInt(previous[0])||a>Integer.parseInt(previous[1]))playMatchTone("goals");
                else if("final".equals(state)&&!"final".equals(previous[2]))playMatchTone("final");
            }catch(NumberFormatException ignored){}
        }
        if(current.isEmpty())return;
        scoreBaseline.clear();scoreBaseline.putAll(current);hasScoreBaseline=true;
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
            heading.setPadding(dp(10),dp(6),dp(8),dp(6));
            TextView title=single(name,12,INK,true);
            heading.addView(title,new LinearLayout.LayoutParams(0,dp(27),1));
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
            h.topMargin=dp(5);h.bottomMargin=dp(4);page.addView(heading,h);
            if(!collapsed){
                for(JSONObject m:group.getValue())matchRow(m,false);
            }
        }
    }
    private void loadMatches(boolean reset){
        int token=generation;
        String cacheKey="match_cache_"+league+"_"+date();
        if(reset){
            filters(false);
            String snapshot=prefs.getString(cacheKey,"");
            if(!snapshot.isEmpty()){
                try{
                    JSONObject cached=new JSONObject(snapshot);
                    JSONArray saved=cached.optJSONArray("items");
                    if(saved!=null){
                        for(int i=0;i<saved.length();i++){
                            JSONObject item=saved.optJSONObject(i);if(item!=null)item.put("stale",true);
                        }
                        cached.put("stale",true);cached.put("liveCount",0);cached.put("available",true);
                        cached.put("message","Saxlanmış matçlar göstərilir · yenilənir (CANLI DEYİL)");
                        renderLiveMatches(cached);
                    }
                }catch(Exception ignored){/* Corrupt snapshot: load from network. */}
            }else banner("Real matçlar yüklənir…",MUTED);
        }
        fetch("/api/live?league="+encode(league)+"&date="+date(),(json,error)->{
            if(token!=generation||!screen.equals("matches"))return;
            if(error!=null||json==null){
                status.setTextColor(RED);
                if(!prefs.getString(cacheKey,"").isEmpty()){
                    // Keep clearly stale local fixtures visible during Render cold starts.
                    banner("Server cavab vermir. Saxlanmış nəticələr CANLI DEYİL; yenidən yoxlanacaq.",RED);
                }else{
                    page.removeAllViews();filters(false);
                    info(networkMessage(error),true);retry("matches");
                }
                return;
            }
            status.setTextColor(json.optBoolean("available")?ACCENT:RED);
            if(json.optBoolean("available")&&!json.optBoolean("stale")&&json.toString().length()<130000)
                prefs.edit().putString(cacheKey,json.toString()).apply();
            checkLiveScoreChanges(json);
            renderLiveMatches(json);
        });
    }
    private void matchRow(JSONObject m,boolean saved){
        LinearLayout wrapper=column();
        wrapper.setBackground(shape(CARD,prefs.getBoolean("compact_cards",false)?8:12));
        wrapper.setPadding(dp(9),dp(7),dp(9),dp(7));
        String state=m.optString("state");
        boolean live=!saved&&!m.optBoolean("stale")&&"live".equals(state);
        LinearLayout top=row();
        TextView phase=single(stateLabel(m,saved),10,live?ACCENT:MUTED,true);
        top.addView(phase,new LinearLayout.LayoutParams(0,-2,1));
        String provider=m.optString("source");
        if(!provider.isEmpty())top.addView(single(provider,10,MUTED,false));
        wrapper.addView(top);
        gap(wrapper,4);
        LinearLayout body=row();
        LinearLayout teams=column();
        JSONObject home=m.optJSONObject("home"),away=m.optJSONObject("away");
        for(JSONObject team:new JSONObject[]{home,away}){
            LinearLayout teamRow=row();
            String name=val(team,"name");
            TeamBadge badge=new TeamBadge(this,name,team==null?"":team.optString("image"),24);
            LinearLayout.LayoutParams bp=new LinearLayout.LayoutParams(dp(24),dp(24));bp.rightMargin=dp(6);
            teamRow.addView(badge,bp);
            teamRow.addView(single(name,11,INK,true),new LinearLayout.LayoutParams(0,-2,1));
            teams.addView(teamRow);
            if(team==home)gap(teams,3);
        }
        body.addView(teams,new LinearLayout.LayoutParams(0,-2,1));
        LinearLayout scoreBlock=column();scoreBlock.setGravity(Gravity.CENTER);
        String score="scheduled".equals(state)?"– : –":val(m,"homeScore")+" : "+val(m,"awayScore");
        TextView result=single(score,15,live?ACCENT:INK,true);
        result.setGravity(Gravity.CENTER);
        scoreBlock.addView(result);
        String time=val(m,"minute");
        if(!"—".equals(time)&&live){
            TextView minute=text(time,10,ACCENT,true);minute.setGravity(Gravity.CENTER);scoreBlock.addView(minute);
        }
        body.addView(scoreBlock,new LinearLayout.LayoutParams(dp(64),-2));
        String id=m.optString("id");
        TextView star=fixed(prefs.contains("fav_"+id)?"★":"☆",21,ACCENT,false,30);
        star.setContentDescription("Seçilmişlərə əlavə et və ya çıxart");
        star.setMinHeight(dp(40));star.setClickable(true);
        star.setOnClickListener(v->{
            if(prefs.contains("fav_"+id))prefs.edit().remove("fav_"+id).apply();
            else prefs.edit().putString("fav_"+id,m.toString()).apply();
            star.setText(prefs.contains("fav_"+id)?"★":"☆");
        });
        body.addView(star);
        wrapper.addView(body);
        wrapper.setOnClickListener(v->{currentMatch=m;navigate("details");});
        wrapper.setContentDescription(val(home,"name")+" "+score+" "+val(away,"name")+", "+stateLabel(m,saved));
        LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(-1,-2);lp.bottomMargin=dp(5);
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
            profileFact("Baş məşqçi",p.optString("manager"));
            profileFact("Liqa",p.optString("league"));
            JSONObject updateStatus=p.optJSONObject("updateStatus");
            if(updateStatus!=null&&updateStatus.optBoolean("autoRefresh")){
                String checked=updateStatus.optString("checkedUtc","");
                info("Avtomatik mənbə yoxlaması aktivdir · Son yoxlama: "+
                    (checked.isEmpty()||"null".equals(checked)?"Hələ yoxlanılmayıb":checked)+
                    " · Yalnız baxılan profillər. Wikipedia / Wikidata.",false);
            }
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
    private void showFormationPicker(){
        LinearLayout list=column();
        list.setPadding(dp(8),dp(8),dp(8),dp(8));
        final AlertDialog dialog=new AlertDialog.Builder(this).setTitle("Taktiki düzülüş").setView(list)
            .setNegativeButton("Bağla",null).create();
        for(int i=0;i<formations.length;i++){
            final int selection=i;
            TextView choice=text((i==formation?"●  ":"○  ")+formations[i],15,i==formation?ACCENT:INK,i==formation);
            choice.setPadding(dp(22),0,dp(12),0);choice.setBackground(shape(RAISED,8));
            LinearLayout.LayoutParams item=new LinearLayout.LayoutParams(-1,dp(43));item.bottomMargin=dp(4);
            list.addView(choice,item);
            choice.setClickable(true);
            choice.setOnClickListener(v->{formation=selection;prefs.edit().putInt("tactic_formation",selection).apply();dialog.dismiss();navigate("tactics");});
        }
        dialog.show();
        if(dialog.getWindow()!=null)dialog.getWindow().setLayout(
            getResources().getDisplayMetrics().widthPixels-dp(56),-2);
    }
    private void showTactics(){
        section("TAKTİKA STUDİYASI PRO");
        LinearLayout modeBar=row();
        for(String mode:new String[]{"Hücum","Müdafiə","Standart"}){
            Button button=button(mode);button.setTextColor(mode.equals(prefs.getString("tactic_mode","Standart"))?ACCENT:INK);
            button.setOnClickListener(v->{prefs.edit().putString("tactic_mode",mode).apply();navigate("tactics");});
            modeBar.addView(button,new LinearLayout.LayoutParams(0,dp(45),1));
        }
        card(modeBar);
        // Active mode is indicated in the controls; keep the pitch above the fold.
        LinearLayout presets=row();
        TextView label=single("Düzülüş",12,MUTED,true);presets.addView(label,new LinearLayout.LayoutParams(0,dp(44),1));
        Button choose=button(formations[formation]+"   ⌄");
        choose.setOnClickListener(v->{
            showFormationPicker();
        });presets.addView(choose);
        card(presets);
        PitchView pitch=new PitchView(this,formations[formation]);
        LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(-1,dp(380));
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
        LinearLayout advanced=row();
        Button undo=button("↶ Geri al");
        undo.setOnClickListener(v->pitch.undo());advanced.addView(undo,new LinearLayout.LayoutParams(0,dp(44),1));
        Button mirror=button("⇆ Güzgü");
        mirror.setOnClickListener(v->pitch.mirror());advanced.addView(mirror,new LinearLayout.LayoutParams(0,dp(44),1));
        card(advanced);
        LinearLayout exports=row();
        Button animate=button("▶ Hərəkət animasiyası");
        animate.setOnClickListener(v->pitch.togglePlayback());
        exports.addView(animate,new LinearLayout.LayoutParams(0,dp(46),1));
        Button png=button("▣ PNG saxla");
        png.setOnClickListener(v->{
            pendingExportPitch=pitch;
            Intent create=new Intent(Intent.ACTION_CREATE_DOCUMENT);
            create.addCategory(Intent.CATEGORY_OPENABLE);
            create.setType("image/png");
            create.putExtra(Intent.EXTRA_TITLE,"MATCHLAB_AZ_Taktika_"+formations[formation].replace("-","_")+".png");
            startActivityForResult(create,EXPORT_TACTIC_PNG);
        });
        exports.addView(png,new LinearLayout.LayoutParams(0,dp(46),1));
        card(exports);
        gap(page,9);
        section("Ehtiyat oyunçular və əvəzetmələr");
        for(int i=1;i<=7;i++){
            final int slot=i;
            String key="tactic_sub_"+formation+"_"+slot;
            LinearLayout line=row();
            TextView sub=text(slot+". "+prefs.getString(key,"Ehtiyat oyunçu"),13,INK,false);
            line.addView(sub,new LinearLayout.LayoutParams(0,dp(42),1));
            Button edit=button("Dəyiş");
            edit.setOnClickListener(v->{
                EditText input=new EditText(this);input.setSingleLine(true);input.setText(prefs.getString(key,""));
                new AlertDialog.Builder(this).setTitle("Ehtiyat oyunçu "+slot).setView(input)
                    .setNegativeButton("Ləğv et",null).setPositiveButton("Saxla",(d,w)->{
                        prefs.edit().putString(key,input.getText().toString().trim()).apply();navigate("tactics");
                    }).show();
            });
            line.addView(edit);card(line);
        }
        Button export=button("Taktika planını və ehtiyatları paylaş");
        export.setOnClickListener(v->{
            StringBuilder sb=new StringBuilder(pitch.exportText()).append("\\nRejim: ").append(prefs.getString("tactic_mode","Standart")).append("\\nEhtiyatlar:\\n");
            for(int i=1;i<=7;i++)sb.append(i).append(". ").append(prefs.getString("tactic_sub_"+formation+"_"+i,"—")).append("\\n");
            Intent shareIntent=new Intent(Intent.ACTION_SEND);shareIntent.setType("text/plain");
            shareIntent.putExtra(Intent.EXTRA_TEXT,sb.toString());
            startActivity(Intent.createChooser(shareIntent,"Taktika planını paylaş"));
        });card(export);
        gap(page,9);
        info("Oxlar alətini aktivləşdirib meydançada başlanğıc və bitiş nöqtəsinə toxun. Oxlar saxlanılır.",false);
        info("Oyunçunu sürüşdürərək mövqeyini dəyiş. Ad və nömrəni dəyişmək üçün oyunçuya qısa toxun. Dəyişikliklər avtomatik saxlanılır.",false);
        info("Bu plan sənin öz taktiki layihəndir. Real matç heyəti və təsdiqlənmiş formasiya kimi təqdim edilmir.",false);
    }
    private void showSettings(){
        section("MATCHLAB AZ Native 0.9.58");
        section("Görünüş, şəbəkə və yaddaş");
        Switch refreshToggle=new Switch(this);
        refreshToggle.setText("Matçları avtomatik yenilə");
        refreshToggle.setTextColor(INK);
        refreshToggle.setChecked(prefs.getBoolean("auto_refresh",true));
        refreshToggle.setOnCheckedChangeListener((v,on)->prefs.edit().putBoolean("auto_refresh",on).apply());
        card(refreshToggle);
        LinearLayout refreshRow=row();
        refreshRow.addView(text("Yenilənmə intervalı",12,INK,true),new LinearLayout.LayoutParams(0,dp(43),1));
        String[] intervals={"15 saniyə","30 saniyə","45 saniyə","60 saniyə"};
        final int[] values={15,30,45,60};
        int index=1;for(int i=0;i<values.length;i++)if(values[i]==prefs.getInt("refresh_interval",30))index=i;
        refreshRow.addView(spinner(intervals,index,n->prefs.edit().putInt("refresh_interval",values[n]).apply()));
        card(refreshRow);
        Switch compact=new Switch(this);compact.setText("Yığcam matç kartları");
        compact.setTextColor(INK);compact.setChecked(prefs.getBoolean("compact_cards",false));
        compact.setOnCheckedChangeListener((v,on)->prefs.edit().putBoolean("compact_cards",on).apply());
        card(compact);
        Button clearHistory=button("Arxiv ve matç keşi təmizlə");
        clearHistory.setOnClickListener(v->new AlertDialog.Builder(this).setTitle("Yerli keş silinsin?")
            .setMessage("Tarix arxivi və matç keşi silinir. Sevimlilər, taktika və tənzimləmələr qalır.")
            .setNegativeButton("Ləğv et",null).setPositiveButton("Sil",(d,w)->{
                SharedPreferences.Editor editor=prefs.edit();
                for(String key:prefs.getAll().keySet())
                    if(key.startsWith("history_bundle_")||key.startsWith("match_cache_"))editor.remove(key);
                editor.apply();historyBundles.clear();
                Toast.makeText(this,"Yerli keş təmizləndi",Toast.LENGTH_SHORT).show();
            }).show());card(clearHistory);
                section("Bildiriş və səs idarəetməsi");
        section("Səs səviyyəsi");
        SeekBar volume=new SeekBar(this);
        volume.setMax(100);volume.setProgress(prefs.getInt("sound_volume",90));
        volume.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener(){
            public void onProgressChanged(SeekBar b,int value,boolean user){if(user)prefs.edit().putInt("sound_volume",value).apply();}
            public void onStartTrackingTouch(SeekBar b){}
            public void onStopTrackingTouch(SeekBar b){}
        });
        card(volume);
        for(String[] setting:new String[][]{{"notif_goals","Qol bildirişləri"},{"notif_kickoff","Matç başlanğıcı"},{"notif_halftime","Fasilə"},{"notif_final","Matçın bitməsi"},{"notif_cards","Qırmızı kart"},{"notif_yellow_cards","Sarı kart"},{"notif_assists","Assist"},{"notif_penalties","Penalti"},{"notif_lineups","Heyətlər açıqlananda"},{"notif_corners","Künc zərbəsi"},{"notif_favorites","Yalnız seçilmiş matçlar"},{"sound_enabled","Tətbiqdaxili səs"}}){
            Switch toggle=new Switch(this);toggle.setText(setting[1]);toggle.setTextSize(13);toggle.setTextColor(INK);
            toggle.setChecked(prefs.getBoolean(setting[0],false));toggle.setPadding(dp(9),dp(9),dp(9),dp(9));
            toggle.setOnCheckedChangeListener((view,checked)->prefs.edit().putBoolean(setting[0],checked).apply());card(toggle);
        }
        section("Hər hadisə üçün səs seçimi");
        String[][] alerts={
            {"goals","Qol"},{"assists","Assist"},{"penalties","Penalti"},
            {"cards","Qırmızı kart"},{"yellow_cards","Sarı kart"},{"corners","Künc zərbəsi"},
            {"lineups","Heyət açıqlanması"},{"final","Matç bitdi"},{"kickoff","Matç başladı"}
        };
        String[] tones={"Səssiz","Qısa siqnal","Təsdiq","Xəbərdarlıq","İkili siqnal"};
        for(String[] alert:alerts){
            final String key=alert[0];
            LinearLayout control=column();control.setPadding(dp(10),dp(10),dp(10),dp(10));
            control.addView(text(alert[1],14,INK,true));
            LinearLayout buttons=row();
            Button sound=button("Səs: "+tones[Math.max(0,Math.min(4,prefs.getInt("alert_tone_"+key,1)))]);
            sound.setOnClickListener(v->new AlertDialog.Builder(this).setTitle(alert[1]+" səsi")
                .setSingleChoiceItems(tones,prefs.getInt("alert_tone_"+key,1),(dialog,selected)->{
                    prefs.edit().putInt("alert_tone_"+key,selected).apply();
                    sound.setText("Səs: "+tones[selected]);dialog.dismiss();
                }).setNegativeButton("Bağla",null).show());
            buttons.addView(sound,new LinearLayout.LayoutParams(0,dp(45),2));
            control.addView(buttons);
            Button preview=button("♪  Sına");
            preview.setOnClickListener(v->{
                int selected=prefs.getInt("alert_tone_"+key,1);
                if(selected>0){
                    int tone=selected==1?ToneGenerator.TONE_PROP_BEEP:selected==2?ToneGenerator.TONE_PROP_ACK:selected==3?ToneGenerator.TONE_PROP_NACK:ToneGenerator.TONE_PROP_PROMPT;
                    ToneGenerator generator=new ToneGenerator(AudioManager.STREAM_MUSIC,prefs.getInt("sound_volume",90));
                    generator.startTone(tone,200);ui.postDelayed(generator::release,320);
                }
            });control.addView(preview);
            card(control);
        }
        info("Bu seçimlər yerli yaddaşa yazılır. Qol və final səsləri yalnız proqram açıq olarkən yeni, təsdiqlənmiş hesab dəyişikliyi görüldükdə işləyir. Push bildirişləri aktiv deyil.",false);
        info("Ekranlar yalnız Android Java komponentlərindən qurulub. Veb səhifə göstərilmir.",false);
        info("Canlı matçlar və profillər HTTPS JSON API-dən gəlir. Mənbələrdə boşluqlar ola bilər.",false);
        Button statusButton=button("Server vəziyyətini yoxla");
        statusButton.setOnClickListener(v->{
            long started=android.os.SystemClock.elapsedRealtime();
            fetch("/api/status",(json,error)->{
                long latency=android.os.SystemClock.elapsedRealtime()-started;
                if(!"settings".equals(screen))return;
                if(error!=null){info(networkMessage(error)+" · "+latency+" ms",true);return;}
                if(json==null){info("Server boş cavab verdi · "+latency+" ms",true);return;}
                info("Versiya: "+json.optString("version")+" · Arxiv: "+(json.optJSONObject("world")!=null?json.optJSONObject("world").optString("total","—"):"—")+
                    " · Cavab müddəti: "+latency+" ms",false);
            });
        });card(statusButton);
    }

    private String historyKey(){return "history_bundle_"+historyLeague+"_"+historySeason;}
    private JSONObject cachedHistory(){
        String key=historyKey();
        if(historyBundles.containsKey(key))return historyBundles.get(key);
        try{
            String saved=prefs.getString(key,"");
            if(!saved.isEmpty()){
                JSONObject result=new JSONObject(saved);
                if(result.optBoolean("available")&&result.optBoolean("bundle")){
                    historyBundles.put(key,result);return result;
                }
            }
        }catch(Exception ignored){}
        return null;
    }
    private void showHistory(){
        page.removeAllViews();
        section("FOOTBALL HERITAGE  ·  CC0 ARXİV");
        info("Arxiv canlı DEYİL. İlk dəfə mövsüm yüklənir, sonra komanda axtarışı internet sorğusu etmədən işləyir.",false);
        final String[] ids={"eng.1","esp.1","ger.1","ita.1","fra.1","tur.1","por.1","ned.1","sco.1","eng.2","bel.1"};
        final String[] names={"Premier League","La Liga","Bundesliga","Serie A","Ligue 1","Süper Lig","Primeira Liga","Eredivisie","Scottish Premiership","Championship","Belgian Pro League"};
        LinearLayout tools=column();
        Spinner leaguesPicker=spinner(names,Math.max(0,Arrays.asList(ids).indexOf(historyLeague)),n->{historyLeague=ids[n];historyOffset=0;showHistory();});
        tools.addView(leaguesPicker);
        String[] seasons=new String[17];
        for(int i=0;i<seasons.length;i++){int y=2026-i;seasons[i]=y+"-"+String.format(Locale.US,"%02d",(y+1)%100);}
        Spinner seasonPicker=spinner(seasons,Math.max(0,Arrays.asList(seasons).indexOf(historySeason)),n->{historySeason=seasons[n];historyOffset=0;showHistory();});
        tools.addView(seasonPicker);
        EditText club=new EditText(this);club.setSingleLine(true);club.setHint("Komanda adına görə axtar");
        club.setText(historyTeam);club.setTextColor(INK);club.setHintTextColor(MUTED);
        tools.addView(club);
        Button load=button("⌕  Komandanı tap");
        load.setOnClickListener(v->{historyTeam=club.getText().toString().trim();historyOffset=0;showHistory();});
        tools.addView(load);card(tools);
        int token=generation;
        String key=historyKey();
        JSONObject old=cachedHistory();
        if(old!=null)renderHistoricalRows(old,true);
        boolean recent=old!=null&&System.currentTimeMillis()-prefs.getLong(key+"_checked",0)<86400000L;
        if(recent)return;
        if(old==null)info("Mövsüm arxivi mənbədən alınır…",false);
        fetch("/api/history-bundle?league="+encode(historyLeague)+"&season="+encode(historySeason),(json,error)->{
            if(token!=generation||!"history".equals(screen)||!key.equals(historyKey()))return;
            if(error!=null||json==null||!json.optBoolean("available")){
                if(old==null){
                    // The live Render server can lag behind the new full-season endpoint.
                    // Use its earlier paged endpoint rather than breaking the archive.
                    fetch("/api/history?league="+encode(historyLeague)+"&season="+encode(historySeason)+
                        "&limit=60&offset="+historyOffset+"&team="+encode(historyTeam),(legacy,legacyError)->{
                        if(token!=generation||!"history".equals(screen)||!key.equals(historyKey()))return;
                        if(legacyError!=null||legacy==null||!legacy.optBoolean("available")){
                            info(legacyError!=null?networkMessage(legacyError):legacy==null?"Arxiv cavab vermədi":legacy.optString("message"),true);return;
                        }
                        info("Uyğunluq rejimi · server tam mövsüm yeniləməsini hələ dəstəkləmir.",false);
                        renderHistoricalRows(legacy,false,true);
                    });
                }
                return;
            }
            if(json.optBoolean("complete")&&json.toString().length()<1_500_000){
                historyBundles.put(key,json);
                prefs.edit().putString(key,json.toString()).putLong(key+"_checked",System.currentTimeMillis()).apply();
            }
            // Keep the current search field intact when stale results were already displayed.
            if(old==null)renderHistoricalRows(json,false);
        });
    }
    private void renderHistoricalRows(JSONObject json,boolean cached){renderHistoricalRows(json,cached,false);}
    private void renderHistoricalRows(JSONObject json,boolean cached,boolean legacy){
        section(json.optString("leagueName",historyLeague)+" · "+historySeason+(cached?" · YERLİ KEŞ":" · CC0"));
        JSONArray rows=json.optJSONArray("items");
        if(rows==null){info("Tarixi məlumat yoxdur.",false);return;}
        ArrayList<JSONObject> filtered=new ArrayList<>();
        String term=historyTeam.toLowerCase(Locale.ROOT).trim();
        for(int i=0;i<rows.length();i++){
            JSONObject game=rows.optJSONObject(i);
            if(game==null)continue;
            if(!term.isEmpty()&&!game.optString("home").toLowerCase(Locale.ROOT).contains(term)
                &&!game.optString("away").toLowerCase(Locale.ROOT).contains(term))continue;
            filtered.add(game);
        }
        info(legacy
            ? filtered.size()+" bu səhifədə uyğun oyun · server axtarışı · TAM MÖVSÜM DEYİL"
            : filtered.size()+" uyğun oyun · tarixi, canlı deyil",false);
        if(!historyTeam.trim().isEmpty()){
            HistoryTeamForm form=new HistoryTeamForm(historyTeam);
            for(JSONObject game:filtered){
                form.add(game.optString("home"),game.optString("away"),
                    game.optInt("homeScore",-1),game.optInt("awayScore",-1),
                    game.optBoolean("resultRecorded"),game.optString("date"));
            }
            if(form.ambiguous()){
                info("Axtarış bir neçə kluba uyğun gəlir. Dəqiq forma üçün klubun tam adını yaz.",true);
            }else if(form.played()>0){
                boolean complete=!legacy&&json.optBoolean("complete")&&json.optBoolean("bundle");
                section(complete?"KOMANDA FORMASI · TAM MÖVSÜM":"KOMANDA FORMASI · BU SƏHİFƏ (TAM DEYİL)");
                info(form.totals()+"\n"+form.goalsAndForm()+"\n"+
                    form.homeAway()+"\n"+form.efficiency(),false);
            }
        }
        int begin=legacy?0:historyOffset;
        int end=Math.min(begin+60,filtered.size());
        for(int i=begin;i<end;i++){
            JSONObject game=filtered.get(i);
            LinearLayout item=column();item.setPadding(dp(12),dp(12),dp(12),dp(12));
            item.setBackground(shape(CARD,12));
            item.addView(text(game.optString("round")+" · "+game.optString("date")+"  "+game.optString("time"),10,MUTED,false));
            String score=game.optBoolean("resultRecorded")?game.optString("homeScore")+" : "+game.optString("awayScore"):"— : —";
            item.addView(text(game.optString("home")+"   "+score+"   "+game.optString("away"),13,INK,true));
            LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(-1,-2);p.bottomMargin=dp(7);page.addView(item,p);
        }
        boolean hasMore=legacy?!json.isNull("nextOffset")&&json.optInt("nextOffset",-1)>historyOffset:end<filtered.size();
        if(hasMore){
            Button more=button("Daha 60 oyun");
            more.setOnClickListener(v->{
                historyOffset=legacy?json.optInt("nextOffset",historyOffset+60):end;
                showHistory();
            });card(more);
        }
        info("Mənbə: OpenFootball CC0. Arxiv yerli yaddaşa köçürülür; gündə bir dəfə yenilənir.",false);
    }
    private void showMenu(View anchor){
        PopupMenu popup=new PopupMenu(this,anchor);
        popup.getMenu().add(0,1,0,"Canlı matçlar");
        popup.getMenu().add(0,2,1,"Axtarış");
        popup.getMenu().add(0,3,2,"Seçilmişlər");
        popup.getMenu().add(0,4,3,"Tənzimləmələr və server");
        popup.getMenu().add(0,5,4,"Android tətbiq məlumatları");
        popup.getMenu().add(0,6,5,"◷ Tarixi futbol arxivi");
        popup.setOnMenuItemClickListener(item->{
            switch(item.getItemId()){
                case 1:navigate("matches");return true;
                case 2:navigate("search");return true;
                case 3:navigate("favorites");return true;
                case 4:navigate("settings");return true;
                case 6:navigate("history");return true;
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
