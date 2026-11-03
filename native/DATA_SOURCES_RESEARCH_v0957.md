# MATCHLAB AZ — Data source decision notes (2026-11-03)

## Purpose
Avoid invented football scores, lineups, xG, transfer claims, and misleading realtime labels when using free sources.

## Current workable feeds
1. **OpenFootball football.json (public domain)**:
   https://github.com/openfootball/football.json
   Has league/season fixture and recorded result data. The repository has a daily export pipeline, but upstream sources may not update every day. Do not promote this to a realtime event feed. Local historic team form must be derived only from games where `resultRecorded=true` and valid nonnegative scores.
2. **football-data.org**:
   https://www.football-data.org/pricing and https://www.football-data.org/documentation/api
   The free tier has delayed score coverage and limited competition scope. Free rate limit for registered clients is 10 calls/minute. An API key must not be embedded in Android/Windows packages; use a server-side secret and bounded caching if this source is integrated later.
3. **Current backend**:
   https://matchlab-az-online.onrender.com
   Keep as the selected origin until a different HTTPS origin passes live /api/status, archive, and native-client smoke checks. A status check alone does not demonstrate realtime source completeness.

## Product behavior rules
- Label saved matches **CANLI DEYİL**, stale live responses **KÖHNƏ MƏLUMAT**.
- Distinguish complete historical archive from partial paginated fallback. A partial list's form is not a season-wide statistic.
- No claim of automatic refresh for all 506207 identities, and no unverified lineup, injury, death date, card, or transfer.
- Native apps should keep network calls off the UI thread. Show connection failures and measured response time without implying server speed is guaranteed.
- For production push notifications on Android 13+, follow runtime notification permission, channel, and background work rules; current local sounds are only while the app is open.
- Avoid copying proprietary Sofascore/LiveScore screens, logos, or restricted data feeds; implement independent UI and licensed/allowed sources.
