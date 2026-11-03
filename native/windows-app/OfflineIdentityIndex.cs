using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.IO.Compression;
using System.Reflection;
using System.Text;

namespace MATCHLABAZ;

/// <summary>
/// Offline, source-verified 506207-row Reep CC0 identity catalogue.
/// Identities only: never claim current squads, career history, images or
/// match statistics are stored in this index.
/// </summary>
public static class OfflineIdentityIndex
{
    public sealed record Entry(string Id,string Name,string Kind,string Country);
    public static string Normalize(string raw)
    {
        if (string.IsNullOrEmpty(raw)) return "";
        string value=raw.Normalize(NormalizationForm.FormD).ToLowerInvariant();
        var output=new StringBuilder(value.Length);
        foreach(char ch in value){
            if(CharUnicodeInfo.GetUnicodeCategory(ch)==UnicodeCategory.NonSpacingMark)continue;
            output.Append(ch switch {'ə'=>'e','ı'=>'i','ø'=>'o','ł'=>'l','ß'=>'s',_=>ch});
        }
        return string.Join(" ",output.ToString().Split(' ',StringSplitOptions.RemoveEmptyEntries));
    }
    public static List<Entry> Search(Stream compressed,string query,string kind,int max=75)
    {
        var matches=new List<Entry>();
        string needle=Normalize(query);
        if(needle.Length<2||max<=0)return matches;
        var tokens=needle.Split(' ',StringSplitOptions.RemoveEmptyEntries);
        using var unzip=new GZipStream(compressed,CompressionMode.Decompress,leaveOpen:true);
        using var reader=new StreamReader(unzip,Encoding.UTF8,detectEncodingFromByteOrderMarks:false,bufferSize:32768);
        while(reader.ReadLine() is { } line){
            var fields=line.Split('\t');
            if(fields.Length!=4)continue;
            if(kind!="all"&&fields[2]!=kind)continue;
            string name=Normalize(fields[1]);
            bool match=true;
            foreach(var token in tokens)if(!name.Contains(token,StringComparison.Ordinal)){match=false;break;}
            if(!match)continue;
            matches.Add(new Entry(fields[0],fields[1],fields[2],fields[3]));
            if(matches.Count>=max)break;
        }
        return matches;
    }
    public static List<Entry> SearchBundled(string query,string kind,int max=75)
    {
        using var input=Assembly.GetExecutingAssembly().GetManifestResourceStream("MATCHLABAZ.OfflineRegistry");
        return input is null?new List<Entry>():Search(input,query,kind,max);
    }
}
