using System;
using System.Collections.Generic;
using System.Drawing;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Text.Json;
using System.Threading.Tasks;
using System.Windows.Forms;

namespace MATCHLABAZ;

internal static class Program
{
    [STAThread]
    private static void Main()
    {
        ApplicationConfiguration.Initialize();
        using (var intro = new SplashForm()) intro.ShowDialog();
        Application.Run(new MatchlabForm());
    }
}
public sealed class MatchlabForm : Form
{
    private static readonly Color Bg = Color.FromArgb(9, 18, 30);
    private static readonly Color Sidebar = Color.FromArgb(13, 27, 43);
    private static readonly Color Card = Color.FromArgb(21, 38, 55);
    private static readonly Color Raised = Color.FromArgb(29, 49, 66);
    private static readonly Color Ink = Color.FromArgb(239, 246, 252);
    private static readonly Color Muted = Color.FromArgb(157, 176, 191);
    private static readonly Color Accent = Color.FromArgb(181, 245, 104);
    private static readonly Color Red = Color.FromArgb(245, 117, 122);
    private static readonly HttpClient Api = new()
    {
        BaseAddress = new Uri("https://matchlab-az-online.onrender.com"),
        Timeout = TimeSpan.FromSeconds(17)
    };
    // Download only provider-supplied HTTPS raster logos; never guess identities from names.
    private static readonly System.Collections.Concurrent.ConcurrentDictionary<string,Image> BadgeCache = new();
    private static readonly System.Threading.SemaphoreSlim ImageSlots = new(4);
    private async Task AttachBadgeAsync(PictureBox badge,string url){
        if(string.IsNullOrEmpty(url)||url.Length>650||!Uri.TryCreate(url,UriKind.Absolute,out var uri)||uri.Scheme!="https")return;
        try{
            if(BadgeCache.TryGetValue(url,out var cached)){if(!badge.IsDisposed)badge.Image=cached;return;}
            await ImageSlots.WaitAsync();
            try{
                if(!BadgeCache.TryGetValue(url,out cached)){
                    using var response=await Api.GetAsync(uri,HttpCompletionOption.ResponseHeadersRead);
                    if(!response.IsSuccessStatusCode)return;
                    var mime=response.Content.Headers.ContentType?.MediaType??"";
                    if(!new[]{"image/png","image/jpeg","image/webp","image/gif"}.Contains(mime))return;
                    if(response.Content.Headers.ContentLength.GetValueOrDefault()>650000)return;
                    using var stream=await response.Content.ReadAsStreamAsync();
                    using var buffer=new MemoryStream();
                    byte[] bytes=new byte[8192];
                    while(true){
                        int count=await stream.ReadAsync(bytes.AsMemory(0,bytes.Length));
                        if(count==0)break;
                        if(buffer.Length+count>650000)return;
                        buffer.Write(bytes,0,count);
                    }
                    buffer.Position=0;
                    using var raw=Image.FromStream(buffer);
                    cached=new Bitmap(raw);
                    if(BadgeCache.Count<180)BadgeCache.TryAdd(url,cached);
                }
            }finally{ImageSlots.Release();}
            if(badge.IsDisposed)return;
            if(badge.InvokeRequired)badge.BeginInvoke(new Action(()=>{if(!badge.IsDisposed)badge.Image=cached;}));
            else badge.Image=cached;
        }catch(Exception){/* Unsupported logo -> neutral fallback, never block scores. */}
    }
    private readonly string[] leagues = {"all","aze.1","eng.1","esp.1","ger.1","ita.1","fra.1","uefa.champions","uefa.europa","uefa.europa.conf","tur.1","por.1","ned.1","sco.1","bel.1","usa.1","ksa.1","eng.2","arg.1","bra.1","jpn.1","mex.1"};
    private readonly string[] leagueNames = {"Bütün liqalar","Azərbaycan Premyer Liqası","Premier League","La Liga","Bundesliga","Serie A","Ligue 1","Champions League","Europa League","Konfrans Liqası","Süper Lig","Primeira Liga","Eredivisie","Scottish Premiership","Belgian Pro League","MLS","Saudi Pro League","Championship","Argentina Primera","Brasileirão","J1 League","Liga MX"};
    private readonly Dictionary<string, string> favoriteSnapshots = new();
    private readonly string savePath = Path.Combine(
        Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
        "MATCHLAB_AZ", "favorites.json");
    private readonly System.Windows.Forms.Timer refreshTimer = new() { Interval = 30000 };
    private readonly FlowLayoutPanel content = new() { Dock=DockStyle.Fill, AutoScroll=true, WrapContents=false, FlowDirection=FlowDirection.TopDown, BackColor=Bg, Padding=new Padding(14,10,14,10) };
    private readonly Label title = new() { Dock=DockStyle.Left, AutoSize=false, Width=540, Font=new Font("Segoe UI Semibold",19f), ForeColor=Ink, TextAlign=ContentAlignment.MiddleLeft };
    private readonly Label connection = new() { Dock=DockStyle.Right, AutoSize=false, Width=200, ForeColor=Muted, TextAlign=ContentAlignment.MiddleCenter, Text="●  Mənbə yoxlanılır" };
    private readonly Panel nav = new() { Dock=DockStyle.Fill, BackColor=Sidebar };
    private readonly List<Button> navButtons = new();
    private string page="matches";
    private string matchFilter="all";
    private readonly HashSet<string> collapsedLeagues=new();
    private string league="all";
    private DateTime selectedDate=DateTime.UtcNow.AddHours(4).Date;
    private string selectedKind="all";
    private string query="";
    private int viewVersion;
    private JsonElement openedMatch;
    private bool hasOpenedMatch;
    private int formation=0;
    private readonly string[] formations={"4-3-3","4-2-3-1","4-4-2","3-5-2","3-4-3","4-1-4-1","5-3-2","4-2-2-2"};
    private List<JsonElement> latestMatches = new();
    private string MatchesCacheFile => Path.Combine(
        Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
        "MATCHLAB_AZ","matches_"+league.Replace('.','_')+"_"+BakuDate(selectedDate)+".json");
    private void ShowCachedMatches(){
        try{
            if(!File.Exists(MatchesCacheFile))return;
            using var document=JsonDocument.Parse(File.ReadAllText(MatchesCacheFile));
            var rows=Array(document.RootElement,"items").Select(x=>x.Clone()).ToList();
            if(rows.Count==0)return;
            latestMatches=rows;
            Heading("Son saxlanmış nəticələr · server yenilənir · CANLI DEYİL");
            string group="";
            foreach(var m in rows){
                string next=Val(m,"leagueName",Val(m,"league","Digər"));
                if(next!=group){Heading(next);group=next;}
                MatchRow(m,true);
            }
        }catch(Exception){/* Unsupported or corrupted snapshot: network will load. */}
    }
    private void StoreMatches(JsonElement data){
        if(!Yes(data,"available")||Yes(data,"stale"))return;
        var raw=data.GetRawText();
        if(raw.Length>120000)return;
        try{
            Directory.CreateDirectory(Path.GetDirectoryName(MatchesCacheFile)!);
            File.WriteAllText(MatchesCacheFile,raw);
        }catch(IOException){/* Network result remains available. */}
    }

