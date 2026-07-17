# 2026 FIFA World Cup - Stats Schema for Milvus RAG Demo

## Overview

- **Tournament**: 2026 FIFA World Cup (USA/Canada/Mexico)
- **Format**: 48 teams, 12 groups (A-L), 4 teams per group, 104 matches total
- **Group Stage**: Each group plays round-robin (6 matches per group), top 2 + 8 best 3rd-place teams advance to Round of 32
- **Knockout**: Round of 32 → Round of 16 → Quarterfinals → Semifinals → 3rd place → Final (32 knockout matches)

## Data Categories

### 1. TOURNAMENT OVERVIEW
Static metadata about the tournament itself.

| Field | Type | Notes |
|-------|------|-------|
| tournament_name | string | "2026 FIFA World Cup" |
| hosts | string | "United States, Canada, Mexico" |
| start_date | date | |
| end_date | date | |
| total_teams | int | 48 |
| total_matches | int | 104 |
| total_groups | int | 12 |
| teams_per_group | int | 4 |
| advancing_per_group | int | 2 |
| best_third_places | int | 8 |
| knockout_rounds | int | 5 (R32, R16, QF, SF, Final + 3rd place) |

**RAG question examples**: "Which countries are hosting?" "How many teams?" "How many matches total?"

---

### 2. GROUP STAGE TEAMS & TABLES
Per-group standing tables. One entry per group.

**Per Group (12 entries total: Groups A-L):**
| Field | Type |
|-------|------|
| group | string | "A" through "L" |
| phase | string | "group" |
| teams | array of team objects | see below |

**Team object (inside group):**
| Field | Type | Description |
|-------|------|-------------|
| team | string | Country name |
| confederation | string | UEFA, CONMEBOL, CONCACAF, AFC, CAF, OFC |
| FIFA_ranking | int | Pre-tournament FIFA ranking |
| matches_played | int | |
| wins | int | |
| draws | int | |
| losses | int | |
| goals_for | int | |
| goals_against | int | |
| goal_difference | int | GF - GA |
| points | int | 3W + 1D |
| form | string | Last 3 results e.g. "WWD" |
| position | int | 1-4 in group |

**RAG question examples**: "What's the group table?" "Who is top of Group B?" "Which teams are eliminated?"

---

### 3. MATCH RESULTS
One entry per match. ~104 matches total.

| Field | Type | Description |
|-------|------|-------------|
| match_id | string | "M1", "M2", etc. or "Group A - Match 1" |
| phase | string | "group", "round_of_32", "round_of_16", "quarterfinal", "semifinal", "third_place", "final" |
| group | string | Group letter (for group stage) |
| date | date | Match date |
| venue | string | Stadium name + city |
| home_team | string | Home/Team 1 |
| away_team | string | Away/Team 2 |
| home_score | int | Full-time score |
| away_score | int | Full-time score |
| home_score_2ht | int | 2nd half only (for trends) |
| away_score_2ht | int | |
| home_score_1ht | int | Half-time score |
| away_score_1ht | int | |
| home_penalty | int | Penalty shootout score (if applicable) |
| away_penalty | int | |
| away_goals_og | int | Own goals scored by home team (counted as away goals) |
| home_goals_og | int | |
| result | string | "home_win", "away_win", "draw", "home_win_pen", "away_win_pen" |
| match_status | string | "scheduled", "live", "completed", "postponed" |

**RAG question examples**: "Who won match 5?" "What was the halftime score in USA vs Spain?" "Which matches went to penalties?"

---

### 4. TEAM PERFORMANCE STATS
Aggregate stats per team across the tournament. 48 entries (one per team).

| Field | Type | Description |
|-------|------|-------------|
| team | string | |
| confederation | string | |
| matches_played | int | |
| wins | int | |
| draws | int | |
| losses | int | |
| goals_scored | int | |
| goals_conceded | int | |
| goal_difference | int | |
| clean_sheets | int | Matches without conceding |
| goals_per_match | float | |
| goals_conceded_per_match | float | |
| possession_avg | float | Average possession % |
| shots_total | int | Total shots |
| shots_on_target | int | |
| shots_on_target_pct | float | |
| shots_per_match | float | |
| passes_total | int | |
| pass_accuracy | float | % |
| passes_per_match | float | |
| crosses_total | int | |
| corner_kicks | int | |
| offsides | int | |
| fouls_committed | int | |
| yellow_cards | int | |
| red_cards | int | |
| penalties_won | int | |
| penalties_scored | int | |
| goals_from_penalties | int | |
| goals_from_freekicks | int | |
| goals_from_headers | int | |
| goals_from_inside_box | int | |
| goals_from_outside_box | int | |
| goals_conceded_from_penalties | int | |
| goals_conceded_from_headers | int | |
| goals_conceded_from_corners | int | |
| saves | int | Total saves by team |
| saves_per_match | float | |
| tackles_total | int | |
| interceptions | int | |
| clearances | int | |
| duels_won | int | |
| duels_won_pct | float | |
| distance_covered_km | float | Total km |
| sprints | int | |
| points_earned | int | Tournament points |
| position_current | string | "Group A leader", "Eliminated", "In Round of 16", etc. |

