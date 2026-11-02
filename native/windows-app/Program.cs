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
    private static int Main(string[] args)
    {
        ApplicationConfiguration.Initialize();
        using var app=new MatchlabForm();
        if(args.Contains("--ui-smoke-test",StringComparer.OrdinalIgnoreCase))
        {
            var timer=new System.Windows.Forms.Timer {Interval=2200};
            app.Shown+=(_,_)=>timer.Start();
            timer.Tick+=(_,_)=>{timer.Stop();app.RunNativeSmokeTest();app.Close();};
            Application.Run(app);
            return app.SmokeResult;
        }
        Application.Run(app);
        return 0;
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
    private static readonly Color Accent = Color.FromArgb(153, 236, 116);
    private static readonly Color Red = Color.FromArgb(245, 117, 122);
    private static readonly HttpClient Api = new()
    {
        BaseAddress = new Uri("https://matchlab-az-online.onrender.com"),
        Timeout = TimeSpan.FromSeconds(28)
    };
    private readonly string[] leagues = {"all","eng.1","esp.1","ger.1","ita.1","fra.1","uefa.champions","uefa.europa","tur.1","por.1","ned.1"};
    private readonly string[] leagueNames = {"Bütün liqalar","Premier League","La Liga","Bundesliga","Serie A","Ligue 1","Champions League","Europa League","Süper Lig","Primeira Liga","Eredivisie"};
    private readonly Dictionary<string, string> favoriteSnapshots = new();
    private readonly string savePath = Path.Combine(
        Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
        "MATCHLAB_AZ", "favorites.json");
    private readonly System.Windows.Forms.Timer refreshTimer = new() { Interval = 30000 };
    private readonly FlowLayoutPanel content = new() { Dock=DockStyle.Fill, AutoScroll=true, WrapContents=false, FlowDirection=FlowDirection.TopDown, BackColor=Bg, Padding=new Padding(22,18,22,18) };
    private readonly Label title = new() { Dock=DockStyle.Left, AutoSize=false, Width=540, Font=new Font("Segoe UI Semibold",21f), ForeColor=Ink, TextAlign=ContentAlignment.MiddleLeft };
    private readonly Label connection = new() { Dock=DockStyle.Right, AutoSize=false, Width=200, ForeColor=Muted, TextAlign=ContentAlignment.MiddleCenter, Text="●  Mənbə yoxlanılır" };
    private readonly Panel nav = new() { Dock=DockStyle.Fill, BackColor=Sidebar };
    private readonly List<Button> navButtons = new();
    private string page="matches";
    private string league="all";
    private DateTime selectedDate=DateTime.UtcNow.AddHours(4).Date;
    private string selectedKind="all";
    private string query="";
    private int viewVersion;
    private JsonElement openedMatch;
    private bool hasOpenedMatch;
    private int formation=0;
    private readonly string[] formations={"4-3-3","4-2-3-1","4-4-2","3-5-2"};
    private List<JsonElement> latestMatches = new();
    private readonly Panel intro = new(){Dock=DockStyle.Fill,BackColor=Bg};
    private readonly Label introState = new(){ForeColor=Muted,TextAlign=ContentAlignment.MiddleCenter,Font=new Font("Segoe UI",12)};
    private readonly System.Windows.Forms.Timer introTimer = new(){Interval=95};
    private int introTicks;
    private bool introFinished;
    public int SmokeResult {get;private set;}=10;
    public void RunNativeSmokeTest()
    {
        // Only genuine WinForms widgets are used; verify user-visible navigation.
        if(WindowState!=FormWindowState.Maximized){SmokeResult=11;return;}
        if(navButtons.Count!=6){SmokeResult=12;return;}
        foreach(string route in new[]{"search","tactics","standings","matches"})
        {
            var b=navButtons.FirstOrDefault(x=>string.Equals(x.Tag as string,route,StringComparison.Ordinal));
            if(b==null){SmokeResult=13;return;}
            b.PerformClick();
            if(page!=route){SmokeResult=14;return;}
        }
        if(!introFinished||intro.Visible){SmokeResult=15;return;}
        SmokeResult=0;
    }

    public MatchlabForm()
    {
        Text="MATCHLAB AZ — Futbol mərkəzi";
        StartPosition=FormStartPosition.CenterScreen;
        MinimumSize=new Size(940,680);
        Size=new Size(1280,830);
        WindowState=FormWindowState.Maximized; // Windows-maximized, taskbar and window controls stay usable.
        BackColor=Bg;
        ForeColor=Ink;
        try { Icon=Icon.ExtractAssociatedIcon(Application.ExecutablePath) ?? Icon; }
        catch { /* Windows may use the embedded executable icon directly. */ }
        Font=new Font("Segoe UI",10);
        try {
            if (File.Exists(savePath)) {
                var raw = JsonSerializer.Deserialize<Dictionary<string,string>>(File.ReadAllText(savePath));
                if(raw!=null)foreach(var x in raw) favoriteSnapshots[x.Key]=x.Value;
            }
        }catch {}
        var shell=new TableLayoutPanel {Dock=DockStyle.Fill, ColumnCount=2, RowCount=1, Margin=Padding.Empty, Padding=Padding.Empty, BackColor=Bg};
        shell.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute,222));
        shell.ColumnStyles.Add(new ColumnStyle(SizeType.Percent,100));
        Controls.Add(shell);
        shell.Controls.Add(nav,0,0);
        var right=new TableLayoutPanel {Dock=DockStyle.Fill, ColumnCount=1, RowCount=2, Padding=Padding.Empty};
        right.RowStyles.Add(new RowStyle(SizeType.Absolute,86));
        right.RowStyles.Add(new RowStyle(SizeType.Percent,100));
        shell.Controls.Add(right,1,0);
        var top=new Panel {Dock=DockStyle.Fill,BackColor=Bg,Padding=new Padding(25,8,22,5)};
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
                if(c is Panel || c is FlowLayoutPanel) c.Width=Math.Max(380,content.ClientSize.Width-52);
        };
        refreshTimer.Tick+=(_,_)=>{ if(page=="matches"&&WindowState!=FormWindowState.Minimized) _=ReloadMatches(false); };
        refreshTimer.Start();
        Render();
        ConfigureIntro();
        Controls.Add(intro);intro.BringToFront();
        introTimer.Tick+=(_,_)=>{
            introTicks++;
            introState.Text="Futbol mərkəzi hazırlanır"+new string('.',(introTicks/3)%4);
            if(introTicks>=12)
            {
                introTimer.Stop();introFinished=true;intro.Visible=false;
            }
        };
        Shown+=(_,_)=>introTimer.Start();
        FormClosed+=(_,_)=>{introTimer.Stop();refreshTimer.Stop();};
    }

    private void ConfigureIntro()
    {
        // Native WinForms splash: intentionally independent of the backend.
        var layout=new TableLayoutPanel{Dock=DockStyle.Fill,ColumnCount=1,RowCount=6,BackColor=Bg};
        layout.RowStyles.Add(new RowStyle(SizeType.Percent,34));
        layout.RowStyles.Add(new RowStyle(SizeType.Absolute,96));
        layout.RowStyles.Add(new RowStyle(SizeType.Absolute,68));
        layout.RowStyles.Add(new RowStyle(SizeType.Absolute,42));
        layout.RowStyles.Add(new RowStyle(SizeType.Absolute,22));
        layout.RowStyles.Add(new RowStyle(SizeType.Percent,66));
        var logo=new PictureBox{Dock=DockStyle.Fill,SizeMode=PictureBoxSizeMode.CenterImage};
        if(Icon!=null)
        {
            using var bitmap=Icon.ToBitmap();
            logo.Image=new Bitmap(bitmap,new Size(86,86));
        }
        layout.Controls.Add(logo,0,1);
        var brand=Txt("MATCHLAB AZ",31,true,Accent);
        brand.Dock=DockStyle.Fill;
        brand.TextAlign=ContentAlignment.MiddleCenter;
        layout.Controls.Add(brand,0,2);
        var subtitle=Txt("FUTBOL MƏRKƏZİ  ·  v0.9.45",12,false,Ink);
        subtitle.Dock=DockStyle.Fill;subtitle.TextAlign=ContentAlignment.MiddleCenter;
        layout.Controls.Add(subtitle,0,3);
        var progress=new ProgressBar{
            Style=ProgressBarStyle.Marquee,MarqueeAnimationSpeed=40,
            Width=210,Height=5,Anchor=AnchorStyles.None
        };
        layout.Controls.Add(progress,0,4);
        introState.Dock=DockStyle.Fill;introState.Text="MATCHLAB AZ açılır";
        layout.Controls.Add(introState,0,5);
        intro.Controls.Add(layout);
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
        var brand=Txt("◉  MATCHLAB",18,true,Accent);
        brand.SetBounds(22,29,185,36);
        nav.Controls.Add(brand);
        var sub=Txt("AZ  ·  NATIVE 0.9.45",9,false,Muted);
        sub.SetBounds(24,66,182,26);
        nav.Controls.Add(sub);
        var items=new(string key,string label)[]{
            ("matches","⚽  Matçlar"),("standings","▤   Cədvəl"),("search","⌕   Axtarış"),
            ("tactics","▦   Taktika"),("favorites","☆   Seçilmişlər"),("settings","⚙   Tənzimləmələr")
        };
        int y=126;
        foreach(var item in items){
            var b=NewButton(item.label,Sidebar,Ink,184);
            b.SetBounds(18,y,184,46);
            b.TextAlign=ContentAlignment.MiddleLeft;
            b.Click+=(_,_)=>{page=item.key;Render();};
            nav.Controls.Add(b);
            navButtons.Add(b);
            b.Tag=item.key;
            y+=54;
        }
        var note=Txt("Nəticələr real mənbələrdən\nalınır. Tam canlılıq zəmanəti yoxdur.",9,false,Muted);
        note.SetBounds(20,540,185,80);
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
            b.BackColor=active?Raised:Sidebar;
            b.ForeColor=active?Accent:Ink;
        }
        title.Text=page switch {
            "matches"=>"Canlı matçlar","standings"=>"Turnir cədvəli","search"=>"Futbol arxivi",
            "tactics"=>"Taktika studiyası","favorites"=>"Seçilmiş matçlar","settings"=>"Tənzimləmələr",
            "details"=>"Matç mərkəzi","profile"=>"Futbol profili",_=>"MATCHLAB AZ"
        };
    }
    private Panel CardPanel(int height=80) {
        var p=new Panel {BackColor=Card,Width=Math.Max(400,content.ClientSize.Width-52),Height=height,Margin=new Padding(0,0,0,12),Padding=new Padding(14)};
        content.Controls.Add(p);
        return p;
    }
    private void Message(string message,bool warning=false){
        var p=CardPanel(85);
        var l=Txt(message,11,false,warning?Red:Muted);
        l.Dock=DockStyle.Fill;l.Padding=new Padding(9);
        p.Controls.Add(l);
    }
    private void Heading(string text) {
        var row=CardPanel(37);
        row.BackColor=Bg;
        row.Padding=Padding.Empty;
        var l=Txt(text,12,true,Accent);l.Dock=DockStyle.Fill;row.Controls.Add(l);
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
        if(reset){DateFilter(); Message("Mənbədən real nəticələr alınır…");}
        try{
            var data=await Get("/api/live?league="+Uri.EscapeDataString(league)+"&date="+BakuDate(selectedDate));
            if(page!="matches"||token!=viewVersion)return;
            latestMatches=Array(data,"items").Select(x=>x.Clone()).ToList();
            SetConnection(Yes(data,"available"));
            content.SuspendLayout();content.Controls.Clear();DateFilter();
            string note=Val(data,"message");
            if(Yes(data,"partial")||Yes(data,"stale"))
                Message("Qismən və ya köhnə məlumat. Yenilənmə mənbədən təsdiqlənməyib.",true);
            if(!string.IsNullOrWhiteSpace(note))Message(note,!Yes(data,"available"));
            if(latestMatches.Count==0){
                Message(Yes(data,"available")?"Bu tarix və liqa üçün matç yoxdur.":"Mənbə cavab vermədi və ya məlumat təqdim etmədi.",!Yes(data,"available"));
            }else{
                string group="";
                foreach(var m in latestMatches){
                    string next=Val(m,"leagueName",Val(m,"league","Digər"));
                    if(next!=group){Heading(next);group=next;}
                    MatchRow(m);
                }
            }
            content.ResumeLayout();
        }catch(Exception e){
            if(page!="matches"||token!=viewVersion)return;
            SetConnection(false);content.Controls.Clear();DateFilter();
            Message("Serverlə əlaqə alınmadı: "+e.Message,true);
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
        var p=CardPanel(94);
        var home=Txt(Team(m,"home"),12,true);home.SetBounds(18,12,240,38);home.Anchor=AnchorStyles.Top|AnchorStyles.Left;p.Controls.Add(home);
        var away=Txt(Team(m,"away"),12,true);away.SetBounds(18,47,240,34);p.Controls.Add(away);
        var score=Txt(Score(m),19,true,Ink);score.SetBounds(272,23,165,42);p.Controls.Add(score);
        var state=Txt(saved?"Saxlanmış nəticə · canlı deyil":Status(m),10,false,Val(m,"state")=="live"?Accent:Muted);
        state.SetBounds(448,22,170,43);p.Controls.Add(state);
        string id=Val(m,"id");
        var fav=NewButton(favoriteSnapshots.ContainsKey(id)?"★":"☆",Raised,Accent,50);
        fav.Anchor=AnchorStyles.Right|AnchorStyles.Top;fav.SetBounds(p.Width-64,24,46,40);
        p.Controls.Add(fav);p.SizeChanged+=(_,_)=>fav.Left=p.Width-64;
        fav.Click+=(_,_)=>{
            if(favoriteSnapshots.ContainsKey(id))favoriteSnapshots.Remove(id);
            else favoriteSnapshots[id]=m.GetRawText();
            SaveFavorites();fav.Text=favoriteSnapshots.ContainsKey(id)?"★":"☆";
        };
        p.Cursor=Cursors.Hand;
        EventHandler open=(_,_)=>{openedMatch=m.Clone();hasOpenedMatch=true;page="details";Render();};
        foreach(Control x in p.Controls)if(x!=fav)x.Click+=open;
        p.Click+=open;
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
            var name=Txt(Val(p,"name","—"),24,true,Accent);name.SetBounds(22,10,610,52);header.Controls.Add(name);
            var kind=Txt(Val(p,"kind")+" · "+Val(p,"country"),12,false,Muted);kind.SetBounds(22,70,610,30);header.Controls.Add(kind);
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
        }catch(Exception e){if(page=="profile"&&token==viewVersion){content.Controls.Clear();Message("Profil açılmadı: "+e.Message,true);}}
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
                Heading("Statistika");
                foreach(var ev in stats)Message(Val(ev,"name",Val(ev,"label"))+": "+Val(ev,"home",Val(ev,"homeValue","—"))+"  :  "+Val(ev,"away",Val(ev,"awayValue","—")));
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
    private void ShowTactics(){
        var panel=CardPanel(75);
        var t=Txt("Düzülüş",12,true);t.SetBounds(18,16,110,40);panel.Controls.Add(t);
        var select=new ComboBox{DropDownStyle=ComboBoxStyle.DropDownList,BackColor=Raised,ForeColor=Ink,Width=200};
        select.Items.AddRange(formations.Cast<object>().ToArray());
        select.SelectedIndex=formation;select.SetBounds(135,17,200,41);panel.Controls.Add(select);
        var field=CardPanel(570);
        var pitch=new PitchPanel {Dock=DockStyle.Fill,Formation=formations[formation]};
        field.Controls.Add(pitch);
        select.SelectedIndexChanged+=(_,_)=>{formation=select.SelectedIndex;pitch.Formation=formations[formation];pitch.Invalidate();};
        Message("Bu, yerli/native taktika lövhəsidir. Hazırda düzülüş seçimini dəstəkləyir; heyət adları mənbə olmadan uydurulmur.");
    }
    private async Task ShowSettings(){
        Heading("Proqram məlumatı");
        Message("MATCHLAB AZ Native v0.9.30 · Windows Forms. Brauzer və WebView işlətmir.");
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

public sealed class PitchPanel : Panel
{
    public string Formation {get;set;}="4-3-3";
    public PitchPanel(){DoubleBuffered=true;BackColor=Color.FromArgb(20,86,66);}
    protected override void OnPaint(PaintEventArgs e){
        base.OnPaint(e);
        var g=e.Graphics;
        g.SmoothingMode=System.Drawing.Drawing2D.SmoothingMode.AntiAlias;
        float x=30,y=22,w=Math.Max(280,Width-60),h=Math.Max(450,Height-44);
        using var line=new Pen(Color.FromArgb(145,215,211,211),2);
        using var white=new SolidBrush(Color.FromArgb(245,250,240));
        using var green=new SolidBrush(Color.FromArgb(25,107,76));
        g.FillRectangle(green,x,y,w,h);
        g.DrawRectangle(line,x,y,w,h);
        g.DrawLine(line,x,y+h/2,x+w,y+h/2);
        g.DrawEllipse(line,x+w/2-52,y+h/2-52,104,104);
        g.DrawRectangle(line,x+w*.22f,y,w*.56f,h*.17f);
        g.DrawRectangle(line,x+w*.22f,y+h-h*.17f,w*.56f,h*.17f);
        string[] pieces=Formation.Split('-');
        var layers=new List<int>{1};layers.AddRange(pieces.Select(z=>int.TryParse(z,out int n)?n:0));
        int number=1;
        for(int r=0;r<layers.Count;r++){
            int count=layers[r];
            float py=y+h-54-r*(h-112)/(layers.Count-1f);
            for(int col=0;col<count;col++){
                float px=x+((col+1f)/(count+1f))*w;
                using var circle=new SolidBrush(Color.FromArgb(153,236,116));
                g.FillEllipse(circle,px-18,py-18,36,36);
                string n=(number++).ToString();
                using var f=new Font("Segoe UI Semibold",10);
                var ts=g.MeasureString(n,f);
                g.DrawString(n,f,Brushes.Black,px-ts.Width/2,py-ts.Height/2);
            }
        }
    }
}
