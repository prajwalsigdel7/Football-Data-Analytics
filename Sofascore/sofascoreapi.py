"""
sofascoreapi.py
===============
A lightweight Python package to access Sofascore match, league,
team and player data directly through their internal API.

This package was built by intercepting Sofascore's own network
requests using Selenium + Chrome DevTools Protocol (CDP), discovering
the hidden API endpoints, and wrapping them into clean reusable code.

No authentication required. No browser needed at runtime.
Just pip install requests and you're good to go.

Author  : Prajwal Sigdel
Version : 2.0.0
Requires: requests

-----------------------------------------------------------------
Quick Start:
-----------------------------------------------------------------

    from sofascoreapi import MatchStats, League, Team, Player

    # Single match
    match = MatchStats("15452752")
    match.get_shotmap()

    # League season
    ucl = League("7", "76953")
    ucl.get_top_players()

    # Team
    team = Team("2829")
    team.get_squad()

    # Player
    player = Player("859025")
    player.get_info()

-----------------------------------------------------------------
How to find IDs — all from Sofascore URLs:
-----------------------------------------------------------------

    match_id      → sofascore.com/match/team-a-team-b/...#id:15452752
                    → grab the number after #id:

    tournament_id → sofascore.com/tournament/football/.../premier-league/17
                    → last number in URL

    season_id     → sofascore.com/tournament/...#id:76953
                    → number after #id: on league page

    team_id       → sofascore.com/team/football/real-madrid/2829
                    → last number in URL

    player_id     → sofascore.com/player/vinicius-jr/859025
                    → last number in URL

-----------------------------------------------------------------
Common Tournament IDs (verified):
-----------------------------------------------------------------

    UEFA Champions League    →  7
    Premier League           →  17
    La Liga                  →  8
    Serie A                  →  23
    Bundesliga               →  35
    Ligue 1                  →  34
    Eredivisie               →  37
    Primeira Liga            →  238
    UEFA Europa League       →  679
    UEFA Conference League   →  17015
    World Cup                →  16
    Euro Championship        →  1

-----------------------------------------------------------------
"""

import requests
import json
import socket
import dns.resolver

# Bypass WorldLink DNS block
_original_getaddrinfo = socket.getaddrinfo

def _patched_getaddrinfo(host, port, *args, **kwargs):
    try:
        # Uses dnspython to resolve via system/specified resolvers 
        # instead of the default socket implementation
        resolved = dns.resolver.resolve(host, 'A', lifetime=10)
        ip = resolved[0].to_text()
        return _original_getaddrinfo(ip, port, *args, **kwargs)
    except Exception:
        # Fallback to original method if custom resolution fails
        return _original_getaddrinfo(host, port, *args, **kwargs)

socket.getaddrinfo = _patched_getaddrinfo

# ─────────────────────────────────────────────────────────────────
#  Shared config
# ─────────────────────────────────────────────────────────────────

BASE_URL = "https://www.sofascore.com/api/v1"
HEADERS  = {"User-Agent": "Mozilla/5.0"}

# Quick reference — common tournament IDs
TOURNAMENTS = {
    "ucl"              : "7",
    "premier_league"   : "17",
    "la_liga"          : "8",
    "serie_a"          : "23",
    "bundesliga"       : "35",
    "ligue_1"          : "34",
    "eredivisie"       : "37",
    "primeira_liga"    : "238",
    "europa_league"    : "679",
    "conference_league": "17015",
    "world_cup"        : "16",
    "euros"            : "1",
}


# ─────────────────────────────────────────────────────────────────
#  Shared utilities
# ─────────────────────────────────────────────────────────────────

def _fetch(url: str) -> dict:
    """
    Internal GET request used by all classes.

    Sends a request to the given Sofascore API URL and returns
    the parsed JSON as a Python dictionary. Raises a clear error
    if the API returns anything other than a 200 status.

    Parameters
    ----------
    url : str
        Full Sofascore API URL to call.

    Returns
    -------
    dict
        Parsed JSON response from Sofascore.

    Raises
    ------
    Exception
        If the API returns a non-200 status code.
    """
    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200:
        raise Exception(
            f"\n❌ API Error\n"
            f"   URL    : {url}\n"
            f"   Status : {response.status_code}\n"
            f"   Tip    : Check if tournament_id, season_id or match_id is correct."
        )
    return response.json()


