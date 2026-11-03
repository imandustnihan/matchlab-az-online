package az.matchlab.mobile;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.text.Normalizer;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.zip.GZIPInputStream;

/** Verified Reep public-domain CC0 identity names. Offline identity-only search.
 * No lineups, current teams, results, photos or player stats are inferred.
 */
public final class OfflineIdentityIndex {
    private OfflineIdentityIndex() {}
    public static final class Entry {
        public final String id,name,kind,country;
        Entry(String id,String name,String kind,String country){
            this.id=id;this.name=name;this.kind=kind;this.country=country;
        }
    }
    public static String normalize(String text){
        if(text==null)return "";
        String s=Normalizer.normalize(text,Normalizer.Form.NFKD)
            .replaceAll("\\p{M}+","").toLowerCase(Locale.ROOT);
        return s.replace('ə','e').replace('ı','i').replace('ø','o').replace('ł','l').replace('ß','s')
            .trim().replaceAll("\\s+"," ");
    }
    public static List<Entry> search(InputStream compressed,String query,String kind,int limit)
            throws IOException {
        String needle=normalize(query);
        ArrayList<Entry> items=new ArrayList<>();
        if(needle.length()<2||limit<1)return items;
        String[] tokens=needle.split(" ");
        try(BufferedReader reader=new BufferedReader(new InputStreamReader(
                new GZIPInputStream(compressed,32768),"UTF-8"),32768)){
            String line;
            while((line=reader.readLine())!=null){
                String[] fields=line.split("\\t",-1);
                if(fields.length!=4)continue;
                if(!"all".equals(kind)&&!fields[2].equals(kind))continue;
                String name=normalize(fields[1]);
                boolean matched=true;
                for(String token:tokens)if(!name.contains(token)){matched=false;break;}
                if(!matched)continue;
                items.add(new Entry(fields[0],fields[1],fields[2],fields[3]));
                if(items.size()>=limit)break;
            }
        }
        return items;
    }
}