**Cool/advanced stats to display**:
- Goals per shot ratio (finishing efficiency)
- Shot accuracy %
- Pass completion % by zone (build-up vs final third)
- Pressing intensity (high turnovers won)
- Set-piece conversion rate (corners + freekicks → goals)
- Clean sheet %
- Goals from different zones (box, outside box, header, freekick, penalty)
- Disciplinary record (fouls per match, cards per 90)
- Possession in final third
- Cross accuracy
- Defensive actions (tackles + interceptions + clearances) per match

**RAG question examples**: "Which team has the best possession?" "Who has the most yellow cards?" "Which team is most efficient at finishing?"

---

### 5. PLAYER STATISTICS
Per-player tournament stats. One entry per player per match they play, or aggregated per player for the tournament.

**Player object (aggregated):**
| Field | Type | Description |
|-------|------|-------------|
| player_name | string | |
| team | string | |
| position | string | "Goalkeeper", "Defender", "Midfielder", "Forward" |
| jersey_number | int | |
| age | int | |
| matches_played | int | |
| minutes_played | int | |
| starts | int | |
| subbed_in | int | |
| subbed_out | int | |
| goals | int | |
| assists | int | |
| shots | int | |
| shots_on_target | int | |
| shots_per_match | float | |
| goals_per_shot | float | Efficiency |
| passes | int | |
| pass_accuracy | float | % |
| key_passes | int | Passes leading to shot |
| crosses | int | |
| cross_accuracy | float | % |
| dribbles_attempted | int | |
| dribbles_successful | int | |
| dribbles_success_pct | float | |
| tackles | int | |
| interceptions | int | |
| clearances | int | |
| blocks | int | |
| fouls_committed | int | |
| fouls_suffered | int | |
| yellow_cards | int | |
| red_cards | int | |
| penalties_scored | int | |
| goals_from_penalty | int | |
| goals_from_freekick | int | |
| goals_from_header | int | |
| goals_from_inside_box | int | |
| goals_from_outside_box | int | |
| own_goals | int | |
| clean_sheets | int | (GK + defenders) |
| saves | int | (GK) |
| goals_conceded | int | (GK) |
| save_percentage | float | % |
| shots_conceded_inside_box | int | (GK) |
| expected_goals (xG) | float | Cumulative |
| expected_assists (xA) | float | Cumulative |
| distance_covered_km | float | Total |
| sprints | int | |
| duels_won | int | |
| rating | float | Average match rating |

**Cool/advanced player stats**:
- Expected Goals (xG) vs actual goals (over/under-performing)
- Expected Assists (xA)
- Progressive passes (forward-moving passes)
- Progressive carries (ball advances into final third)
- Pressures applied
- Defensive actions per 90
- Shot-creating actions (SCA)
- Goal-creating actions (GCA)
- Dribble success rate
- Pass completion in final third
- Passes into penalty area
- Aerial duels won %

**RAG question examples**: "Who is the top scorer?" "Which player has the most assists?" "Who has the best shot accuracy?" "How many goals did Messi score?"

---

### 6. MATCH EVENTS
Detailed event log per match. Could be many entries.

| Field | Type | Description |
|-------|------|-------------|
| match_id | string | |
| minute | int | Match minute (0-90+) |
| extra_time | int | 0 for regular, 1-4 for stoppage time |
| player | string | |
| team | string | |
| event_type | string | "goal", "assist", "shot_on_target", "shot_off_target", "shot_blocked", "save", "corner", "foul", "yellow_card", "red_card", "substitution", "offside", "cross", "tackle", "interception", "clearance", "header", "freekick", "penalty", "own_goal" |
| body_part | string | "right_foot", "left_foot", "header", "other" |
| outcome | string | "goal", "missed", "saved", "blocked", "post", "wide" |
| assist_player | string | Name of assist provider (for goals/shots) |
| xg | float | Expected goals value at time of shot |
| location_x | int | Pitch coordinates (0-100) |
| location_y | int | |

**Cool event types to track**:
- Shot location on pitch (coordinates for heat maps)
- Expected Goals (xG) value
- Build-up style (set piece, counter-attack, slow buildup, fast break)
- Pressure level (high press, mid block, low block)