def pretty_print(data: dict) -> None:
    """
    Print any API response in clean, readable JSON format.

    Use this to explore what fields Sofascore returns before
    building your DataFrames or visualizations.

    Parameters
    ----------
    data : dict
        Any dictionary returned from a get_* method.

    Examples
    --------
    >>> from sofascoreapi import League, pretty_print
    >>> ucl  = League("7", "76953")
    >>> data = ucl.get_top_players()
    >>> pretty_print(data)
    """
    print(json.dumps(data, indent=2, ensure_ascii=False))


def list_tournaments() -> None:
    """
    Print all built-in tournament shortcut names and their IDs.

    Use these to quickly look up a tournament_id without
    going to the Sofascore website.

    Examples
    --------
    >>> from sofascoreapi import list_tournaments
    >>> list_tournaments()
    """
    print("\n📋 Available Tournament Shortcuts:\n")
    print(f"  {'Name':<25} {'tournament_id'}")
    print(f"  {'-'*25} {'-'*15}")
    for name, tid in TOURNAMENTS.items():
        print(f"  {name:<25} {tid}")
    print()


def test_endpoints(
    tournament_id: str,
    season_id: str,
    match_id: str
) -> None:
    """
    Run a full connectivity test across all known Sofascore endpoints.

    Tests every endpoint across MatchStats and League and prints
    a clear pass/fail result for each one. Run this whenever you
    set up a new project or suspect Sofascore has changed their
    API structure.

    Parameters
    ----------
    tournament_id : str
        A valid Sofascore tournament ID.
    season_id : str
        A valid season ID for the given tournament.
    match_id : str
        A valid match ID to test match-level endpoints.

    Examples
    --------
    >>> from sofascoreapi import test_endpoints
    >>> test_endpoints(
    ...     tournament_id="7",
    ...     season_id="76953",
    ...     match_id="15452752"
    ... )
    """
    print("\n🔍 Running Sofascore API Endpoint Tests...\n")

    # match endpoints
    print("── MatchStats Endpoints ──────────────────────")
    match_eps = [
        "shotmap", "lineups", "statistics", "incidents",
        "graph", "average-positions", "highlights", "best-players",
    ]
    for ep in match_eps:
        url = f"{BASE_URL}/event/{match_id}/{ep}"
        try:
            r = requests.get(url, headers=HEADERS)
            status = "✅" if r.status_code == 200 else "❌"
            print(f"  {status}  {ep:<25} ({r.status_code})")
        except Exception as e:
            print(f"  ❌  {ep:<25} (error: {e})")

    # league endpoints
    print("\n── League Endpoints ──────────────────────────")
    league_eps = [
        ("standings/total",                  "get_standings"),
        ("top-players/overall",              "get_top_players"),
        ("top-players-per-game/all/overall", "get_top_players_per_game"),
        ("top-teams/overall",                "get_top_teams"),
        ("events/round/1",                   "get_matches"),
    ]
    for ep, method in league_eps:
        url = f"{BASE_URL}/unique-tournament/{tournament_id}/season/{season_id}/{ep}"
        try:
            r = requests.get(url, headers=HEADERS)
            status = "✅" if r.status_code == 200 else "❌"
            print(f"  {status}  {method:<35} ({r.status_code})")
        except Exception as e:
            print(f"  ❌  {method:<35} (error: {e})")

    print("\n── All Tests Done ────────────────────────────\n")


# ─────────────────────────────────────────────────────────────────
#  MatchStats — everything about a single match
# ─────────────────────────────────────────────────────────────────

