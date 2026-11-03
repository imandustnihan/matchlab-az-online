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
        check(f.homePlayed()==2&&f.awayPlayed()==1,"Home and away results split correctly");
        check(f.homeWins()==1&&f.homeDraws()==0&&f.homeLosses()==1,"Recorded home W/D/L accurate");
        check(f.awayWins()==0&&f.awayDraws()==1&&f.awayLosses()==0,"Recorded away W/D/L accurate");
        check(f.goalDifference()==1&&f.winPercent()==33,"Goal difference and rounded percentage accurate");
        check(f.homeAway().contains("Evdə 2")&&f.efficiency().contains("+1"),"Azerbaijani home/away and efficiency displayed");
        HistoryTeamForm ambiguous=new HistoryTeamForm("Manchester");
        ambiguous.add("Manchester United","Everton",2,0,true,"2025-08-11");
        ambiguous.add("Manchester City","Chelsea",3,1,true,"2025-08-12");
        check(ambiguous.ambiguous(),"Different clubs matching same filter flagged ambiguous");
        HistoryTeamForm empty=new HistoryTeamForm("");
        empty.add("X","Y",2,0,true,"2026-01-01");
        check(empty.played()==0&&empty.winPercent()==0,"Blank team filter must not aggregate or divide by zero");
        HistoryTeamForm away=new HistoryTeamForm("Atletico");
        away.add("Real Madrid","Atletico Madrid",0,2,true,"2026-04-01");
        away.add("Atletico Madrid","Cadiz",1,1,true,"2026-04-02");
        away.add("Real Madrid","Atletico Madrid",4,1,true,"2026-04-03");
        away.add("Atletico Madrid","Cadiz",9,9,false,"2026-04-04");
        check(away.homePlayed()==1&&away.awayPlayed()==2,"Away/home splits independent of score order");
        check(away.goalDifference()==-1&&away.winPercent()==33,"Negative goal difference and percentage accurate");
        check(away.efficiency().contains("-1"),"Negative goal difference rendered with minus sign");
        HistoryTeamForm rounding=new HistoryTeamForm("Team X");
        rounding.add("Team X","A",2,0,true,"2026-01-01");
        rounding.add("B","Team X",0,1,true,"2026-01-02");
        rounding.add("Team X","C",1,1,true,"2026-01-03");
        check(rounding.winPercent()==67,"Two wins from three games round to 67 percent");
        System.out.println("MATCHLAB Android HistoryTeamForm QA: "+passed+" checks passed");
    }
}
