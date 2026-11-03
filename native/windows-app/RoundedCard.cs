using System;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.Windows.Forms;

namespace MATCHLABAZ;

/// <summary>Double-buffered rounded dark card used across native Windows dashboards.</summary>
public sealed class RoundedCard : Panel
{
    public int CornerRadius { get; set; } = 16;
    public RoundedCard()
    {
        DoubleBuffered = true;
        ResizeRedraw = true;
        BackColor = Color.FromArgb(21,38,55);
    }
    private GraphicsPath Outline(Rectangle area)
    {
        int radius = Math.Min(CornerRadius * 2,Math.Min(area.Width,area.Height));
        var path = new GraphicsPath();
        if(radius < 2){path.AddRectangle(area);return path;}
        path.AddArc(area.Left,area.Top,radius,radius,180,90);
        path.AddArc(area.Right-radius,area.Top,radius,radius,270,90);
        path.AddArc(area.Right-radius,area.Bottom-radius,radius,radius,0,90);
        path.AddArc(area.Left,area.Bottom-radius,radius,radius,90,90);
        path.CloseFigure();
        return path;
    }
    protected override void OnPaintBackground(PaintEventArgs e)
    {
        if(Parent==null){base.OnPaintBackground(e);return;}
        e.Graphics.Clear(Parent.BackColor);
        var bounds = new Rectangle(0,0,Math.Max(1,Width-1),Math.Max(1,Height-1));
        using var path=Outline(bounds);
        e.Graphics.SmoothingMode=SmoothingMode.AntiAlias;
        using var bg=new SolidBrush(BackColor);
        using var border=new Pen(Color.FromArgb(36,74,88),1);
        e.Graphics.FillPath(bg,path);
        e.Graphics.DrawPath(border,path);
    }
}