**RAG question examples**: "When did the first goal come in match 3?" "Who scored headers?" "Which player got a red card?" "How many shots from outside the box?"

---

### 7. VENUE/STADIUM INFO
One entry per venue (~16 venues across 3 host countries).

| Field | Type | Description |
|-------|------|-------------|
| venue_name | string | |
| city | string | |
| country | string | "USA", "Canada", "Mexico" |
| capacity | int | |
| matches_hosted | int | |
| total_attendance | int | |
| avg_attendance | int | |
| matches_list | array | List of match IDs |

**RAG question examples**: "Which stadium hosted the opening match?" "How many matches in New York?"

---

### 8. AWARD TRACKERS
Dynamic awards tracked throughout the tournament.

| Award | Description |
|-------|-------------|
| Golden Boot | Top goalscorer (goals, then assists, then minutes) |
| Silver Boot | 2nd place |
| Bronze Boot | 3rd place |
| Golden Ball | Best player (FIFA) |
| Silver Ball | 2nd best |
| Bronze Ball | 3rd best |
| Yashin Trophy | Best goalkeeper |
| FIFA Fair Play | Best discipline |
| Top scorer | Overall |
| Top assists | Overall |
| Most clean sheets | Goalkeepers |
| Most saves | Goalkeepers |

**RAG question examples**: "Who is winning the Golden Boot?" "Who is the best goalkeeper?"

---

### 9. HISTORICAL CONTEXT (optional, for richer RAG)
| Field | Type | Description |
|-------|------|-------------|
| previous_champion | string | Argentina (2022) |
| most_titles | string | Brazil (5) |
| host_history | array | Previous hosts |
| all_time_top_scorers | array | Historical leaders |
| world_cup_milestones | array | Notable firsts (first 48-team WC, etc.) |

---

## Recommended Data Structure for Milvus

For RAG with Milvus, I recommend structuring data into **separate collections** (or at least separate document chunks):

### Collection 1: `tournament_metadata`
- Small, static. ~20 fields total.
- Embedding: full tournament summary paragraph.

### Collection 2: `group_standings`
- 12 documents (one per group, containing all 4 teams).
- Embedding: group table summary + context.

### Collection 3: `team_stats`
- 48 documents (one per team).
- Embedding: team name + key stats paragraph.

### Collection 4: `match_results`
- 104 documents (one per match).
- Embedding: match summary paragraph + key details.

### Collection 5: `player_stats`
- Up to ~750-800 players × ~2-3 matches = could be large.
- Recommendation: One document per player with aggregated tournament stats.
- Embedding: player name + team + position + key stats.

### Collection 6: `match_events` (optional, high-volume)
- Could be thousands of entries. Consider keeping in a relational DB or filtering.
- Embedding: event summary paragraph.

### Collection 7: `awards`
- Small, dynamic. Updated after each matchday.
- Embedding: current award standings.

---

## Priority Phases

### Phase 1 (Must-have for demo):
1. Tournament metadata
2. Group standings (A-L)
3. Match results (scores, dates, venues)
4. Top scorer table (Golden Boot race)
5. Team standings (aggregate per team)

### Phase 2 (Nice-to-have):
6. Player stats (goals, assists, cards, minutes)
7. Team performance stats (possession, shots, passes, etc.)
8. Match events (goals, cards, key moments)

### Phase 3 (Advanced):
9. Advanced metrics (xG, xA, progressive passes, pressing)
10. Shot maps and location data
11. Historical context and comparisons

---

## Sample RAG Questions by Data Category

**Tournament**: "How many teams in the 2026 World Cup?" "Which countries are hosting?"

**Groups**: "Who is leading Group E?" "Which teams are eliminated from Group C?" "What's the goal difference for Brazil?"

**Matches**: "What was the score of the USA vs Belgium match?" "When is the next match?" "Which matches went to penalties?" "Who won the opening match?"

**Teams**: "Which team has the most goals?" "Which team has the best possession?" "Which team has the most yellow cards?" "What is Argentina's win rate?"

**Players**: "Who is the top scorer?" "Which player has the most assists?" "How many goals did Messi score?" "Who got a red card?"

**Advanced**: "Which team is over-performing their xG?" "Which goalkeeper has the most saves?" "What is the most efficient finishing team?"

**Awards**: "Who is winning the Golden Boot?" "Who is the best goalkeeper?"

**Venues**: "Which stadium hosted the final?" "How many matches are in New York?"

---

## Data Sources

For live/accurate data:
1. **Wikipedia** - https://en.wikipedia.org/wiki/2026_FIFA_World_Cup (groups, results, stats tables)
2. **FIFA.com** - Official stats
3. **SofaScore/WhoScored** - Advanced metrics (xG, passes, etc.)
4. **Football-Data.co.uk** - Match data