class MatchStats:
    """
    Access all available data for a single Sofascore match.

    This is your go-to class when you have a specific match in mind
    and want to dig into the details — shot locations, lineups,
    player ratings, match timeline, and more.

    Parameters
    ----------
    match_id : str
        The unique Sofascore match ID found at the end of any
        match page URL after '#id:'.

        Example:
            sofascore.com/match/real-madrid-benfica/...#id:15452752
            → match_id = "15452752"

    Examples
    --------
    >>> from sofascoreapi import MatchStats, pretty_print
    >>> match = MatchStats("15452752")
    >>> pretty_print(match.get_shotmap())
    >>> pretty_print(match.get_lineups())
    >>> all_data = match.get_all()
    """

    def __init__(self, match_id: str) -> None:
        self.match_id = match_id

    def _get(self, endpoint: str) -> dict:
        url = f"{BASE_URL}/event/{self.match_id}/{endpoint}"
        return _fetch(url)

    def get_shotmap(self) -> dict:
        """
        Get every shot taken in the match with full detail.

        Each shot entry contains the player who took it, where on
        the pitch it came from (x/y on 0-100 scale), the xG value,
        whether it was a goal, saved, missed or blocked, and which
        body part was used.

        Returns
        -------
        dict
            Key 'shotmap' → list of shots.
            Each shot: player, x, y, xg, result, bodyPart, situation.

        Examples
        --------
        >>> match = MatchStats("15452752")
        >>> data  = match.get_shotmap()
        >>> shots = data["shotmap"]
        >>> print(shots[0]["player"]["name"], shots[0]["xg"])
        """
        return self._get("shotmap")

    def get_lineups(self) -> dict:
        """
        Get starting XI, substitutes and formation for both teams.

        Returns full player details including name, jersey number,
        position, match rating, minutes played and substitution info.

        Returns
        -------
        dict
            Keys 'home' and 'away' → player lists and formation string.

        Examples
        --------
        >>> match     = MatchStats("15452752")
        >>> data      = match.get_lineups()
        >>> home      = data["home"]["players"]
        >>> formation = data["home"]["formation"]
        """
        return self._get("lineups")

    def get_statistics(self) -> dict:
        """
        Get match statistics for both teams across all periods.

        Covers possession, shots, passes, accuracy, corners,
        fouls, offsides, tackles and more. Grouped by full match,
        first half and second half.

        Returns
        -------
        dict
            Key 'statistics' → list of period groups with team stats.

        Examples
        --------
        >>> match = MatchStats("15452752")
        >>> data  = match.get_statistics()
        """
        return self._get("statistics")

    def get_incidents(self) -> dict:
        """
        Get the full match timeline in chronological order.

        Includes goals with scorer and assist, yellow/red cards,
        substitutions with minute and player info, and VAR decisions.

        Returns
        -------
        dict
            Key 'incidents' → list of match events in order.

        Examples
        --------
        >>> match     = MatchStats("15452752")
        >>> data      = match.get_incidents()
        >>> incidents = data["incidents"]
        """
        return self._get("incidents")

    def get_graph(self) -> dict:
        """
        Get match momentum graph data across all minutes.

        Shows how the match rating shifted for both teams over time.
        Great for plotting match flow and identifying key periods.

        Returns
        -------
        dict
            Graph data points with minute and value per team.

        Examples
        --------
        >>> match = MatchStats("15452752")
        >>> data  = match.get_graph()
        """
        return self._get("graph")

    def get_average_positions(self) -> dict:
        """
        Get the average pitch position of every player in the match.

        Returns x/y coordinates showing where each player spent
        most of their time. Great for team shape visualizations.

        Returns
        -------
        dict
            Keys 'home' and 'away' → 'averagePositions' with x/y.

        Examples
        --------
        >>> match = MatchStats("15452752")
        >>> data  = match.get_average_positions()
        >>> home  = data["home"]["averagePositions"]
        """
        return self._get("average-positions")

    def get_highlights(self) -> dict:
        """
        Get available highlight video links for the match.

        Returns source URLs and thumbnails for any highlight
        clips Sofascore has indexed for this match.

        Returns
        -------
        dict
            Highlight video data with URLs and thumbnails.

        Examples
        --------
        >>> match = MatchStats("15452752")
        >>> data  = match.get_highlights()
        """
        return self._get("highlights")

    def get_best_players(self) -> dict:
        """
        Get the highest rated players from both teams.

        Returns standout performers with match ratings
        and their key contributing statistics.

        Returns
        -------
        dict
            Best players from home and away with ratings.

        Examples
        --------
        >>> match = MatchStats("15452752")
        >>> data  = match.get_best_players()
        """
        return self._get("best-players")

    def get_all(self) -> dict:
        """
        Fetch all available match data in a single call.

        Calls every working endpoint and bundles everything
        into one dictionary.

        Returns
        -------
        dict
            Keys: 'shotmap', 'lineups', 'statistics', 'incidents',
            'graph', 'average_positions', 'highlights', 'best_players'.

        Examples
        --------
        >>> match   = MatchStats("15452752")
        >>> data    = match.get_all()
        >>> shotmap = data["shotmap"]
        """
        return {
            "shotmap"           : self.get_shotmap(),
            "lineups"           : self.get_lineups(),
            "statistics"        : self.get_statistics(),
            "incidents"         : self.get_incidents(),
            "graph"             : self.get_graph(),
            "average_positions" : self.get_average_positions(),
            "highlights"        : self.get_highlights(),
            "best_players"      : self.get_best_players(),
        }