    private readonly string optionsPath = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "MATCHLAB_AZ", "options.json");
    private readonly Dictionary<string, string> options = new();
    private readonly string[] alertIds={"goals","assists","penalties","cards","yellow_cards","corners","lineups","final","kickoff"};
    private readonly string[] alertNames={"Qol","Assist","Penalti","Qırmızı kart","Sarı kart","Künc zərbəsi","Heyət açıqlanması","Matç bitdi","Matç başladı"};

    public MatchlabForm()
    {
        Text="MATCHLAB AZ — Futbol mərkəzi";
        try { Icon = Icon.ExtractAssociatedIcon(Application.ExecutablePath); } catch { /* icon optional in IDE */ }
        StartPosition=FormStartPosition.CenterScreen;
        MinimumSize=new Size(940,640);
        Size=new Size(1280,830);
        BackColor=Bg;
        ForeColor=Ink;
        Font=new Font("Segoe UI",10);
        try {
            if (File.Exists(savePath)) {
                var raw = JsonSerializer.Deserialize<Dictionary<string,string>>(File.ReadAllText(savePath));
                if(raw!=null)foreach(var x in raw) favoriteSnapshots[x.Key]=x.Value;
            }
        }catch {}
        try{
            if(File.Exists(optionsPath)){
                var saved=JsonSerializer.Deserialize<Dictionary<string,string>>(File.ReadAllText(optionsPath));
                if(saved!=null)foreach(var item in saved)options[item.Key]=item.Value;
            }
            if(int.TryParse(Option("tactic_formation","0"),out int selected)&&selected>=0&&selected<formations.Length)formation=selected;
        }catch{}
        var shell=new TableLayoutPanel {Dock=DockStyle.Fill, ColumnCount=2, RowCount=1, Margin=Padding.Empty, Padding=Padding.Empty, BackColor=Bg};
        shell.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute,222));
        shell.ColumnStyles.Add(new ColumnStyle(SizeType.Percent,100));
        Controls.Add(shell);
        shell.Controls.Add(nav,0,0);
        var right=new TableLayoutPanel {Dock=DockStyle.Fill, ColumnCount=1, RowCount=2, Padding=Padding.Empty};
        right.RowStyles.Add(new RowStyle(SizeType.Absolute,88));
        right.RowStyles.Add(new RowStyle(SizeType.Percent,100));
        shell.Controls.Add(right,1,0);
        var top=new Panel {Dock=DockStyle.Fill,BackColor=Bg,Padding=new Padding(25,8,22,5)};
        top.Paint+=(_,e)=>{using var edge=new Pen(Color.FromArgb(36,70,79));e.Graphics.DrawLine(edge,0,top.Height-1,top.Width,top.Height-1);};
        right.Controls.Add(top,0,0);
        right.Controls.Add(content,0,1);
        title.Text="Canlı matçlar";
        top.Controls.Add(title);
        var refresh=NewButton("↻  Yenilə", Raised,Ink,100);
        refresh.Dock=DockStyle.Right;
        refresh.Margin=new Padding(3,12,3,10);
        refresh.Click+=(_,_)=>Render();
        top.Controls.Add(refresh);
        top.Controls.Add(connection);
        BuildNav();
        content.SizeChanged+=(_,_)=>{
            foreach(Control c in content.Controls)
                if(c is Panel || c is FlowLayoutPanel) c.Width=Math.Max(380,content.ClientSize.Width-36);
        };
        refreshTimer.Tick+=(_,_)=>{ if(page=="matches"&&WindowState!=FormWindowState.Minimized) _=ReloadMatches(false); };
        refreshTimer.Start();
        Render();
    }

    private static Button NewButton(string label,Color back,Color fore,int width=130) {
        var b=new Button{Text=label,BackColor=back,ForeColor=fore,Width=width,Height=43,FlatStyle=FlatStyle.Flat,Cursor=Cursors.Hand,Font=new Font("Segoe UI Semibold",10)};
        b.FlatAppearance.BorderSize=0;
        return b;
    }
    private static Label Txt(string value,int size=11,bool bold=false,Color? color=null) {
        return new Label {Text=value,ForeColor=color??Ink,Font=new Font(bold?"Segoe UI Semibold":"Segoe UI",size),AutoEllipsis=true,TextAlign=ContentAlignment.MiddleLeft};
    }
    private void BuildNav() {
        var mark=new PictureBox{Left=20,Top=25,Width=48,Height=48,SizeMode=PictureBoxSizeMode.Zoom};
        var markImage=new Bitmap(96,96);
        using(var g=Graphics.FromImage(markImage))BrandArtwork.Draw(g,new RectangleF(0,0,96,96));
        mark.Image=markImage;nav.Controls.Add(mark);
        var brand=Txt("MATCHLAB AZ",13,true,Accent);
        brand.SetBounds(80,24,140,30);nav.Controls.Add(brand);
        var sub=Txt("FUTBOL MƏRKƏZİ",8,false,Muted);
        sub.SetBounds(80,53,138,19);nav.Controls.Add(sub);
        var build=Txt("NATIVE · 0.9.54",8,false,Muted);
        build.SetBounds(20,91,190,22);nav.Controls.Add(build);
        var items=new(string key,string label)[]{
            ("matches","⚽  Matçlar"),("standings","▤   Cədvəl"),("search","⌕   Axtarış"),
            ("tactics","▦   Taktika"),("favorites","☆   Seçilmişlər"),("settings","⚙   Tənzimləmələr")
        };
        int y=149;
        foreach(var item in items){
            var b=NewButton(item.label,Sidebar,Ink,190);
            b.SetBounds(15,y,190,47);
            b.FlatAppearance.MouseOverBackColor=Raised;
            b.TextAlign=ContentAlignment.MiddleLeft;
            b.Click+=(_,_)=>{page=item.key;Render();};
            nav.Controls.Add(b);
            navButtons.Add(b);
            b.Tag=item.key;
            y+=55;
        }
        var note=Txt("Nəticələr real mənbələrdən\nalınır. Tam canlılıq zəmanəti yoxdur.",9,false,Muted);
        note.SetBounds(20,Math.Max(490,nav.Height-132),185,80);
        nav.Resize+=(_,_)=>note.Top=Math.Max(490,nav.Height-132);
        nav.Controls.Add(note);
    }
    private static JsonElement Prop(JsonElement o,string k){
        if(o.ValueKind==JsonValueKind.Object&&o.TryGetProperty(k,out var v))return v;
        return default;
    }
    private static string Val(JsonElement o,string k,string fallback=""){
        var v=Prop(o,k);
        return v.ValueKind switch {JsonValueKind.String=>v.GetString()??fallback,JsonValueKind.Number=>v.ToString(),JsonValueKind.True=>"true",JsonValueKind.False=>"false",_=>fallback};
    }
    private static bool Yes(JsonElement o,string k)=>Prop(o,k).ValueKind==JsonValueKind.True;
    private static IEnumerable<JsonElement> Array(JsonElement o,string k){
        var a=Prop(o,k);
        return a.ValueKind==JsonValueKind.Array?a.EnumerateArray():Enumerable.Empty<JsonElement>();
    }
    private async Task<JsonElement> Get(string endpoint) {
        using var response=await Api.GetAsync(endpoint);
        response.EnsureSuccessStatusCode();
        using var stream=await response.Content.ReadAsStreamAsync();
        using var json=await JsonDocument.ParseAsync(stream);
        return json.RootElement.Clone();
    }
    private void SetConnection(bool ok){
        connection.ForeColor=ok?Accent:Red;
        connection.Text=ok?"●  Mənbə aktiv":"●  Bağlantı yoxdur";
    }
    private void ClearPage(){
        viewVersion++;
        content.SuspendLayout();
        content.Controls.Clear();
        content.ResumeLayout();
        foreach(var b in navButtons){
            var active=(string?)b.Tag==page;
            b.BackColor=active?Color.FromArgb(28,62,53):Sidebar;
            b.ForeColor=active?Accent:Ink;
        }
        title.Text=page switch {
            "matches"=>"Canlı matçlar","standings"=>"Turnir cədvəli","search"=>"Futbol arxivi",
            "tactics"=>"Taktika studiyası","favorites"=>"Seçilmiş matçlar","settings"=>"Tənzimləmələr",
            "details"=>"Matç mərkəzi","profile"=>"Futbol profili",_=>"MATCHLAB AZ"
        };
    }
    private Panel CardPanel(int height=80) {
        var p=new RoundedCard {BackColor=Card,Width=Math.Max(400,content.ClientSize.Width-36),Height=height,Margin=new Padding(0,0,0,9),Padding=new Padding(12)};
        content.Controls.Add(p);
        return p;
    }
    private void Message(string message,bool warning=false){
        var p=CardPanel(70);
        var l=Txt(message,11,false,warning?Red:Muted);
        l.Dock=DockStyle.Fill;l.Padding=new Padding(9);
        p.Controls.Add(l);
    }
    private void Heading(string text) {
        var row=CardPanel(40);
        row.BackColor=Bg;
        row.Padding=Padding.Empty;
        var l=Txt(text,12,true,Accent);l.Dock=DockStyle.Fill;row.Controls.Add(l);
    }
    private void DashboardHero(string? caption=null){
        var hero=CardPanel(165);
        hero.BackColor=Color.FromArgb(17,43,48);
        var eyebrow=Txt("MATCHLAB  /  MATÇ MƏRKƏZİ",9,true,Accent);
        eyebrow.SetBounds(18,11,370,21);hero.Controls.Add(eyebrow);
        var h=Txt("Bu gün futbol",20,true,Ink);
        h.SetBounds(18,34,440,35);hero.Controls.Add(h);
        var detail=Txt(caption??"Real nəticələr, təsdiqlənmiş heyətlər və klub statistikası — bir məkanda.",10,false,Muted);
        detail.SetBounds(19,75,570,27);hero.Controls.Add(detail);
        var quick=new (string label,string target)[]{("⌕  Axtarış","search"),("▦  Taktika","tactics"),("▤  Cədvəl","standings")};
        var shortcutButtons=new List<Button>();
        for(int i=0;i<quick.Length;i++){
            var target=quick[i].target;
            var action=NewButton(quick[i].label,Raised,Ink,105);
            action.Click+=(_,_)=>{page=target;Render();};
            hero.Controls.Add(action);shortcutButtons.Add(action);
        }
        void LayoutHero(){
            bool narrow=hero.Width<920;
            int x=narrow?18:hero.Width-365;
            int y=narrow?114:53;
            for(int index=0;index<shortcutButtons.Count;index++)
                shortcutButtons[index].SetBounds(x+index*115,y,105,36);
            detail.Width=narrow?hero.Width-36:hero.Width-435;
        }
        hero.SizeChanged+=(_,_)=>LayoutHero();
        LayoutHero();
    }
    private void LoadingState(string message){
        var panel=CardPanel(83);
        var dot=Txt("◌",19,true,Accent);dot.SetBounds(15,10,40,50);panel.Controls.Add(dot);
        var label=Txt(message,11,true,Ink);label.SetBounds(60,9,640,27);panel.Controls.Add(label);
        var note=Txt("Pulsuz server ilk açılışda gec oyana bilər. Keş varsa, oyunlar yuxarıda göstərilir.",9,false,Muted);
        note.SetBounds(60,39,730,26);panel.Controls.Add(note);
    }
    private void EmptyState(string headline,string detail,bool allowRetry=true){
        var panel=CardPanel(152);
        panel.BackColor=Color.FromArgb(17,37,53);
        var icon=Txt("◉",24,true,Accent);icon.SetBounds(24,20,65,70);panel.Controls.Add(icon);
        var title=Txt(headline,16,true,Ink);title.SetBounds(94,20,620,36);panel.Controls.Add(title);
        var sub=Txt(detail,10,false,Muted);sub.SetBounds(95,61,640,33);panel.Controls.Add(sub);
        if(allowRetry){
            var button=NewButton("↻  Yenidən yoxla",Accent,Bg,165);button.SetBounds(95,104,165,37);
            button.Click+=(_,_)=>Render();panel.Controls.Add(button);
        }
    }
    private void Render() {
        ClearPage();
        int token=viewVersion;
        switch(page){
            case "matches":_ = ReloadMatches(true);break;
            case "standings":ShowStandings();break;
            case "search":ShowSearch();break;
            case "tactics":ShowTactics();break;
            case "favorites":ShowFavorites();break;
            case "settings":_ = ShowSettings();break;
            case "details":if(hasOpenedMatch)_=ShowDetails(token);break;
            case "profile": break;
        }
    }
    private static string BakuDate(DateTime x)=>x.ToString("yyyy-MM-dd",CultureInfo.InvariantCulture);
    private void DateFilter(){
        var p=CardPanel(68);
        var prev=NewButton("‹",Raised,Ink,45);prev.SetBounds(15,13,45,42);
        prev.Click+=(_,_)=>{selectedDate=selectedDate.AddDays(-1);Render();};
        p.Controls.Add(prev);
        var day=Txt(selectedDate.ToString("dd MMM yyyy",CultureInfo.GetCultureInfo("az-Latn-AZ")),12,true,Ink);
        day.SetBounds(74,15,148,38);p.Controls.Add(day);
        var next=NewButton("›",Raised,Ink,45);next.SetBounds(223,13,45,42);
        next.Click+=(_,_)=>{selectedDate=selectedDate.AddDays(1);Render();};p.Controls.Add(next);
        var today=NewButton("Bu gün",Raised,Accent,95);today.SetBounds(280,13,95,42);
        today.Click+=(_,_)=>{selectedDate=DateTime.UtcNow.AddHours(4).Date;Render();};p.Controls.Add(today);
        var combo=LeagueSelect(false);
        combo.Anchor=AnchorStyles.Right|AnchorStyles.Top;combo.SetBounds(p.Width-240,13,214,42);
        p.Controls.Add(combo);
        p.SizeChanged+=(_,_)=>combo.Left=p.Width-240;
    }
    private ComboBox LeagueSelect(bool single){
        var box=new ComboBox {DropDownStyle=ComboBoxStyle.DropDownList,BackColor=Raised,ForeColor=Ink,FlatStyle=FlatStyle.Flat,Font=new Font("Segoe UI",11),Height=44};
        int start=single?1:0;
        for(int i=start;i<leagueNames.Length;i++)box.Items.Add(leagueNames[i]);
        int current=System.Array.IndexOf(leagues,league);
        box.SelectedIndex=Math.Max(0,current-start);
        box.SelectedIndexChanged+=(_,_)=>{
            if(box.SelectedIndex<0)return;
            var value=leagues[box.SelectedIndex+start];
            if(value==league)return;
            league=value;Render();
        };
        return box;
    }
    private async Task ReloadMatches(bool reset) {
        int token=viewVersion;
        if(reset){DashboardHero();DateFilter();ShowCachedMatches();LoadingState("Matç məlumatları yüklənir…");}
        try{
            var data=await Get("/api/live?league="+Uri.EscapeDataString(league)+"&date="+BakuDate(selectedDate));
            if(page!="matches"||token!=viewVersion)return;
            latestMatches=Array(data,"items").Select(x=>x.Clone()).ToList();
            StoreMatches(data);
            SetConnection(Yes(data,"available"));
            content.SuspendLayout();content.Controls.Clear();DashboardHero();DateFilter();
            string note=Val(data,"message");
            if(Yes(data,"partial")||Yes(data,"stale"))
                Message("Qismən və ya köhnə məlumat. Yenilənmə mənbədən təsdiqlənməyib.",true);
            if(!string.IsNullOrWhiteSpace(note))Message(note,!Yes(data,"available"));
            if(latestMatches.Count==0){
                EmptyState(Yes(data,"available")?"Bu tarixdə oyun tapılmadı":"Mənbə hazırda əlçatan deyil",
                    Yes(data,"available")?"Başqa liqa və ya tarix seçə bilərsən.":"Yoxlamanı təkrarla. Render pulsuz serveri oyanarkən gecikə bilər.");
            }else{
                MatchFilterBar(Yes(data,"stale"));
                RenderGroupedMatches(latestMatches,Yes(data,"stale"));
            }
            content.ResumeLayout();
        }catch(Exception e){
            if(page!="matches"||token!=viewVersion)return;
            SetConnection(false);
            if(!File.Exists(MatchesCacheFile)||latestMatches.Count==0){
                content.Controls.Clear();DashboardHero();DateFilter();
                EmptyState("Serverə qoşulmaq mümkün olmadı",e.Message);
            }else Message("Serverlə əlaqə alınmadı: "+e.Message+" · saxlanmış nəticələr CANLI DEYİL.",true);
        }
    }
    private void MatchFilterBar(bool stale){
        var bar=CardPanel(67);
        var live=latestMatches.Count(m=>Val(m,"state")=="live"&&!Yes(m,"stale")&&!stale);
        var total=latestMatches.Count;
        var caption=Txt(total+" matç  ·  "+live+" canlı",11,true,live>0?Accent:Muted);
        caption.SetBounds(12,12,185,40);bar.Controls.Add(caption);
        int left=215;
        foreach(var item in new[]{("all","Hamısı"),("live","● Canlı"),("favorites","☆ Seçilmiş")}){
            string filter=item.Item1;
            var selected=filter==matchFilter;
            var btn=NewButton(item.Item2,selected?Accent:Raised,selected?Bg:Ink,105);
            btn.SetBounds(left,13,105,39);left+=113;
            btn.Click+=(_,_)=>{matchFilter=filter;Render();};
            bar.Controls.Add(btn);
        }
    }
    private void RenderGroupedMatches(IEnumerable<JsonElement> all,bool stale){
        var filtered=all.Where(m=>matchFilter switch{
            "live" => Val(m,"state")=="live"&&!Yes(m,"stale")&&!stale,
            "favorites"=>favoriteSnapshots.ContainsKey(Val(m,"id")), _=>true
        }).ToList();
        if(filtered.Count==0){EmptyState(matchFilter=="live"?"Hazırda canlı matç yoxdur":"Uyğun matç tapılmadı",
            "Başqa tarix, liqa və ya filtri seçə bilərsən.",false);return;}
        foreach(var group in filtered.GroupBy(m=>Val(m,"leagueName",Val(m,"league","Digər")))){
            var title=group.Key;
            var rows=group.ToList();
            var bar=CardPanel(45);
            bar.BackColor=Color.FromArgb(27,48,65);
            var label=Txt((collapsedLeagues.Contains(title)?"▸  ":"▾  ")+title,11,true,Ink);
            label.SetBounds(14,2,Math.Max(300,bar.Width-150),39);bar.Controls.Add(label);
            var count=Txt(rows.Count+" oyun",10,true,Accent);count.Anchor=AnchorStyles.Right;
            count.SetBounds(bar.Width-105,3,90,38);bar.Controls.Add(count);
            bar.SizeChanged+=(_,_)=>count.Left=bar.Width-105;
            void Toggle(object? sender,EventArgs e){if(!collapsedLeagues.Add(title))collapsedLeagues.Remove(title);Render();}
            bar.Cursor=Cursors.Hand;bar.Click+=Toggle;label.Click+=Toggle;count.Click+=Toggle;
            if(collapsedLeagues.Contains(title))continue;
            foreach(var match in rows)MatchRow(match,stale);
        }
    }
    private static string Team(JsonElement m,string key)=>Val(Prop(m,key),"name","—");
    private string Score(JsonElement m){
        if(Val(m,"state")=="scheduled")return "— : —";
        return Val(m,"homeScore","—")+" : "+Val(m,"awayScore","—");
    }
    private string Status(JsonElement m){
        var state=Val(m,"state");
        return state=="live"?"● CANLI  "+Val(m,"minute"):state=="final"?"Bitib":state=="scheduled"?"Başlamayıb":state;
    }
    private void MatchRow(JsonElement m,bool saved=false) {
        var p=CardPanel(78);
        var home=Txt(Team(m,"home"),11,true);home.SetBounds(48,9,206,30);home.Anchor=AnchorStyles.Top|AnchorStyles.Left;p.Controls.Add(home);
        var away=Txt(Team(m,"away"),11,true);away.SetBounds(48,40,206,28);p.Controls.Add(away);
        var homeBadge=new PictureBox{Left=15,Top=12,Width=25,Height=25,SizeMode=PictureBoxSizeMode.Zoom};
        var awayBadge=new PictureBox{Left=15,Top=42,Width=25,Height=25,SizeMode=PictureBoxSizeMode.Zoom};
        p.Controls.Add(homeBadge);p.Controls.Add(awayBadge);
        _=AttachBadgeAsync(homeBadge,Val(Prop(m,"home"),"image"));
        _=AttachBadgeAsync(awayBadge,Val(Prop(m,"away"),"image"));
        var score=Txt(Score(m),16,true,Ink);score.SetBounds(258,17,145,39);p.Controls.Add(score);
        var state=Txt(saved?"Saxlanmış nəticə · canlı deyil":Status(m),10,false,Val(m,"state")=="live"?Accent:Muted);
        state.SetBounds(417,15,160,36);p.Controls.Add(state);
        string id=Val(m,"id");
        var fav=NewButton(favoriteSnapshots.ContainsKey(id)?"★":"☆",Raised,Accent,50);
        fav.Anchor=AnchorStyles.Right|AnchorStyles.Top;fav.SetBounds(p.Width-58,18,42,38);
        p.Controls.Add(fav);p.SizeChanged+=(_,_)=>fav.Left=p.Width-58;
        fav.Click+=(_,_)=>{
            if(favoriteSnapshots.ContainsKey(id))favoriteSnapshots.Remove(id);
            else favoriteSnapshots[id]=m.GetRawText();
            SaveFavorites();fav.Text=favoriteSnapshots.ContainsKey(id)?"★":"☆";
        };
        p.Cursor=Cursors.Hand;
        EventHandler open=(_,_)=>{openedMatch=m.Clone();hasOpenedMatch=true;page="details";Render();};
        foreach(Control x in p.Controls)if(x!=fav)x.Click+=open;
        p.Click+=open;
        homeBadge.Click+=open;awayBadge.Click+=open;
    }
    private void SaveFavorites(){
        try{Directory.CreateDirectory(Path.GetDirectoryName(savePath)!);File.WriteAllText(savePath,JsonSerializer.Serialize(favoriteSnapshots));}catch{}
    }
    private void ShowStandings(){
        if(league=="all")league="eng.1";
        var p=CardPanel(67);
        var l=Txt("Liqa",11,true);l.SetBounds(15,14,70,39);p.Controls.Add(l);
        var choose=LeagueSelect(true);choose.SetBounds(90,14,255,39);p.Controls.Add(choose);
        _=LoadStandings(viewVersion);
    }
    private async Task LoadStandings(int token){
        Message("Turnir cədvəli alınır…");
        try{
            var d=await Get("/api/standings?league="+Uri.EscapeDataString(league));
            if(page!="standings"||token!=viewVersion)return;
            content.Controls.Clear();
            var p=CardPanel(67);
            var l=Txt("Liqa",11,true);l.SetBounds(15,14,70,39);p.Controls.Add(l);
            var choose=LeagueSelect(true);choose.SetBounds(90,14,255,39);p.Controls.Add(choose);
            if(Yes(d,"stale"))Message("Cədvəl əvvəlki saxlanmış mənbədən alınıb.",true);
            var rows=Array(d,"items").ToList();
            if(rows.Count==0){Message(Val(d,"message","Hazırda cədvəl mövcud deyil."),true);return;}
            Heading("Sıra     Klub                                         O      Q      H      M      X");
            foreach(var x in rows){
                var b=CardPanel(57);
                var rank=Txt(Val(x,"rank","—"),12,true,Accent);rank.SetBounds(14,6,40,42);b.Controls.Add(rank);
                var name=Txt(Val(x,"name"),12,true);name.SetBounds(62,6,270,42);b.Controls.Add(name);
                var stats=Txt(Val(x,"played","—")+"     "+Val(x,"win","—")+"     "+Val(x,"draw","—")+"     "+Val(x,"loss","—")+"     "+Val(x,"points","—"),12);
                stats.SetBounds(350,6,260,42);b.Controls.Add(stats);
            }
        }catch(Exception e){if(page!="standings"||token!=viewVersion)return;content.Controls.Clear();Message("Cədvəl yüklənmədi: "+e.Message,true);}
    }
    private void ShowSearch(){
        var p=CardPanel(86);
        var text=new TextBox{Text=query,BackColor=Raised,ForeColor=Ink,BorderStyle=BorderStyle.FixedSingle,Font=new Font("Segoe UI",13),Width=330};
        text.SetBounds(14,18,330,42);p.Controls.Add(text);
        var kind=new ComboBox{BackColor=Raised,ForeColor=Ink,DropDownStyle=ComboBoxStyle.DropDownList,FlatStyle=FlatStyle.Flat,Width=145};
        kind.Items.AddRange(new object[]{"Hamısı","Futbolçular","Klublar","Məşqçilər"});
        kind.SelectedIndex=selectedKind switch {"players"=>1,"teams"=>2,"coaches"=>3,_=>0};
        kind.SetBounds(354,19,145,41);p.Controls.Add(kind);
        var button=NewButton("Axtar",Accent,Bg,110);button.SetBounds(512,17,110,44);p.Controls.Add(button);
        void Go(){query=text.Text.Trim();selectedKind=kind.SelectedIndex switch{1=>"players",2=>"teams",3=>"coaches",_=>"all"};_ = LoadSearch(query,selectedKind);}
        button.Click+=(_,_)=>Go();text.KeyDown+=(_,e)=>{if(e.KeyCode==Keys.Enter){e.SuppressKeyPress=true;Go();}};
        Message("500 mindən artıq real futbol qeydini serverdə axtara bilərsən. Nəticələr mənbədən alınır.");
        if(query.Length>0)Go();
    }
    private async Task LoadSearch(string q,string kind){
        if(string.IsNullOrWhiteSpace(q)){Message("Axtarış üçün ad yaz.");return;}
        int token=viewVersion;
        try{
            var data=await Get("/api/search?q="+Uri.EscapeDataString(q)+"&kind="+kind);
            if(page!="search"||token!=viewVersion)return;
            // Preserve the two input panels; replace only search results.
            while(content.Controls.Count>2) content.Controls.RemoveAt(content.Controls.Count-1);
            var rows=Array(data,"items").ToList();
            Heading("Nəticələr · "+rows.Count);
            if(rows.Count==0){Message("Bu sorğu üzrə nəticə tapılmadı.");return;}
            foreach(var row in rows){
                var p=CardPanel(70);p.Cursor=Cursors.Hand;
                var name=Txt(Val(row,"name","—"),12,true);name.SetBounds(18,7,520,29);p.Controls.Add(name);
                var meta=Txt(Val(row,"country")+"  ·  "+Val(row,"kind")+"  ·  "+Val(row,"source"),9,false,Muted);
                meta.SetBounds(18,38,520,23);p.Controls.Add(meta);
                var id=Val(row,"id");
                EventHandler open=(_,_)=>_ = OpenProfile(id);
                p.Click+=open;name.Click+=open;meta.Click+=open;
            }
        }catch(Exception e){if(page!="search"||token!=viewVersion)return;Message("Axtarış alınmadı: "+e.Message,true);}
    }
    private async Task OpenProfile(string id){
        page="profile";ClearPage();
        int token=viewVersion;
        Message("Profil yüklənir…");
        try{
            var d=await Get("/api/profile?id="+Uri.EscapeDataString(id));
            if(page!="profile"||token!=viewVersion)return;
            content.Controls.Clear();
            var p=Prop(d,"profile");
            if(p.ValueKind!=JsonValueKind.Object){Message("Bu profil üçün təsdiqlənmiş məlumat yoxdur.",true);return;}
            var header=CardPanel(185);
            var name=Txt(Val(p,"name","—"),21,true,Accent);name.SetBounds(134,10,520,52);header.Controls.Add(name);
            var photo=new PictureBox{Left=20,Top=22,Width=100,Height=100,BackColor=Raised,SizeMode=PictureBoxSizeMode.Zoom};
            header.Controls.Add(photo);_ = AttachBadgeAsync(photo,Val(p,"image"));
            var kind=Txt(Val(p,"kind")+" · "+Val(p,"country"),12,false,Muted);kind.SetBounds(134,70,520,30);header.Controls.Add(kind);
            var dates=Txt("Doğum: "+Val(p,"birth","məlum deyil")+"     Vəfat: "+Val(p,"death","—"),11);dates.SetBounds(22,110,620,32);header.Controls.Add(dates);
            foreach(var entry in new[]{"position","description","source","careerStatus","lifeStatus"}){
                var value=Val(p,entry);
                if(!string.IsNullOrWhiteSpace(value))Message(entry+": "+value);
            }
            foreach(var entry in new[]{"clubs","coached","awards"}){
                var a=Array(p,entry).ToList();if(a.Count==0)continue;
                Heading(entry+" ("+a.Count+")");
                foreach(var item in a.Take(35))Message(item.ValueKind==JsonValueKind.String?item.ToString():Val(item,"name",item.ToString()).Substring(0,Math.Min(170,Val(item,"name",item.ToString()).Length)));
            }
            Heading("Wikipedia / Wikidata və karyera keçidləri");
            string qid=Val(p,"wikidataId",Val(p,"qid"));
            if(System.Text.RegularExpressions.Regex.IsMatch(qid,@"^Q[1-9][0-9]{0,11}$")){
                ExternalLink("Wikidata profili","https://www.wikidata.org/wiki/"+qid);
                ExternalLink("Wikipedia dillərində məqalələr","https://www.wikidata.org/wiki/Special:SiteLinks/"+qid);
            }
            string sourceUrl=Val(p,"wikipediaUrl",Val(p,"url"));
            if(Uri.TryCreate(sourceUrl,UriKind.Absolute,out var uri)&&uri.Scheme=="https")
                ExternalLink("Təsdiqlənmiş mənbə səhifəsi",sourceUrl);
            string profileName=Val(p,"name");
            ExternalLink("Wikipedia-da axtar","https://en.wikipedia.org/w/index.php?search="+Uri.EscapeDataString(profileName));
            bool club=Val(p,"kind")=="teams";
            ExternalLink(club?"Heyət və transfer axtarışı":"Karyera və transfer axtarışı",
                "https://www.google.com/search?q="+Uri.EscapeDataString(profileName+(club?" club squad transfers":" football career transfers")));
            ExternalLink(club?"Oyunlar və nəticələr":"Mövsümlük statistika axtarışı",
                "https://www.google.com/search?q="+Uri.EscapeDataString(profileName+(club?" football fixtures results":" football season statistics")));
        }catch(Exception e){if(page=="profile"&&token==viewVersion){content.Controls.Clear();Message("Profil açılmadı: "+e.Message,true);}}
    }
    private void ExternalLink(string title,string url){
        var p=CardPanel(52);
        var link=new LinkLabel{Text=title,LinkColor=Accent,ActiveLinkColor=Color.White,
            VisitedLinkColor=Accent,Dock=DockStyle.Fill,TextAlign=ContentAlignment.MiddleLeft,Padding=new Padding(9)};
        link.Click+=(_,_)=>{
            try{
                var uri=new Uri(url);
                if(uri.Scheme=="https")System.Diagnostics.Process.Start(new System.Diagnostics.ProcessStartInfo(uri.AbsoluteUri){UseShellExecute=true});
            }catch(Exception ex){Message("Keçid açılmadı: "+ex.Message,true);}
        };
        p.Controls.Add(link);
    }
    private void ShowLineup(JsonElement lineup,string side,string teamName){
        var squad=Prop(lineup,side);
        if(squad.ValueKind!=JsonValueKind.Object)return;
        var starters=Array(squad,"starters").ToList();
        var bench=Array(squad,"substitutes").ToList();
        if(starters.Count+bench.Count==0)return;
        Heading(teamName+" · "+(Yes(squad,"formationVerified")?Val(squad,"formation"):"Düzülüş təsdiqlənməyib"));
        if(Yes(squad,"incomplete"))Message("Heyət mənbədə natamamdır.",true);
        void Rows(string name,List<JsonElement> players){
            if(players.Count==0)return;
            Heading(name+" ("+players.Count+")");
            foreach(var player in players.Take(25))
                Message(Val(player,"number","—")+"   "+Val(player,"name","—")+"   "+Val(player,"position"));
        }
        Rows("İlk 11",starters);Rows("Ehtiyatlar",bench);
    }
    private async Task ShowDetails(int token){
        var m=openedMatch;
        var p=CardPanel(170);
        var name=Txt(Team(m,"home")+"   "+Score(m)+"   "+Team(m,"away"),20,true,Accent);
        name.SetBounds(20,14,790,56);p.Controls.Add(name);
        var meta=Txt(Val(m,"leagueName")+"  ·  "+Status(m)+"  ·  "+Val(m,"source"),11,false,Muted);
        meta.SetBounds(20,83,790,42);p.Controls.Add(meta);
        string id=Val(m,"id");
        var split=id.Split(':',3);
        if(split.Length!=3 || !new[]{"espn","open","sportsdb"}.Contains(split[0])){Message("Bu matçın detalları hazırda mövcud deyil.");return;}
        Message("Matç hadisələri və statistika alınır…");
        try{
            var data=await Get("/api/match-detail?provider="+split[0]+"&league="+Uri.EscapeDataString(split[1])+"&id="+Uri.EscapeDataString(split[2]));
            if(page!="details"||token!=viewVersion)return;
            if(!Yes(data,"available"))Message(Val(data,"message","Təfsilat mənbədə mövcud deyil."),true);
            var events=Array(data,"events").Take(70).ToList();
            if(events.Count>0){
                Heading("Matç hadisələri");
                foreach(var ev in events)Message(Val(ev,"minute",Val(ev,"clock"))+"  "+Val(ev,"text",Val(ev,"type",ev.ToString())));
            }
            var stats=Array(data,"statistics").Take(40).ToList();
            if(stats.Count>0){
                Heading("Matç statistikası");
                foreach(var ev in stats){
                    string left=Val(ev,"home",Val(ev,"homeValue","—")),right=Val(ev,"away",Val(ev,"awayValue","—"));
                    var block=CardPanel(77);
                    var statLabel=Txt(Val(ev,"name",Val(ev,"label","Statistika")),11,true);
                    statLabel.SetBounds(15,6,310,32);block.Controls.Add(statLabel);
                    var value=Txt(left+"  :  "+right,11,true,Accent);
                    value.SetBounds(345,6,170,32);block.Controls.Add(value);
                    static bool ParseStat(string s,out double n) =>
                        double.TryParse(s.Trim().TrimEnd('%').Replace(',','.'),NumberStyles.Float,CultureInfo.InvariantCulture,out n)&&n>=0;
                    if(ParseStat(left,out var l)&&ParseStat(right,out var r)&&l+r>0){
                        int width=440;
                        var track=new Panel{Left=15,Top=48,Width=width,Height=8,BackColor=Raised};block.Controls.Add(track);
                        var fill=new Panel{Left=0,Top=0,Width=Math.Clamp((int)Math.Round(width*l/(l+r)),1,width),Height=8,BackColor=Accent};
                        track.Controls.Add(fill);
                    }
                }
            }else Message("Mənbədə statistika yoxdur.");
            var lineup=Prop(data,"lineup");
            if(lineup.ValueKind==JsonValueKind.Object){
                Heading("Təsdiqlənmiş heyətlər");
                ShowLineup(lineup,"home",Team(m,"home"));
                ShowLineup(lineup,"away",Team(m,"away"));
            }
        }catch(Exception e){if(page=="details"&&token==viewVersion)Message("Matç detalları alınmadı: "+e.Message,true);}
    }
    private void ShowFavorites(){
        Heading("Yadda saxlanmış matçlar");
        Message("Bu siyahı əvvəlki qeydləri göstərir. Köhnə hesab canlı nəticə kimi təqdim edilmir.");
        if(favoriteSnapshots.Count==0){Message("Hələ seçilmiş matç yoxdur. Matçın yanındakı ☆ düyməsinə bas.");return;}
        foreach(var raw in favoriteSnapshots.Values.ToList()){
            try{using var json=JsonDocument.Parse(raw);MatchRow(json.RootElement.Clone(),saved:true);}catch{}
        }
    }
    private string Option(string name,string fallback="") => options.TryGetValue(name,out var value)?value:fallback;
    private void SaveOption(string name,string value){
        options[name]=value;
        try{
            Directory.CreateDirectory(Path.GetDirectoryName(optionsPath)!);
            File.WriteAllText(optionsPath,JsonSerializer.Serialize(options));
        }catch(IOException ex){Message("Ayar saxlanmadı: "+ex.Message,true);}
    }
    private void ShowTactics(){
        Heading("TAKTİKA STUDİYASI PRO · Yerli məşq planı");
        var panel=CardPanel(85);
        var t=Txt("Düzülüş",12,true);t.SetBounds(12,14,95,42);panel.Controls.Add(t);
        var select=new ComboBox{DropDownStyle=ComboBoxStyle.DropDownList,BackColor=Raised,ForeColor=Ink};
        select.Items.AddRange(formations.Cast<object>().ToArray());
        select.SelectedIndex=formation;select.SetBounds(110,17,165,39);panel.Controls.Add(select);
        var modes=new ComboBox{DropDownStyle=ComboBoxStyle.DropDownList,BackColor=Raised,ForeColor=Ink};
        modes.Items.AddRange(new object[]{"Standart","Hücum","Müdafiə"});
        modes.SelectedItem=Option("tactic_mode","Standart");
        if(modes.SelectedIndex<0)modes.SelectedIndex=0;
        modes.SetBounds(292,17,145,39);panel.Controls.Add(modes);
        modes.SelectedIndexChanged+=(_,_)=>SaveOption("tactic_mode",modes.Text);
        var field=CardPanel(545);
        var pitch=new PitchPanel {Dock=DockStyle.Fill,Formation=formations[formation]};
        field.Controls.Add(pitch);
        select.SelectedIndexChanged+=(_,_)=>{
            formation=select.SelectedIndex;
            SaveOption("tactic_formation",formation.ToString(CultureInfo.InvariantCulture));
            pitch.Formation=formations[formation];
            Render();
        };
        var tools=CardPanel(78);
        int bx=12;
        void Tool(string label,Action click,int width=130){
            var b=NewButton(label,Raised,Ink,width);b.SetBounds(bx,12,width,45);bx+=width+10;
            b.Click+=(_,_)=>click();tools.Controls.Add(b);
        }
        Tool("➜ Oxları çək",()=>{pitch.ArrowMode=!pitch.ArrowMode;},128);
        Tool("▦ Tor",()=>{pitch.ShowGrid=!pitch.ShowGrid;},95);
        Tool("Oxları sil",pitch.ClearArrows,115);
        var extras=CardPanel(76);int ex=12;
        void Extra(string label,Action action,int width){
            var btn=NewButton(label,Raised,Ink,width);btn.SetBounds(ex,12,width,45);ex+=width+10;
            btn.Click+=(_,_)=>action();extras.Controls.Add(btn);
        }
        Extra("▶ Animasiya",pitch.TogglePlayback,150);
        Extra("▣ PNG saxla",()=>{
            using var save=new SaveFileDialog{Title="Taktika şəkli",Filter="PNG (*.png)|*.png",FileName="MATCHLAB_AZ_Taktika_"+formations[formation].Replace("-","_")+".png"};
            if(save.ShowDialog(this)!=DialogResult.OK)return;
            try{pitch.ExportPng(save.FileName);MessageBox.Show("Məşq planı PNG kimi saxlandı.","MATCHLAB AZ");}
            catch(Exception e){MessageBox.Show("PNG saxlamaq alınmadı: "+e.Message,"MATCHLAB AZ");}
        },150);
        Tool("Sıfırla",()=>{
            if(MessageBox.Show("Bu düzülüşü sıfırlamaq istəyirsən?","MATCHLAB AZ",MessageBoxButtons.YesNo)==DialogResult.Yes)
                pitch.ResetPlan();
        },100);
        Tool("Paylaş",()=>{
            var sb=new System.Text.StringBuilder(pitch.ExportText());
            sb.Append("\nRejim: ").Append(Option("tactic_mode","Standart")).Append("\nEhtiyatlar:");
            for(int n=1;n<=7;n++)sb.Append("\n").Append(n).Append(". ").Append(Option("sub_"+formation+"_"+n,"—"));
            Clipboard.SetText(sb.ToString());
            MessageBox.Show("Taktika və ehtiyatlar mübadilə buferinə köçürüldü.","MATCHLAB AZ");
        },112);
        Heading("Ehtiyat oyunçular");
        for(int n=1;n<=7;n++){
            int index=n;
            var row=CardPanel(61);
            var label=Txt(n+".  "+Option("sub_"+formation+"_"+n,"Ehtiyat oyunçu"),11);
            label.SetBounds(16,8,430,38);row.Controls.Add(label);
            var edit=NewButton("Dəyiş",Raised,Accent,120);edit.SetBounds(465,8,120,40);
            edit.Click+=(_,_)=>{
                using var dialog=new Form{Text="Ehtiyat oyunçu "+index,Width=405,Height=170,StartPosition=FormStartPosition.CenterParent};
                var name=new TextBox{Left=18,Top=17,Width=350,Text=Option("sub_"+formation+"_"+index,"")};
                var save=NewButton("Saxla",Accent,Bg,110);save.SetBounds(258,60,110,42);
                save.Click+=(_,_)=>{SaveOption("sub_"+formation+"_"+index,name.Text.Trim());dialog.DialogResult=DialogResult.OK;};
                dialog.Controls.AddRange(new Control[]{name,save});
                if(dialog.ShowDialog(this)==DialogResult.OK)Render();
            };
            row.Controls.Add(edit);
        }
        Message("Meydanda 11 oyunçunu sürüşdür, iki dəfə kliklə ad/nömrəni dəyiş. Hərəkət oxlarını animasiyada oynat və PNG saxla. Şəxsi plan avtomatik yadda qalır.");
    }
    private async Task ShowSettings(){
        Heading("Bildiriş və səs mərkəzi · kateqoriyalar");
        string[] toneNames={"Səssiz","Qısa siqnal","Təsdiq","Xəbərdarlıq","İkili siqnal"};
        for(int i=0;i<alertIds.Length;i++){
            string id=alertIds[i];
            var card=CardPanel(77);
            var label=Txt(alertNames[i],11,true);label.SetBounds(12,12,185,42);card.Controls.Add(label);
            var tone=new ComboBox{DropDownStyle=ComboBoxStyle.DropDownList,BackColor=Raised,ForeColor=Ink};
            tone.Items.AddRange(toneNames.Cast<object>().ToArray());
            tone.SelectedIndex=int.TryParse(Option("tone_"+id,"1"),out var chosen)?Math.Clamp(chosen,0,4):1;
            tone.SetBounds(199,15,170,37);card.Controls.Add(tone);
            tone.SelectedIndexChanged+=(_,_)=>SaveOption("tone_"+id,tone.SelectedIndex.ToString());
            var vibrate=new CheckBox{Text="Vibrasiya",ForeColor=Ink,Checked=Option("vibrate_"+id,"false")=="true"};
            vibrate.SetBounds(383,16,120,38);
            vibrate.CheckedChanged+=(_,_)=>SaveOption("vibrate_"+id,vibrate.Checked?"true":"false");
            card.Controls.Add(vibrate);
            var preview=NewButton("♪ Sına",Raised,Accent,100);preview.SetBounds(510,13,100,42);
            preview.Click+=(_,_)=>{
                int n=tone.SelectedIndex;
                if(n>0)System.Media.SystemSounds.Beep.Play();
                if(vibrate.Checked)MessageBox.Show("Windows masaüstündə vibrasiya cihazı aşkarlanması tətbiq olunmayıb.","MATCHLAB AZ");
            };
            card.Controls.Add(preview);
        }
        Heading("Proqram məlumatı");
        Message("MATCHLAB AZ Native v0.9.54 · Windows Forms. Brauzer və WebView işlətmir.");
        Message("Bildiriş seçimləri və səs sınaqları lokaldır; avtomatik canlı push bildirişləri hələ aktiv deyil.");
        Message("Canlı nəticələr və profillər Render serverindən HTTPS API vasitəsilə gəlir. İnternet olmayanda uydurma statistika göstərilmir.");
        try{
            var d=await Get("/api/status");
            if(page!="settings")return;
            SetConnection(Yes(d,"ok"));
            Message("Server: "+Val(d,"version")+"  ·  Arxiv: "+Val(Prop(d,"world"),"total","yüklənməyib"));
        }catch(Exception e){if(page=="settings"){SetConnection(false);Message("Server vəziyyəti: "+e.Message,true);}}
    }
    protected override void OnFormClosed(FormClosedEventArgs e){refreshTimer.Stop();Api.Dispose();base.OnFormClosed(e);}
}

