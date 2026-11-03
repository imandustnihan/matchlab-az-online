using System;
using System.Diagnostics;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.Windows.Forms;

namespace MATCHLABAZ;

/// <summary>Original green MATCHLAB AZ M-ball identity from assets/icon.svg, drawn natively.</summary>
internal static class BrandArtwork
{
    public static void Draw(Graphics g, RectangleF bounds)
    {
        var state = g.Save();
        g.SmoothingMode = SmoothingMode.AntiAlias;
        g.TranslateTransform(bounds.Left, bounds.Top);
        g.ScaleTransform(bounds.Width / 64f, bounds.Height / 64f);
        using var shape = new GraphicsPath();
        shape.AddArc(0, 0, 32, 32, 180, 90);
        shape.AddArc(32, 0, 32, 32, 270, 90);
        shape.AddArc(32, 32, 32, 32, 0, 90);
        shape.AddArc(0, 32, 32, 32, 90, 90);
        shape.CloseFigure();
        using var green = new SolidBrush(Color.FromArgb(181,245,104));
        using var dark = new SolidBrush(Color.FromArgb(19,44,32));
        g.FillPath(green, shape);
        using var pen = new Pen(Color.FromArgb(19,44,32), 8)
        {
            LineJoin = LineJoin.Round, StartCap = LineCap.Round, EndCap = LineCap.Round
        };
        g.DrawLines(pen, new[] {new PointF(10,40),new PointF(21,17),new PointF(32,33),new PointF(43,17),new PointF(54,40)});
        g.FillEllipse(dark,41,39,16,16);
        g.Restore(state);
    }
}

/// <summary>Native lightweight, non-network splash animation; it does not pretend to fetch live scores.</summary>
public sealed class SplashForm : Form
{
    private readonly Stopwatch animation = new();
    private readonly System.Windows.Forms.Timer ticker = new() { Interval = 25 };
    private float phase;
    public SplashForm()
    {
        Text = "MATCHLAB AZ";
        ClientSize = new Size(580, 320);
        FormBorderStyle = FormBorderStyle.None;
        StartPosition = FormStartPosition.CenterScreen;
        ShowInTaskbar = false;
        DoubleBuffered = true;
        BackColor = Color.FromArgb(9,18,30);
        ticker.Tick += (_,_) =>
        {
            var milliseconds = animation.ElapsedMilliseconds;
            phase = Math.Clamp(milliseconds / 1100f, 0f, 1f);
            if(milliseconds > 920)
            {
                Opacity = Math.Max(0, 1 - (milliseconds - 920) / 240d);
            }
            if(milliseconds >= 1170){ticker.Stop();Close();return;}
            Invalidate();
        };
    }
    protected override void OnShown(EventArgs e)
    {
        base.OnShown(e);
        animation.Start();ticker.Start();
    }
    protected override void OnPaint(PaintEventArgs e)
    {
        base.OnPaint(e);
        var g = e.Graphics;g.SmoothingMode = SmoothingMode.AntiAlias;
        using(var bg = new LinearGradientBrush(ClientRectangle,
            Color.FromArgb(10,21,34), Color.FromArgb(17,44,46), 25f))
            g.FillRectangle(bg,ClientRectangle);
        using(var glow = new SolidBrush(Color.FromArgb(20,126,230,131)))
            g.FillEllipse(glow, 295, -190, 500, 500);
        using(var border = new Pen(Color.FromArgb(50,143,231,154)))
            g.DrawRectangle(border, 1, 1, Width - 3, Height - 3);
        BrandArtwork.Draw(g,new RectangleF(36,77,115,115));
        using var title = new Font("Segoe UI Semibold",30,FontStyle.Bold);
        using var sub = new Font("Segoe UI",12,FontStyle.Regular);
        using var tiny = new Font("Segoe UI",9);
        using var white = new SolidBrush(Color.FromArgb(242,249,253));
        using var lime = new SolidBrush(Color.FromArgb(181,245,104));
        using var muted = new SolidBrush(Color.FromArgb(174,196,205));
        g.DrawString("MATCHLAB",title,white,174,79);
        g.DrawString("AZ",title,lime,445,79);
        g.DrawString("FUTBOL MƏRKƏZİ",sub,muted,180,140);
        g.DrawString("Windows · Native · v0.9.55",tiny,muted,180,181);
        g.DrawString("Tətbiq açılır",sub,white,36,243);
        using var track = new SolidBrush(Color.FromArgb(48,76,88));
        using var progress = new SolidBrush(Color.FromArgb(154,239,117));
        g.FillRectangle(track,36,281,508,6);
        // Smooth visual intro indicator; server loading is handled separately in the application.
        float eased = 1 - (float)Math.Pow(1 - phase,3);
        g.FillRectangle(progress,36,281,508*eased,6);
    }
    protected override void OnFormClosed(FormClosedEventArgs e)
    {
        ticker.Stop();ticker.Dispose();
        base.OnFormClosed(e);
    }
}
