using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Reflection;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;
using System.Windows.Forms;
using Microsoft.Web.WebView2.Core;
using Microsoft.Web.WebView2.WinForms;
namespace MATCHLABAZ;

internal static class Program
{
    [STAThread]
    static int Main(string[] args)
    {
        if(args.Contains("--self-test",StringComparer.OrdinalIgnoreCase))
            return HtmlApp.CheckAssets()?0:3;
        ApplicationConfiguration.Initialize();
        Application.Run(new HtmlApp());
        return 0;
    }
}
public sealed class HtmlApp:Form
{
    const string Origin="https://matchlab.local";
    const string Backend="https://matchlab-az-online.onrender.com";
    static readonly HttpClient Client=new(){Timeout=TimeSpan.FromSeconds(55)};
    static readonly Dictionary<string,(string Key,string Mime)> Assets=new(StringComparer.OrdinalIgnoreCase)
    {
        ["/"]=("ML.index.html","text/html"),
        ["/index.html"]=("ML.index.html","text/html"),
        ["/app.js"]=("ML.app.js","text/javascript"),
        ["/styles.css"]=("ML.styles.css","text/css"),
        ["/catalog.js"]=("ML.catalog.js","text/javascript"),
        ["/featured_media.js"]=("ML.featured_media.js","text/javascript"),
        ["/coach_tactics.js"]=("ML.coach_tactics.js","text/javascript"),
        ["/assets/icon.svg"]=("ML.assets.icon.svg","image/svg+xml"),
        ["/shell.css"]=("ML.shell.css","text/css")
    };
    readonly WebView2 browser=new(){Dock=DockStyle.Fill,DefaultBackgroundColor=Color.FromArgb(8,14,25)};
    readonly Label error=new(){Dock=DockStyle.Fill,TextAlign=ContentAlignment.MiddleCenter,
        ForeColor=Color.White,BackColor=Color.FromArgb(8,14,25),Visible=false,
        Font=new Font("Segoe UI",14),Padding=new Padding(24)};
    public HtmlApp()
    {
        Text="MATCHLAB AZ — v0.9.40 · HTML Desktop";
        StartPosition=FormStartPosition.CenterScreen;
        MinimumSize=new Size(760,540);Size=new Size(1280,820);
        BackColor=Color.FromArgb(8,14,25);
        Controls.Add(browser);Controls.Add(error);
        Shown+=async (_,_)=>await Start();
    }
    public static bool CheckAssets()
    {
        var ass=Assembly.GetExecutingAssembly();
        foreach(var asset in Assets.Values.DistinctBy(v=>v.Key))
        {
            using var stream=ass.GetManifestResourceStream(asset.Key);
            if(stream==null||stream.Length<50)return false;
        }
        return true;
    }
    async Task Start()
    {
        try
        {
            if(!CheckAssets())throw new IOException("HTML faylları EXE daxilində tapılmadı.");
            string userDir=Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),"MATCHLAB_AZ","WebView2");
            Directory.CreateDirectory(userDir);
            var env=await CoreWebView2Environment.CreateAsync(userDataFolder:userDir);
            await browser.EnsureCoreWebView2Async(env);
            var core=browser.CoreWebView2;
            core.Settings.IsStatusBarEnabled=false;
            core.Settings.AreDevToolsEnabled=false;
            core.Settings.AreDefaultContextMenusEnabled=false;
            core.AddWebResourceRequestedFilter(Origin+"/*",CoreWebView2WebResourceContext.All);
            core.WebResourceRequested+=Request;
            core.NewWindowRequested+=(_,e)=>{e.Handled=true;OpenExternal(e.Uri);};
            core.NavigationStarting+=(_,e)=>{
                if(!e.Uri.StartsWith(Origin+"/",StringComparison.OrdinalIgnoreCase))
                {e.Cancel=true;OpenExternal(e.Uri);}
            };
            core.Navigate(Origin+"/index.html");
        }
        catch(Exception ex)
        {
            error.Text="MATCHLAB AZ açıla bilmədi.\n\nMicrosoft Edge WebView2 Runtime komponentini yoxla.\n\n"+ex.Message;
            error.Visible=true;error.BringToFront();
        }
    }
    static void OpenExternal(string url)
    {
        if(Uri.TryCreate(url,UriKind.Absolute,out var u)&&(u.Scheme=="https"||u.Scheme=="http"))
        {try{Process.Start(new ProcessStartInfo(u.ToString()){UseShellExecute=true});}catch{}}
    }
    void Request(object? sender,CoreWebView2WebResourceRequestedEventArgs e)
    {
        var d=e.GetDeferral();
        _=Serve(e,d);
    }
    async Task Serve(CoreWebView2WebResourceRequestedEventArgs e,CoreWebView2Deferral d)
    {
        try
        {
            var uri=new Uri(e.Request.Uri);
            if(uri.Scheme!="https"||uri.Host!="matchlab.local")return;
            if(uri.AbsolutePath.StartsWith("/api/",StringComparison.Ordinal))
            {
                if(e.Request.Method!="GET")
                {Reply(e,403,"application/json",Encoding.UTF8.GetBytes("{\"error\":\"Bu əməliyyat bağlıdır\"}"));return;}
                try
                {
                    using var response=await Client.GetAsync(Backend+uri.PathAndQuery,HttpCompletionOption.ResponseHeadersRead);
                    var bytes=await response.Content.ReadAsByteArrayAsync();
                    if(bytes.Length>8000000)throw new IOException("API response too large");
                    Reply(e,(int)response.StatusCode,"application/json",bytes);
                }
                catch(Exception ex)
                {
                    Reply(e,503,"application/json",Encoding.UTF8.GetBytes(
                        JsonSerializer.Serialize(new{available=false,error="Serverə bağlantı yoxdur: "+ex.Message})));
                }
                return;
            }
            if(!Assets.TryGetValue(uri.AbsolutePath,out var asset))
            {Reply(e,404,"text/plain",Encoding.UTF8.GetBytes("Not Found"));return;}
            using var stream=Assembly.GetExecutingAssembly().GetManifestResourceStream(asset.Key);
            if(stream==null){Reply(e,500,"text/plain",Encoding.UTF8.GetBytes("Asset missing"));return;}
            using var buffer=new MemoryStream();
            stream.CopyTo(buffer);
            byte[] bytes2=buffer.ToArray();
            if(uri.AbsolutePath is "/" or "/index.html")
                bytes2=Encoding.UTF8.GetBytes(Encoding.UTF8.GetString(bytes2).Replace(
                    "</head>","<link rel=\"stylesheet\" href=\"shell.css\"></head>",StringComparison.OrdinalIgnoreCase));
            Reply(e,200,asset.Mime,bytes2);
        }
        catch(Exception ex)
        {
            Reply(e,500,"application/json",Encoding.UTF8.GetBytes(JsonSerializer.Serialize(new{error=ex.Message})));
        }
        finally{d.Complete();}
    }
    void Reply(CoreWebView2WebResourceRequestedEventArgs e,int code,string mime,byte[] content)
    {
        e.Response=browser.CoreWebView2.Environment.CreateWebResourceResponse(
            new MemoryStream(content),code,code<400?"OK":"Unavailable",
            "Content-Type: "+mime+"; charset=utf-8\r\nCache-Control: no-store\r\nX-Content-Type-Options: nosniff");
    }
}
