using System;
using System.Collections.Generic;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.Diagnostics;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text;
using System.Text.Json;
using System.Windows.Forms;

namespace MATCHLABAZ;

/// <summary>Native, locally saved football tactics editor. These are user-created plans, not verified match lineups.</summary>
public sealed class PitchPanel : Panel
{
    private const int SquadSize = 11;
    private string formation = "4-3-3";
    private float[][] positions = new float[SquadSize][];
    private string[] playerNames = new string[SquadSize];
    private string[] numbers = new string[SquadSize];
    private List<float[]> arrows = new();
    private int dragging = -1;
    private PointF? arrowStart;
    private bool arrowMode;
    private bool gridVisible;
    private bool changed;
    private readonly Stopwatch playback = new();
    private readonly System.Windows.Forms.Timer playbackTimer = new() { Interval = 25 };
    private bool playing;
    public bool IsPlaying => playing;
    public void TogglePlayback()
    {
        if(playing){StopPlayback();return;}
        if(arrows.Count==0){MessageBox.Show("Əvvəlcə ən azı bir hərəkət oxu çək.","MATCHLAB AZ");return;}
        playing=true;playback.Restart();playbackTimer.Start();Invalidate();
    }
    private void StopPlayback()
    {
        playing=false;playbackTimer.Stop();playback.Reset();Invalidate();
    }
    public void ExportPng(string filename)
    {
        using var canvas=new Bitmap(Math.Max(500,Width),Math.Max(450,Height));
        DrawToBitmap(canvas,new Rectangle(0,0,canvas.Width,canvas.Height));
        canvas.Save(filename,System.Drawing.Imaging.ImageFormat.Png);
    }