# ─────────────────────────────────────────────────────────────────
#  League — season-level data for any tournament
# ─────────────────────────────────────────────────────────────────

class League:
    """
    Access season-level data for any Sofascore tournament.

    Works for every major competition — Champions League, Premier
    League, La Liga, Serie A, Bundesliga, Ligue 1, Europa League
    and more. The API structure is identical across all of them.
    Only the tournament_id and season_id change.

    Parameters
    ----------
    tournament_id : str
        Sofascore tournament ID from the league page URL.

        Common IDs:
            UCL              → "7"
            Premier League   → "17"
            La Liga          → "8"
            Serie A          → "23"
            Bundesliga       → "35"
            Ligue 1          → "34"
            Europa League    → "679"

        Run list_tournaments() to see all built-in shortcuts.

    season_id : str
        Season ID from the league page URL after '#id:'.
        Grab this fresh from Sofascore for the season you want.

        Example:
            sofascore.com/tournament/.../7#id:76953
            → season_id = "76953"

    Examples
    --------
    >>> from sofascoreapi import League, pretty_print
    >>> ucl  = League("7", "76953")
    >>> pretty_print(ucl.get_standings())
    >>> pretty_print(ucl.get_top_players())
    """

    def __init__(self, tournament_id: str, season_id: str) -> None:
        self.tournament_id = tournament_id
        self.season_id     = season_id

    def _get(self, endpoint: str) -> dict:
        url = f"{BASE_URL}/unique-tournament/{self.tournament_id}/season/{self.season_id}/{endpoint}"
        return _fetch(url)

    def get_standings(self) -> dict:
        """
        Get the current league standings table.

        Returns every team's position, points, wins, draws,
        losses, goals scored, conceded and goal difference.

        Returns
        -------
        dict
            Key 'standings' → list of team rows by position.

        Examples
        --------
        >>> ucl  = League("7", "76953")
        >>> data = ucl.get_standings()
        >>> rows = data["standings"][0]["rows"]
        """
        return self._get("standings/total")

    def get_top_players(self) -> dict:
        """
        Get overall top player statistics for the season.

        Returns ranked players with accumulated season stats
        including goals, assists, xG, appearances and ratings.
        This is your main endpoint for any player ranking or
        xG analysis task.

        Returns
        -------
        dict
            Key 'topPlayers' → stat categories with ranked players.

        Examples
        --------
        >>> ucl  = League("7", "76953")
        >>> data = ucl.get_top_players()
        >>> pretty_print(data)
        """
        return self._get("top-players/overall")

    def get_top_players_per_game(self) -> dict:
        """
        Get top player statistics averaged per game.

        Same as get_top_players() but all numbers are per
        appearance. Useful for comparing players with different
        numbers of games played.

        Returns
        -------
        dict
            Top players ranked by per-game averages.

        Examples
        --------
        >>> ucl  = League("7", "76953")
        >>> data = ucl.get_top_players_per_game()
        """
        return self._get("top-players-per-game/all/overall")

    def get_top_teams(self) -> dict:
        """
        Get top team statistics for the season.

        Teams ranked across categories including goals,
        xG, possession, shots and more.

        Returns
        -------
        dict
            Top teams ranked by various stat categories.

        Examples
        --------
        >>> ucl  = League("7", "76953")
        >>> data = ucl.get_top_teams()
        """
        return self._get("top-teams/overall")

    def get_all_scorers(self) -> list:
        """
        Get every player who scored in this league season so far.

        Loops through all rounds automatically — stops when a round
        returns no matches, meaning it naturally halts at the current
        point in the competition. For each match it pulls incidents
        and extracts goals, excluding own goals.

        Returns
        -------
        list of dict
            One entry per player, sorted by goals descending.
            Each dict has: player, player_id, team, goals.

        Examples
        --------
        >>> ucl     = League("7", "76953")
        >>> scorers = ucl.get_all_scorers()
        >>> for s in scorers[:10]:
        ...     print(s["player"], s["team"], s["goals"])
        """
        from collections import defaultdict

        tally   = defaultdict(lambda: {"player": "", "player_id": None, "team": "", "goals": 0})
        round_n = 1

        while True:
            try:
                matches = self._get(f"events/round/{round_n}")
            except Exception:
                break

            events = matches.get("events", [])
            if not events:
                break

            for event in events:
                # skip unplayed matches
                status = event.get("status", {}).get("type", "")
                if status not in ("finished",):
                    continue

                match_id = str(event["id"])
                try:
                    inc_data  = _fetch(f"{BASE_URL}/event/{match_id}/incidents")
                    incidents = inc_data.get("incidents", [])
                except Exception:
                    continue

                for inc in incidents:
                    if inc.get("incidentType") != "goal":
                        continue
                    # skip own goals
                    if inc.get("incidentClass") == "ownGoal":
                        continue

                    player = inc.get("player", {})
                    team   = inc.get("team", {})
                    pid    = player.get("id")
                    name   = player.get("name", "Unknown")
                    tname  = team.get("name", "Unknown")

                    if pid is None:
                        continue

                    tally[pid]["player"]    = name
                    tally[pid]["player_id"] = pid
                    tally[pid]["team"]      = tname
                    tally[pid]["goals"]    += 1

            round_n += 1

        return sorted(tally.values(), key=lambda x: x["goals"], reverse=True)

    def get_matches(self, round_number: str = "1") -> dict:
        """
        Get all fixtures and results for a specific round.

        Returns every match in that gameweek including scores,
        match IDs, team names and kickoff times. The match IDs
        here can be passed directly into MatchStats.

        Parameters
        ----------
        round_number : str
            Gameweek or round number. Defaults to "1".

        Returns
        -------
        dict
            Key 'events' → list of matches for that round.

        Examples
        --------
        >>> ucl   = League("7", "76953")
        >>> data  = ucl.get_matches(round_number="8")
        >>> games = data["events"]
        >>> for g in games:
        ...     print(g["homeTeam"]["name"], "vs", g["awayTeam"]["name"])
        """
        return self._get(f"events/round/{round_number}")


