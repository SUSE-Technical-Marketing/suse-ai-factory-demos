import requests
from bs4 import BeautifulSoup
import json
import re

url = "https://en.wikipedia.org/wiki/2026_FIFA_World_Cup"
headers = {"User-Agent": "Mozilla/5.0 (World Cup RAG Data Collector)"}
response = requests.get(url, headers=headers, timeout=30)
response.raise_for_status()
soup = BeautifulSoup(response.text, 'html.parser')

# Find all footballbox elements
football_elements = []
for elem in soup.find_all(True):
    classes = elem.get('class', [])
    if classes and 'footballbox' in classes:
        football_elements.append(elem)

print(f"Found {len(football_elements)} footballbox elements\n")

matches = []
for idx, elem in enumerate(football_elements):
    # Date
    date_div = elem.find(class_='fdate')
    date_parts = []
    for child in date_div.children:
        if isinstance(child, str):
            child = child.strip()
            if child and child not in ('', '(', ')'):
                date_parts.append(child)
    date = ' '.join(date_parts)
    
    # Time
    time_div = elem.find(class_='ftime')
    time_parts = []
    for child in time_div.children:
        if isinstance(child, str):
            child = child.strip()
            if child and child not in ('', '(', ')'):
                time_parts.append(child)
    time = ' '.join(time_parts)
    
    # Home team
    home_th = elem.find('th', class_='fhome')
    home_a = home_th.find('a') if home_th else None
    home = home_a.get_text(strip=True) if home_a else ''
    
    # Score
    score_th = elem.find('th', class_='fscore')
    score_text = score_th.get_text(strip=True).replace('\u2013', '-').replace('\u2212', '-') if score_th else '0-0'
    score_parts = re.split(r'[-–]', score_text)
    home_score = int(score_parts[0]) if len(score_parts) >= 1 and score_parts[0].isdigit() else 0
    away_score = int(score_parts[1]) if len(score_parts) >= 2 and score_parts[1].isdigit() else 0
    
    # Away team
    away_th = elem.find('th', class_='faway')
    away_a = away_th.find('a') if away_th else None
    away = away_a.get_text(strip=True) if away_a else ''
    
    # Get goals from fhgoal and fagoal
    goals = []
    
    # Home goals
    fhgoal = elem.find('td', class_='fhgoal')
    if fhgoal:
        for li in fhgoal.find_all('li'):
            player_a = li.find('a')
            player = player_a.get_text(strip=True) if player_a else ''
            minute_span = li.find('span')
            minute = ''
            if minute_span:
                for ms in minute_span.children:
                    if isinstance(ms, str):
                        ms = ms.strip()
                        if ms and ms != '':
                            minute = ms
            if player:
                goals.append({'player': player, 'minute': minute, 'team': home})
    
    # Away goals
    fagoal = elem.find('td', class_='fagoal')
    if fagoal:
        for li in fagoal.find_all('li'):
            player_a = li.find('a')
            player = player_a.get_text(strip=True) if player_a else ''
            minute_span = li.find('span')
            minute = ''
            if minute_span:
                for ms in minute_span.children:
                    if isinstance(ms, str):
                        ms = ms.strip()
                        if ms and ms != '':
                            minute = ms
            if player:
                goals.append({'player': player, 'minute': minute, 'team': away})
    
    # Venue
    fright = elem.find(class_='fright')
    venue_div = fright.find('div')  # First div with location
    venue_name = ''
    venue_city = ''
    if venue_div:
        links = venue_div.find_all('a')
        if len(links) >= 2:
            venue_name = links[0].get_text(strip=True)
            venue_city = links[1].get_text(strip=True)
    venue = f"{venue_name}, {venue_city}" if venue_name else ''
    
    # Attendance
    attendance_divs = fright.find_all('div')
    attendance = 0
    if len(attendance_divs) >= 2:
        att_text = attendance_divs[1].get_text(strip=True)
        att_m = re.search(r'Attendance:\s*(\d+(?:,\d+)*)', att_text)
        if att_m:
            attendance = int(att_m.group(1).replace(',', ''))
    
    # Referee
    ref_div = None
    if len(attendance_divs) >= 3:
        ref_div = attendance_divs[2]
    if not ref_div and len(attendance_divs) >= 2:
        ref_text = attendance_divs[1].get_text()
        if 'Referee' in ref_text:
            ref_div = attendance_divs[1]
        elif 'Attendance' in ref_text:
            ref_div = attendance_divs[2] if len(attendance_divs) > 2 else None
    
    referee = ''
    if ref_div:
        ref_a = ref_div.find('a')
        if ref_a:
            # Skip "Portugal" or federation name - get the referee name
            full_text = ref_div.get_text(strip=True)
            ref_parts = full_text.split('(')
            referee = ref_parts[0].strip().replace('Referee:', '').strip()
            # Clean up
            if 'referee)' in referee.lower():
                referee = referee.split('referee)')[0].strip()
            if ',' in referee:
                referee = referee.split(',')[0].strip()
    
    # Check for penalty info in goals row
    penalty_score = None
    fgoals_row = elem.find('tr', class_='fgoals')
    if fgoals_row:
        pen_m = re.search(r'\((\d+-\d+)\s*p\.\)', fgoals_row.get_text())
        if pen_m:
            penalty_score = pen_m.group(1)
    
    # Result type
    result_type = 'normal'
    if penalty_score:
        result_type = 'penalties'
    
    matches.append({
        'date': date,
        'time': time,
        'home_team': home,
        'home_score': home_score,
        'away_score': away_score,
        'away_team': away,
        'result_type': result_type,
        'penalty_score': penalty_score,
        'goals': goals,
        'venue': venue,
        'attendance': attendance,
        'referee': referee
    })

print(f"Total matches extracted: {len(matches)}")
for i, m in enumerate(matches):
    penalty_str = f" ({m['penalty_score']} p.)" if m['penalty_score'] else ""
    print(f"  [{i:3d}] {m['date']} | {m['home_team']:20s} {m['home_score']}-{m['away_score']}{penalty_str} {m['away_team']:20s}")
    if m['goals']:
        goal_list = [f"{g['player']} ({g['team']}) {g['minute']}'" for g in m['goals']]
        print(f"       Goals: {', '.join(goal_list)}")
    print(f"       {m['venue']} | Att: {m['attendance']} | Ref: {m['referee']}")

# Save
with open('/home/erin/projects/world-cup-rag/matches.json', 'w') as f:
    json.dump(matches, f, indent=2)
print(f"\nSaved {len(matches)} matches to matches.json")
