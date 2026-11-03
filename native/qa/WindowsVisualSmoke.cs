using System;
using System.Collections.Generic;
using System.Drawing;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Text.Json;
using System.Threading;
using System.Windows.Forms;
using MATCHLABAZ;

namespace MatchlabQA;

public static class QaProgram
{
    private static readonly BindingFlags PrivateInstance=BindingFlags.NonPublic|BindingFlags.Instance;
    private static readonly List<string> Passed=new();
    private static string OutDir=Path.Combine(Environment.CurrentDirectory,"qa-artifacts","windows");
    private static void Check(bool condition,string name)
    {
        if(!condition)throw new InvalidOperationException("QA FAILED: "+name);
        Passed.Add(name);
        Console.WriteLine("[PASS] "+name);
    }
    private static IEnumerable<Control> Walk(Control root)
    {
        foreach(Control control in root.Controls){
            yield return control;
            foreach(var child in Walk(control))yield return child;
        }
    }
    private static bool HasText(Control root,string fragment)
        => Walk(root).Any(c=>c.Text?.Contains(fragment,StringComparison.OrdinalIgnoreCase)==true);
    private static T Field<T>(object obj,string name)
        => (T)(obj.GetType().GetField(name,PrivateInstance)?.GetValue(obj)
            ??throw new InvalidOperationException("Missing field: "+name));
    private static void SetField(object obj,string name,object value)
        => (obj.GetType().GetField(name,PrivateInstance)
             ??throw new InvalidOperationException("Missing field: "+name)).SetValue(obj,value);
    private static void RenderPage(MatchlabForm form,string page)
    {
        SetField(form,"page",page);
        var method=typeof(MatchlabForm).GetMethod("Render",PrivateInstance)
            ??throw new InvalidOperationException("Render method not found");
        method.Invoke(form,null);
        Application.DoEvents();
        Thread.Sleep(120);
        Application.DoEvents();
    }
    private static void Shot(MatchlabForm form,string filename)
    {
        Application.DoEvents();
        using var bitmap=new Bitmap(Math.Max(940,form.Width),Math.Max(640,form.Height));
        form.DrawToBitmap(bitmap,new Rectangle(0,0,bitmap.Width,bitmap.Height));
        var output=Path.Combine(OutDir,filename);
        bitmap.Save(output,System.Drawing.Imaging.ImageFormat.Png);
        Check(new FileInfo(output).Length>6000,filename+" screenshot not blank");
    }
    private static float[][] ClonePositions(PitchPanel pitch)
    {
        var raw=Field<float[][]>(pitch,"positions");
        return raw.Select(a=>a.ToArray()).ToArray();
    }
    private static bool PositionsEqual(float[][] a,float[][] b)
       => a.Length==b.Length&&a.Zip(b).All(pair=>
            pair.First.Length==pair.Second.Length&&
            pair.First.Zip(pair.Second).All(x=>Math.Abs(x.First-x.Second)<.001f));
    [STAThread]
    public static int Main()
    {
        Directory.CreateDirectory(OutDir);
        MatchlabForm? form=null;
        try{
            ApplicationConfiguration.Initialize();
            form=new MatchlabForm();
            form.Show();
            Application.DoEvents();
            Thread.Sleep(250);
            Application.DoEvents();
            Check(form.WindowState==FormWindowState.Maximized,"Windows opens maximized");
            Check(form.Width>=940&&form.Height>=640,"Window meets minimum usable size");
            var heading=Walk(form).OfType<Label>().FirstOrDefault(
                l=>l.Text=="Bu gün futbol");
            Check(heading!=null,"Football hero heading present");
            Check(heading!.ClientSize.Height>=TextRenderer.MeasureText(
                heading.Text,heading.Font,new Size(2000,100),
                TextFormatFlags.NoPadding).Height,
                "Football hero title is not vertically clipped");
            Check(Walk(form).OfType<PictureBox>().Any(p=>p.Image!=null),
                "Original rendered MATCHLAB M-ball logo present");
            Shot(form,"01_matches.png");

            string cacheFolder=Path.Combine(
                Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
                "MATCHLAB_AZ");
            Directory.CreateDirectory(cacheFolder);
            string localHistory=Path.Combine(cacheFolder,"history_eng_1_2025-26.json");
            File.WriteAllText(localHistory,JsonSerializer.Serialize(new{
                available=true,bundle=true,complete=true,live=false,
                leagueName="Premier League",season="2025-26",count=2,
                items=new object[]{
                    new{home="Liverpool FC",away="AFC Bournemouth",date="2025-08-15",
                        time="20:00",round="Matchday 1",resultRecorded=true,homeScore=4,awayScore=2},
                    new{home="Real Madrid",away="Valencia",date="2025-08-16",
                        time="20:00",round="Matchday 2",resultRecorded=true,homeScore=2,awayScore=1}
                }
            }));
            SetField(form,"historyLeague","eng.1");
            SetField(form,"historySeason","2025-26");
            SetField(form,"historyTeam","Liverpool");
            var watch=System.Diagnostics.Stopwatch.StartNew();
            RenderPage(form,"history");watch.Stop();
            Check(HasText(form,"Liverpool FC"),"Cached history matches chosen team");
            Check(!HasText(form,"Real Madrid"),"Cached history filters out other teams");
            Check(watch.ElapsedMilliseconds<3500,
                "Cached history search renders without a server round trip");
            Shot(form,"02_history_filter.png");
            SetField(form,"historyTeam","Real Madrid");
            RenderPage(form,"history");
            Check(HasText(form,"Real Madrid"),"Second local team search works");
            Shot(form,"03_history_search.png");

            RenderPage(form,"tactics");
            var pitch=Walk(form).OfType<PitchPanel>().FirstOrDefault();
            Check(pitch!=null,"Tactics pitch initialized");
            Check(HasText(form,"Geri al")&&HasText(form,"Güzgü")&&HasText(form,"PNG saxla"),
                "Tactics undo, mirror and PNG controls present");
            var before=ClonePositions(pitch!);
            pitch.MirrorPlan();
            var mirrored=ClonePositions(pitch);
            Check(!PositionsEqual(before,mirrored),"Mirror changes player coordinates");
            pitch.UndoLast();
            Check(PositionsEqual(before,ClonePositions(pitch)),"Undo restores positions");
            var png=Path.Combine(OutDir,"tactics-export.png");
            pitch.ExportPng(png);
            Check(File.Exists(png)&&new FileInfo(png).Length>4000,
                "Tactics exports non-empty PNG");
            Shot(form,"04_tactics.png");

            RenderPage(form,"settings");
            Check(HasText(form,"Yerli keşi təmizlə"),"Safe cache-cleaning setting exists");
            Check(HasText(form,"Yığcam matç kartları"),"Compact card setting exists");
            Check(HasText(form,"Açılışda maksimum"),"Startup window-size option exists");
            Shot(form,"05_settings.png");
            File.WriteAllText(Path.Combine(OutDir,"results.json"),
                JsonSerializer.Serialize(new{platform="Windows 11 hosted runner",passed=Passed,
                    count=Passed.Count,mode="WinForms native control rendering and interaction"},
                    new JsonSerializerOptions{WriteIndented=true}));
            Console.WriteLine("Windows GUI QA completed: "+Passed.Count+" checks.");
            return 0;
        }catch(Exception e){
            File.WriteAllText(Path.Combine(OutDir,"failure.txt"),e.ToString());
            Console.Error.WriteLine(e);
            return 1;
        }finally{form?.Close();form?.Dispose();}
    }
}