# ─────────────────────────────────────────────────────────────────
#  Team — club profile and squad data
# ─────────────────────────────────────────────────────────────────

class Team:
    """
    Access profile and squad data for any Sofascore team.

    Parameters
    ----------
    team_id : str
        Sofascore team ID from the team page URL.

        Example:
            sofascore.com/team/football/real-madrid/2829
            → team_id = "2829"

    Examples
    --------
    >>> from sofascoreapi import Team, pretty_print
    >>> team = Team("2829")
    >>> pretty_print(team.get_info())
    >>> pretty_print(team.get_squad())
    """

    def __init__(self, team_id: str) -> None:
        self.team_id = team_id

    def get_info(self) -> dict:
        """
        Get basic team profile information.

        Returns team name, country, founded year, stadium,
        manager, colors and other profile details.

        Returns
        -------
        dict
            Key 'team' → full team profile dictionary.

        Examples
        --------
        >>> team = Team("2829")
        >>> data = team.get_info()
        >>> print(data["team"]["name"])
        """
        url = f"{BASE_URL}/team/{self.team_id}"
        return _fetch(url)

    def get_squad(self) -> dict:
        """
        Get the full squad list for the team.

        Returns every player with name, position, jersey number,
        nationality, age and current market value.

        Returns
        -------
        dict
            Key 'players' → list of player dictionaries.

        Examples
        --------
        >>> team    = Team("2829")
        >>> data    = team.get_squad()
        >>> players = data["players"]
        >>> for p in players:
        ...     print(p["player"]["name"], p["player"]["position"])
        """
        url = f"{BASE_URL}/team/{self.team_id}/players"
        return _fetch(url)

    def get_season_stats(self, tournament_id: str, season_id: str) -> dict:
        """
        Get team statistics for a specific league season.

        Parameters
        ----------
        tournament_id : str
            League tournament ID (e.g. "7" for UCL).
        season_id : str
            Season ID (e.g. "76953" for UCL 2025/26).

        Returns
        -------
        dict
            Team stats for that competition and season.

        Examples
        --------
        >>> team = Team("2829")
        >>> data = team.get_season_stats("7", "76953")
        """
        url = f"{BASE_URL}/team/{self.team_id}/unique-tournament/{tournament_id}/season/{season_id}/statistics/overall"
        return _fetch(url)
    
    def get_season_matches(self, tournament_id: str, season_id: str) -> list:
        """
        Get all finished matches for this team in a specific season.

        Works for any competition — league, cup or knockout tournament.
        Loops through the team's full match history and filters by
        tournament and season. Returns group stage and knockout matches
        together in one list, no deduplication needed.

        Parameters
        ----------
        tournament_id : str
            League tournament ID (e.g. "7" for UCL, "17" for PL).
        season_id : str
            Season ID for the competition.

        Returns
        -------
        list of dict
            Each dict has: match_id, home, away.
            match_id can be passed directly into MatchStats.

        Examples
        --------
        >>> team    = Team("1644")
        >>> matches = team.get_season_matches("7", "76953")   # PSG UCL
        >>> for m in matches:
        ...     print(m["home"], "vs", m["away"])

        >>> team    = Team("9")
        >>> matches = team.get_season_matches("17", "52186")  # Arsenal PL
        """
        matches = []
        page    = 0

        while True:
            try:
                data   = _fetch(f"{BASE_URL}/team/{self.team_id}/events/last/{page}")
                events = data.get("events", [])
                if not events:
                    break
                for ev in events:
                    tid    = ev.get("tournament", {}).get("uniqueTournament", {}).get("id")
                    sid    = ev.get("season", {}).get("id")
                    status = ev.get("status", {}).get("type", "")
                    if str(tid) == tournament_id and str(sid) == season_id and status == "finished":
                        matches.append({
                            "match_id": str(ev["id"]),
                            "home":     ev["homeTeam"]["name"],
                            "away":     ev["awayTeam"]["name"],
                        })
                page += 1
            except Exception:
                break

        return matches

