import json
import re

# Load the goalscorer data
with open("/home/erin/projects/world-cup-rag/goalscorer_module.lua") as f:
    lua_content = f.read()

# Parse goalscorers from Lua format
# Format: {"[[Player Name]]", "COUNTRY", N }
# or: {{ "[[Player Name]", "SortName" }, "COUNTRY", N }

goalscorers = []

# Extract goal scorers entries
# Pattern 1: {"[[Player Name]]", "COUNTRY", goals }
pattern1 = r'"\{\{\[\[(.*?)\]\]\]"\s*,\s*"([A-Z]+)",\s*(\d+)\s*\}'
# Pattern 2: {{ "[[Player Name", "SortName" }, "COUNTRY", goals }
pattern2 = r'\{\{\s*"\[\[(.*?)\]"\s*,\s*"\s*(.*?)\s*"\s*\}\s*,\s*"([A-Z]+)",\s*(\d+)\s*\}'

# Extract from pattern 1
for match in re.finditer(pattern1, lua_content):
    name = match.group(1)
    country = match.group(2)
    goals = int(match.group(3))
    goalscorers.append({"player": name, "country": country, "goals": goals})

# Extract from pattern 2
for match in re.finditer(pattern2, lua_content):
    name = match.group(1)
    sort_name = match.group(2)
    country = match.group(3)
    goals = int(match.group(4))
    goalscorers.append({"player": name, "country": country, "goals": goals})

# Parse own goalscorers
# Format: {"[[Player]]", "COUNTRY", { own_goals, opponents } }
own_goalscorers = []
og_pattern = r'"\{\{\[\[(.*?)\]\]\]"\s*,\s*"([A-Z]+)",\s*\{\s*(\d+)\s*,\s*"([^"]+)"'
for match in re.finditer(og_pattern, lua_content):
    player = match.group(1)
    country = match.group(2)
    own_goals = int(match.group(3))
    opponents = match.group(4)
    own_goalscorers.append({
        "player": player,
        "country": country,
        "own_goals": own_goals,
        "against": opponents
    })

# Sort goalscorers by goals descending
goalscorers.sort(key=lambda x: (-x["goals"], x["player"]))

print(f"Total goalscorers: {len(goalscorers)}")
print(f"Top 10 goalscorers:")
for i, gc in enumerate(goalscorers[:10]):
    print(f"  {i+1}. {gc['player']} ({gc['country']}) - {gc['goals']} goals")

print(f"\nTotal own goalscorers: {len(own_goalscorers)}")
for og in own_goalscorers:
    print(f"  {og['player']} ({og['country']}) - {og['own_goals']} own goals vs {og['against']}")

# Also extract updated data
# data.updated = { finals = { 102, "2026-07-15", "1/1" } }
updated_match = re.search(r'finals\s*=\s*\{\s*(\d+),\s*"([^"]+)"', lua_content)
if updated_match:
    total_matches = int(updated_match.group(1))
    update_date = updated_match.group(2)
    print(f"\nTournament data as of: {update_date}")
    print(f"Total matches played: {total_matches}")

# Save parsed goalscorer data
goalscorer_data = {
    "tournament_info": {
        "name": "2026 FIFA World Cup",
        "hosts": ["Canada", "Mexico", "United States"],
        "dates": "June 11 – July 19, 2026",
        "teams": 48,
        "groups": ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L"],
        "total_matches": 102,  # matches played as of data extraction
        "total_goals": 297,   # from earlier summary
        "data_updated": update_date,
        "active_countries": ["ARG", "ENG", "FRA", "ESP"]
    },
    "top_scorers": goalscorers[:20],  # Golden Boot race
    "top_scorers_full": goalscorers,
    "own_goals": own_goalscorers,
    "active_teams": goalscorers  # players from active teams
}

with open("/home/erin/projects/world-cup-rag/goalscorers_data.json", "w") as f:
    json.dump(goalscorer_data, f, indent=2)

print("\nSaved to /home/erin/projects/world-cup-rag/goalscorers_data.json")
