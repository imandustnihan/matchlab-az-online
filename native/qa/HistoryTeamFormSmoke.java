import az.matchlab.mobile.HistoryTeamForm;

/** JDK 17-only contract QA for Android's native historical team-form logic. */
public final class HistoryTeamFormSmoke {
    private static int passed;
    private static void check(boolean ok,String name){
        if(!ok)throw new AssertionError(name);
        passed++;System.out.println("[PASS] "+name);
    }
    public static void main(String[] args){
        HistoryTeamForm f=new HistoryTeamForm("Liverpool");
        f.add("Liverpool FC","Bournemouth",4,2,true,"2025-08-15");
        f.add("Arsenal","Liverpool FC",2,2,true,"2025-08-17");
        f.add("Liverpool FC","Chelsea",0,1,true,"2025-08-19");
        f.add("Liverpool FC","Everton",-1,-1,false,"2025-08-22");
        f.add("Liverpool Ladies","Liverpool FC",2,0,true,"2025-08-23");
        f.add("Real Madrid","Valencia",3,1,true,"2025-08-21");
        check(f.played()==3,"Only recorded and unambiguous matches counted");
        check(f.wins()==1&&f.draws()==1&&f.losses()==1,"Win/draw/loss from actual score");
        check(f.goalsFor()==6&&f.goalsAgainst()==5,"Home and away goals oriented to chosen team");
        check("M · H · Q".equals(f.recentForm()),"Recent form sorted newest first");
        check(f.totals().contains("Qələbə: 1"),"Readable Azerbaijani summary");
        HistoryTeamForm ambiguous=new HistoryTeamForm("Manchester");
        ambiguous.add("Manchester United","Everton",2,0,true,"2025-08-11");
        ambiguous.add("Manchester City","Chelsea",3,1,true,"2025-08-12");
        check(ambiguous.ambiguous(),"Different clubs matching same filter flagged ambiguous");
        HistoryTeamForm empty=new HistoryTeamForm("");
        empty.add("X","Y",2,0,true,"2026-01-01");
        check(empty.played()==0,"Blank team filter must not aggregate entire league");
        System.out.println("MATCHLAB Android HistoryTeamForm QA: "+passed+" checks passed");
    }
}
