import az.matchlab.mobile.OfflineIdentityIndex;
import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.zip.GZIPOutputStream;
public class OfflineIdentitySmoke {
    private static int passed=0;
    private static void check(boolean condition,String label){
        if(!condition)throw new AssertionError(label);
        passed++;System.out.println("[PASS] "+label);
    }
    private static byte[] fixture()throws Exception{
        var output=new ByteArrayOutputStream();
        try(var stream=new GZIPOutputStream(output)){
            stream.write(("rp1\tKylian Mbappé\tplayers\tFrance\n"+
                "rt2\tQarabağ FK\tteams\tAzerbaijan\n"+
                "rc3\tCarlo Ancelotti\tcoaches\tItaly\n"+
                "rp4\tArda Güler\tplayers\tTürkiye\n").getBytes(StandardCharsets.UTF_8));
        }
        return output.toByteArray();
    }
    private static List<OfflineIdentityIndex.Entry> find(byte[] gz,String query,String kind)throws Exception{
        return OfflineIdentityIndex.search(new ByteArrayInputStream(gz),query,kind,75);
    }
    public static void main(String[] args)throws Exception{
        byte[] gz=fixture();
        check(find(gz,"Mbappe","all").size()==1,"Diacritics-insensitive real name search");
        check(find(gz,"QARABAG","teams").size()==1,"Azerbaijan team normalization");
        check(find(gz,"arda","players").size()==1,"Player prefix name search");
        check(find(gz,"Carlo","coaches").size()==1,"Coach kind");
        check(find(gz,"Carlo","players").isEmpty(),"Kind filter excludes other categories");
        check(find(gz,"Guler Arda","all").size()==1,"Token order independent");
        check(find(gz,"Xyz","all").isEmpty(),"No fabricated results");
        check(find(gz,"","all").isEmpty(),"Blank query never dumps entire registry");
        check(find(gz,"Q","all").isEmpty(),"One-character queries refused");
        check(OfflineIdentityIndex.normalize("Qarabağ").equals("qarabag"),"Normalization stable");
        check(find(gz,"Carlo","all").get(0).id.equals("rc3"),"Original verified Reep ID retained");
        check(OfflineIdentityIndex.search(new ByteArrayInputStream(gz),"ar","all",1).size()==1,
            "Result limit is enforced");
        System.out.println("MATCHLAB offline Java identity QA: "+passed+" checks passed");
    }
}