    private sealed class SavedPlan
    {
        public float[][] Positions { get; set; } = Array.Empty<float[]>();
        public string[] Names { get; set; } = Array.Empty<string>();
        public string[] Numbers { get; set; } = Array.Empty<string>();
        public List<float[]> Arrows { get; set; } = new();
    }
    public PitchPanel()
    {
        DoubleBuffered = true;
        BackColor = Color.FromArgb(20, 86, 66);
        playbackTimer.Tick+=(_,_)=>{
            if(!IsDisposed&&playing)Invalidate();
            else playbackTimer.Stop();
        };
        LoadPlan();
    }
    protected override void Dispose(bool disposing)
    {
        if(disposing)playbackTimer.Dispose();
        base.Dispose(disposing);
    }
    public string Formation
    {
        get => formation;
        set { StopPlayback(); formation = value; arrowStart = null; LoadPlan(); Invalidate(); }
    }
    public bool ArrowMode
    {
        get => arrowMode;
        set { arrowMode = value; arrowStart = null; Cursor = value ? Cursors.Cross : Cursors.Hand; Invalidate(); }
    }
    public bool ShowGrid
    {
        get => gridVisible;
        set { gridVisible = value; Invalidate(); }
    }
    private string PlanPath => Path.Combine(
        Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
        "MATCHLAB_AZ", "tactics_" + formation.Replace("-", "_") + ".json");
    private static float Clamp(float x) => Math.Max(0.05f, Math.Min(.95f, x));
    private void Defaults()
    {
        var layers = new List<int> { 1 };
        layers.AddRange(formation.Split('-').Select(x => int.TryParse(x, out var v) ? v : 0));
        int n = 0;
        for (int row = 0; row < layers.Count && n < SquadSize; row++)
        {
            for (int col = 0; col < layers[row] && n < SquadSize; col++)
            {
                positions[n++] = new[] { (col + 1f) / (layers[row] + 1f), .88f - row * (.75f / (layers.Count - 1)) };
            }
        }
        for (int i = 0; i < SquadSize; i++)
        {
            positions[i] ??= new[] { .5f, .5f };
            playerNames[i] = "";
            numbers[i] = (i + 1).ToString(CultureInfo.InvariantCulture);
        }
        arrows.Clear();
    }
    private void LoadPlan()
    {
        Defaults();
        try
        {
            if (!File.Exists(PlanPath)) return;
            var plan = JsonSerializer.Deserialize<SavedPlan>(File.ReadAllText(PlanPath));
            if (plan == null) return;
            for (int i = 0; i < SquadSize; i++)
            {
                if (i < plan.Positions.Length && plan.Positions[i]?.Length == 2)
                    positions[i] = new[] { Clamp(plan.Positions[i][0]), Clamp(plan.Positions[i][1]) };
                if (i < plan.Names.Length) playerNames[i] = (plan.Names[i] ?? "").Trim();
                if (i < plan.Numbers.Length) numbers[i] = (plan.Numbers[i] ?? (i + 1).ToString()).Trim();
            }
            arrows = (plan.Arrows ?? new()).Where(a => a != null && a.Length == 4).Take(80)
                .Select(a => a.Select(Clamp).ToArray()).ToList();
        }
        catch (Exception) { /* Corrupt local plan: defaults stay usable. */ }
    }
    private void SavePlan()
    {
        try
        {
            Directory.CreateDirectory(Path.GetDirectoryName(PlanPath)!);
            File.WriteAllText(PlanPath, JsonSerializer.Serialize(new SavedPlan
            {
                Positions = positions, Names = playerNames, Numbers = numbers, Arrows = arrows
            }));
        }
        catch (IOException e) { MessageBox.Show("Taktika saxlanmadı: " + e.Message, "MATCHLAB AZ"); }
    }
    public void ResetPlan() { StopPlayback(); Defaults(); SavePlan(); Invalidate(); }
    public void ClearArrows() { StopPlayback(); arrows.Clear(); arrowStart = null; SavePlan(); Invalidate(); }
    public void ReplacePlayer(int index, string newName)
    {
        if (index < 0 || index >= SquadSize || string.IsNullOrWhiteSpace(newName)) return;
        playerNames[index] = newName.Trim().Length > 30 ? newName.Trim()[..30] : newName.Trim();
        SavePlan(); Invalidate();
    }
    public string ExportText()
    {
        var sb = new StringBuilder("MATCHLAB AZ — Taktika " + formation);
        for (int i = 0; i < SquadSize; i++)
            sb.Append("\n").Append(numbers[i]).Append(". ")
                .Append(string.IsNullOrWhiteSpace(playerNames[i]) ? "Mövqe " + (i + 1) : playerNames[i]);
        sb.Append("\nHərəkət oxları: ").Append(arrows.Count)
          .Append("\nŞəxsi taktika planı — real matç heyəti kimi təqdim edilmir.");
        return sb.ToString();
    }
    private RectangleF Field => new(30, 22, Math.Max(180, Width - 60), Math.Max(260, Height - 44));
    private PointF Position(int index)
    {
        var f = Field;
        return new(f.Left + positions[index][0] * f.Width, f.Top + positions[index][1] * f.Height);
    }
    private PointF Normalized(Point p)
    {
        var f = Field;
        return new(Clamp((p.X - f.Left) / f.Width), Clamp((p.Y - f.Top) / f.Height));
    }
    protected override void OnMouseDown(MouseEventArgs e)
    {
        base.OnMouseDown(e);
        if (e.Button != MouseButtons.Left) return;
        if(playing)StopPlayback();
        if (arrowMode)
        {
            var p = Normalized(e.Location);
            if (arrowStart == null) arrowStart = p;
            else
            {
                arrows.Add(new[] { arrowStart.Value.X, arrowStart.Value.Y, p.X, p.Y });
                arrowStart = null; SavePlan();
            }
            Invalidate(); return;
        }
        dragging = -1;
        for (int i = SquadSize - 1; i >= 0; i--)
        {
            var p = Position(i);
            if (Math.Pow(e.X - p.X, 2) + Math.Pow(e.Y - p.Y, 2) <= 28 * 28)
            { dragging = i; break; }
        }
        changed = false;
    }
    protected override void OnMouseMove(MouseEventArgs e)
    {
        base.OnMouseMove(e);
        if (dragging < 0 || e.Button != MouseButtons.Left || arrowMode) return;
        var pt = Normalized(e.Location);
        positions[dragging] = new[] { pt.X, pt.Y }; changed = true; Invalidate();
    }
    protected override void OnMouseUp(MouseEventArgs e)
    {
        base.OnMouseUp(e);
        if (dragging >= 0 && changed) SavePlan();
        dragging = -1;
    }
    protected override void OnMouseDoubleClick(MouseEventArgs e)
    {
        base.OnMouseDoubleClick(e);
        if (arrowMode) return;
        for (int i = SquadSize - 1; i >= 0; i--)
        {
            var p = Position(i);
            if (Math.Pow(e.X - p.X, 2) + Math.Pow(e.Y - p.Y, 2) > 28 * 28) continue;
            int player = i;
            using var dialog = new Form { Text = "Oyunçu " + (i + 1), Size = new Size(370, 195), StartPosition = FormStartPosition.CenterParent };
            var name = new TextBox { Left = 15, Top = 14, Width = 325, PlaceholderText = "Oyunçunun adı", Text = playerNames[i] };
            var number = new TextBox { Left = 15, Top = 53, Width = 325, PlaceholderText = "Forma nömrəsi", Text = numbers[i] };
            var ok = new Button { Text = "Saxla", Left = 225, Top = 95, Width = 115, DialogResult = DialogResult.OK };
            dialog.Controls.AddRange(new Control[] { name, number, ok });
            dialog.AcceptButton = ok;
            if (dialog.ShowDialog(FindForm()) == DialogResult.OK)
            {
                playerNames[player] = name.Text.Trim().Length > 30 ? name.Text.Trim()[..30] : name.Text.Trim();
                numbers[player] = string.IsNullOrWhiteSpace(number.Text) ? (player + 1).ToString() : number.Text.Trim()[..Math.Min(3, number.Text.Trim().Length)];
                SavePlan(); Invalidate();
            }
            break;
        }
    }
    protected override void OnPaint(PaintEventArgs e)
    {
        base.OnPaint(e);
        var g = e.Graphics;
        g.SmoothingMode = SmoothingMode.AntiAlias;
        var f = Field;
        using var darkGreen = new SolidBrush(Color.FromArgb(23, 96, 72));
        using var line = new Pen(Color.FromArgb(165, 236, 246, 242), 2);
        using var arrowPen = new Pen(Color.FromArgb(255, 210, 100), 3) { EndCap = LineCap.ArrowAnchor };
        g.FillRectangle(darkGreen, f);
        g.DrawRectangle(line, f.X, f.Y, f.Width, f.Height);
        g.DrawLine(line, f.Left, f.Top + f.Height / 2, f.Right, f.Top + f.Height / 2);
        g.DrawEllipse(line, f.Left + f.Width / 2 - 44, f.Top + f.Height / 2 - 44, 88, 88);
        g.DrawRectangle(line, f.Left + f.Width * .22f, f.Top, f.Width * .56f, f.Height * .17f);
        g.DrawRectangle(line, f.Left + f.Width * .22f, f.Bottom - f.Height * .17f, f.Width * .56f, f.Height * .17f);
        if (gridVisible)
        {
            using var grid = new Pen(Color.FromArgb(65, 240, 255, 255));
            for (int i = 1; i < 6; i++) g.DrawLine(grid, f.Left + f.Width * i / 6, f.Top, f.Left + f.Width * i / 6, f.Bottom);
            for (int i = 1; i < 10; i++) g.DrawLine(grid, f.Left, f.Top + f.Height * i / 10, f.Right, f.Top + f.Height * i / 10);
        }
        foreach (var arrow in arrows)
            g.DrawLine(arrowPen, f.Left + arrow[0] * f.Width, f.Top + arrow[1] * f.Height,
                f.Left + arrow[2] * f.Width, f.Top + arrow[3] * f.Height);
        if(playing&&arrows.Count>0)
        {
            // Visual rehearsal of the user's own paths, not tracked player movement.
            var t=(float)(playback.Elapsed.TotalSeconds % (arrows.Count*1.2))/1.2f;
            int index=Math.Min(arrows.Count-1,(int)t);
            float fraction=t-index;
            var a=arrows[index];
            float x=f.Left+(a[0]+(a[2]-a[0])*fraction)*f.Width;
            float y=f.Top+(a[1]+(a[3]-a[1])*fraction)*f.Height;
            using var glow=new SolidBrush(Color.FromArgb(110,255,212,83));
            using var dot=new SolidBrush(Color.FromArgb(255,244,120));
            g.FillEllipse(glow,x-18,y-18,36,36);
            g.FillEllipse(dot,x-8,y-8,16,16);
        }
        if (arrowStart is PointF start)
        {
            using var brush = new SolidBrush(Color.Gold);
            g.FillEllipse(brush, f.Left + start.X * f.Width - 6, f.Top + start.Y * f.Height - 6, 12, 12);
        }
        using var circle = new SolidBrush(Color.FromArgb(153, 236, 116));
        using var numberFont = new Font("Segoe UI Semibold", 10);
        using var nameFont = new Font("Segoe UI Semibold", 9);
        for (int i = 0; i < SquadSize; i++)
        {
            var p = Position(i);
            g.FillEllipse(circle, p.X - 17, p.Y - 17, 34, 34);
            var size = g.MeasureString(numbers[i], numberFont);
            g.DrawString(numbers[i], numberFont, Brushes.Black, p.X - size.Width / 2, p.Y - size.Height / 2);
            if (!string.IsNullOrWhiteSpace(playerNames[i]))
            {
                var text = playerNames[i].Length > 16 ? playerNames[i][..16] + "…" : playerNames[i];
                var measure = g.MeasureString(text, nameFont);
                using var pill = new SolidBrush(Color.FromArgb(220, 11, 28, 40));
                g.FillRectangle(pill, p.X - measure.Width / 2 - 5, p.Y + 21, measure.Width + 10, 21);
                g.DrawString(text, nameFont, Brushes.White, p.X - measure.Width / 2, p.Y + 23);
            }
        }
    }
}
