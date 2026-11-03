using System;
using System.IO;
using System.Media;
using System.Threading.Tasks;

namespace MATCHLABAZ;

/// <summary>Original synthesised short notification themes. No copyrighted audio files.</summary>
public static class MatchlabAudio
{
    private static readonly object Gate = new();
    private static readonly System.Collections.Generic.Dictionary<string,int[]> Themes = new()
    {
        ["goals"] = new[] { 523, 659, 784, 1047 },
        ["assists"] = new[] { 587, 740, 880 },
        ["penalties"] = new[] { 440, 440, 659 },
        ["cards"] = new[] { 523, 392, 262 },
        ["yellow_cards"] = new[] { 523, 440 },
        ["corners"] = new[] { 587, 784 },
        ["lineups"] = new[] { 392, 523, 659 },
        ["final"] = new[] { 659, 523, 392 },
        ["kickoff"] = new[] { 440, 554, 659 }
    };
    public static void Play(string category,int volume=85)
    {
        volume=Math.Clamp(volume,0,100);
        if(volume==0)return;
        var notes=Themes.TryGetValue(category,out var found)?found:new[]{523,659};
        _=Task.Run(()=>{
            try {
                lock(Gate) {
                    using var wave=CreateWave(notes,volume);
                    using var player=new SoundPlayer(wave);
                    player.PlaySync();
                }
            } catch { /* Audio device may be muted/unavailable. */ }
        });
    }
    private static MemoryStream CreateWave(int[] notes,int volume)
    {
        const int sampleRate=22050;
        const int ms=145;
        int perNote=sampleRate*ms/1000;
        int samples=notes.Length*perNote;
        var stream=new MemoryStream(44+samples*2);
        using(var writer=new BinaryWriter(stream,System.Text.Encoding.UTF8,true)){
            writer.Write(System.Text.Encoding.ASCII.GetBytes("RIFF"));writer.Write(36+samples*2);
            writer.Write(System.Text.Encoding.ASCII.GetBytes("WAVEfmt "));writer.Write(16);
            writer.Write((short)1);writer.Write((short)1);writer.Write(sampleRate);
            writer.Write(sampleRate*2);writer.Write((short)2);writer.Write((short)16);
            writer.Write(System.Text.Encoding.ASCII.GetBytes("data"));writer.Write(samples*2);
            for(int i=0;i<samples;i++){
                int note=i/perNote, at=i%perNote;
                double seconds=(double)at/sampleRate;
                double envelope=Math.Min(1,at/350.0)*Math.Min(1,(perNote-at)/1600.0);
                double tone=Math.Sin(2*Math.PI*notes[note]*seconds)+.20*Math.Sin(4*Math.PI*notes[note]*seconds);
                short sample=(short)Math.Clamp(tone*envelope*(volume/100.0)*22000,-32768,32767);
                writer.Write(sample);
            }
        }
        stream.Position=0;return stream;
    }
}
