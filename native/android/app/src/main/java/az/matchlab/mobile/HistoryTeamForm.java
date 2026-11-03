package az.matchlab.mobile;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Locale;

/**
 * Historical team form from explicitly recorded results only. No network or
 * Android dependency, so the exact logic can be tested with an ordinary JDK.
 */
public final class HistoryTeamForm {
    private final String team;
    private final List<Game> games=new ArrayList<>();
    private final java.util.Set<String> matchedClubs=new java.util.HashSet<>();
    private int wins,draws,losses,forGoals,againstGoals;
    private static final class Game {
        final String date,form;
        final int order;
        Game(String d,String f,int n){date=d;form=f;order=n;}
    }

    public HistoryTeamForm(String selectedTeam){
        team=selectedTeam==null?"":selectedTeam.trim().toLowerCase(Locale.ROOT);
    }
    public void add(String home,String away,int homeScore,int awayScore,boolean recorded,String date){
        if(team.isEmpty()||!recorded||homeScore<0||awayScore<0)return;
        boolean h=home!=null&&home.toLowerCase(Locale.ROOT).contains(team);
        boolean a=away!=null&&away.toLowerCase(Locale.ROOT).contains(team);
        if(h==a)return; // Unmatched or ambiguous substring: do not guess.
        matchedClubs.add((h?home:away).trim().toLowerCase(Locale.ROOT));
        int scored=h?homeScore:awayScore,conceded=h?awayScore:homeScore;
        String mark=scored>conceded?"Q":scored<conceded?"M":"H";
        if("Q".equals(mark))wins++;
        else if("M".equals(mark))losses++;
        else draws++;
        forGoals+=scored;againstGoals+=conceded;
        games.add(new Game(date==null?"":date,mark,games.size()));
    }
    public boolean ambiguous(){return matchedClubs.size()>1;}
    public int played(){return games.size();}
    public int wins(){return wins;}
    public int draws(){return draws;}
    public int losses(){return losses;}
    public int goalsFor(){return forGoals;}
    public int goalsAgainst(){return againstGoals;}
    public String recentForm(){
        List<Game> ordered=new ArrayList<>(games);
        ordered.sort(Comparator.comparing((Game g)->g.date).thenComparingInt(g->g.order).reversed());
        StringBuilder result=new StringBuilder();
        for(int i=0;i<Math.min(5,ordered.size());i++){
            if(i>0)result.append(" · ");
            result.append(ordered.get(i).form);
        }
        return result.toString();
    }
    public String totals(){
        return "Oyun: "+played()+" · Qələbə: "+wins+" · Heç-heçə: "+draws+" · Məğlubiyyət: "+losses;
    }
    public String goalsAndForm(){
        return "Qollar: "+forGoals+":"+againstGoals+" · Son 5 (Q/H/M): "+recentForm();
    }
}
