using System;
using System.Collections.Generic;
using System.Linq;

namespace MATCHLABAZ;

/// <summary>
/// Deterministic statistics from *recorded* OpenFootball historical results.
/// A partial/paged response must never be described as a full-season record.
/// </summary>
public sealed class HistoryTeamForm
{
    private readonly string team;
    private readonly List<(string Date, int Order, string Form)> played = new();
    public int Played { get; private set; }
    public int Wins { get; private set; }
    public int Draws { get; private set; }
    public int Losses { get; private set; }
    public int GoalsFor { get; private set; }
    public int GoalsAgainst { get; private set; }

    public HistoryTeamForm(string selectedTeam) => team = selectedTeam.Trim();

    public void Add(string home, string away, int homeScore, int awayScore, bool resultRecorded, string date)
    {
        if (team.Length == 0 || !resultRecorded || homeScore < 0 || awayScore < 0) return;
        bool homeMatch = home.Contains(team, StringComparison.OrdinalIgnoreCase);
        bool awayMatch = away.Contains(team, StringComparison.OrdinalIgnoreCase);
        // An ambiguous substring (matching both sides) cannot be attributed safely.
        if (homeMatch == awayMatch) return;

        int scored = homeMatch ? homeScore : awayScore;
        int conceded = homeMatch ? awayScore : homeScore;
        string form = scored > conceded ? "Q" : scored < conceded ? "M" : "H";
        Played++;
        GoalsFor += scored;
        GoalsAgainst += conceded;
        if (form == "Q") Wins++;
        else if (form == "M") Losses++;
        else Draws++;
        played.Add((date ?? "", played.Count, form));
    }

    /// <summary>Newest five *recorded* fixtures; ISO dates are sortable as text.</summary>
    public string RecentForm => string.Join(" · ", played
        .OrderByDescending(item => item.Date, StringComparer.Ordinal)
        .ThenByDescending(item => item.Order)
        .Take(5).Select(item => item.Form));

    public string Totals => $"Oyun: {Played}  ·  Qələbə: {Wins}  ·  Heç-heçə: {Draws}  ·  Məğlubiyyət: {Losses}";
    public string GoalsAndForm => $"Qollar: {GoalsFor}:{GoalsAgainst}  ·  Son 5 (Q/H/M): {RecentForm}";
}