# ─────────────────────────────────────────────────────────────────
#  Player — individual player stats and heatmaps
# ─────────────────────────────────────────────────────────────────

class Player:
    """
    Access individual player profile, season stats and heatmaps.

    Parameters
    ----------
    player_id : str
        Sofascore player ID from the player page URL.

        Example:
            sofascore.com/player/vinicius-jr/859025
            → player_id = "859025"

    Examples
    --------
    >>> from sofascoreapi import Player, pretty_print
    >>> player = Player("859025")
    >>> pretty_print(player.get_info())
    >>> pretty_print(player.get_heatmap("7", "76953"))
    """

    def __init__(self, player_id: str) -> None:
        self.player_id = player_id

    def get_info(self) -> dict:
        """
        Get basic player profile information.

        Returns name, nationality, date of birth, position,
        current team, preferred foot, height and market value.

        Returns
        -------
        dict
            Key 'player' → full player profile dictionary.

        Examples
        --------
        >>> player = Player("859025")
        >>> data   = player.get_info()
        >>> print(data["player"]["name"])
        >>> print(data["player"]["position"])
        """
        url = f"{BASE_URL}/player/{self.player_id}"
        return _fetch(url)

    def get_season_stats(self, tournament_id: str, season_id: str) -> dict:
        """
        Get a player's statistics for a specific season.

        Returns full accumulated stats: goals, assists, xG, xA,
        rating, minutes played, dribbles, key passes and more.

        Parameters
        ----------
        tournament_id : str
            League tournament ID (e.g. "7" for UCL).
        season_id : str
            Season ID (e.g. "76953" for UCL 2025/26).

        Returns
        -------
        dict
            Full season statistics for this player.

        Examples
        --------
        >>> player = Player("859025")
        >>> data   = player.get_season_stats("7", "76953")
        """
        url = f"{BASE_URL}/player/{self.player_id}/unique-tournament/{tournament_id}/season/{season_id}/statistics/overall"
        return _fetch(url)

    def get_heatmap(self, tournament_id: str, season_id: str) -> dict:
        """
        Get a player's position heatmap for a specific season.

        Returns x/y coordinate points showing where the player
        was most active on the pitch across all appearances.
        Perfect for heatmap visualizations.

        Parameters
        ----------
        tournament_id : str
            League tournament ID.
        season_id : str
            Season ID for the competition.

        Returns
        -------
        dict
            Key 'points' → list of x/y coordinate dictionaries.

        Examples
        --------
        >>> player = Player("859025")
        >>> data   = player.get_heatmap("7", "76953")
        >>> points = data["points"]
        """
        url = f"{BASE_URL}/player/{self.player_id}/unique-tournament/{tournament_id}/season/{season_id}/heatmap/overall"
        return _fetch(url)