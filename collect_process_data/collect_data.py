import requests
import json
import time



def get_players_by_page(page: int, season_code="pvp_rta_ss18", world_code="all", lang="en"):
    """
    Fetch 10 players from the Epic7 ranking API for a specific page.
    
    :param page: Page number (1 = top 1-10, 2 = 11-20, ... up to 10 = 91-100)
    :param season_code: Season code (default = current RTA season)
    :param world_code: Server code ("all", "world_eu", "world_asia", "world_kor", "world_global")
    :param lang: Language ("en", "fr", etc.)
    :return: list of player dictionaries
    """
    URL = "https://epic7.onstove.com/gg/gameApi/getWorldUserRankingDetail"

    params = {
        "season_code": season_code,
        "world_code": world_code,
        "current_page": page,
        "lang": lang
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:143.0) Gecko/20100101 Firefox/143.0",
        "Referer": "https://epic7.onstove.com/en/gg/rank/server",
        "Content-Type": "application/json;charset=UTF-8",
        "Origin": "https://epic7.onstove.com",
        "Accept": "application/json, text/javascript, */*; q=0.01",
    }

    resp = requests.post(URL, params=params, headers=headers, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    return data.get("result_body", [])

def getBattlePlayer(nick_no, world_code, page=1, lang="en"):
    """
    Fetch detailed battle player information from the Epic7 API.
    
    :param nick_no: Player's nickname number
    :param world_code: Server code
    :param page: Page number for additional data (default = 1)
    :param lang: Language ("en", "fr", etc.)
    :return: Player detail dictionary
    """
    URL = "https://epic7.onstove.com/gg/gameApi/getBattleList"

    params = {
        "nick_no": nick_no,
        "world_code": world_code,
        "current_page": page,
        "lang": lang
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:143.0) Gecko/20100101 Firefox/143.0",
        "Referer": f"https://epic7.onstove.com/en/gg/user/{nick_no}",
        "Content-Type": "application/json;charset=UTF-8",
        "Origin": "https://epic7.onstove.com",
        "Accept": "application/json, text/javascript, */*; q=0.01",
    }

    resp = requests.post(URL, params=params, headers=headers, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    return data.get("result_body", {})

def transformBattleData(battle_data):
    """
    Return a simplified JSON with only the relevant fields:
    pick_order, hero_code, artifact, and equip for both teams
    for all battles in battle_list.
    """
    results = []

    for battle in battle_data.get("battle_list", []):
        result = {}

        teamBattleInfo_str = battle.get("teamBettleInfo")
        teamBattleInfoenemy_str = battle.get("teamBettleInfoenemy")
        mydeck = battle.get("my_deck")
        enemydeck = battle.get("enemy_deck")

        # Determine first pick
        if mydeck and enemydeck:
            if(len(mydeck.get("hero_list", [])) == 0 or len(enemydeck.get("hero_list", [])) == 0):
                break
            if mydeck['hero_list'][0].get("first_pick") == 1:
                result["first_pick"] = "my_team"
            elif enemydeck['hero_list'][0].get("first_pick") == 1:
                result["first_pick"] = "enemy_team"
            else:
                result["first_pick"] = "unknown"

        # Determine winner
        if battle.get("iswin") == 1:
            result["winner"] = "my_team"
        elif battle.get("iswin") == 2:
            result["winner"] = "enemy_team"
        else:
            result["winner"] = "unknown"

        # Parse my team info
        if teamBattleInfo_str:
            try:
                teamBattleInfo = json.loads("{" + teamBattleInfo_str + "}")
                result["my_team"] = [
                    {
                        "pick_order": hero["pick_order"],
                        "hero_code": hero["hero_code"],
                        "artifact": hero["artifact"],
                        "equip": hero["equip"],
                        "banned": (
                            mydeck["hero_list"][hero["pick_order"] - 1].get("ban", 0)
                            if mydeck and "hero_list" in mydeck and len(mydeck["hero_list"]) >= hero["pick_order"]
                            else 0
                        )
                    }
                    for hero in teamBattleInfo.get("my_team", [])
                ]
            except json.JSONDecodeError as e:
                print("Error parsing teamBettleInfo:", e)
                result["my_team"] = []
        else:
            print("No teamBattleInfo data found.")
            result["my_team"] = []

        # Parse enemy team info
        if teamBattleInfoenemy_str:
            try:
                teamBattleInfoenemy = json.loads("{" + teamBattleInfoenemy_str + "}")
                result["enemy_team"] = [
                    {
                        "pick_order": hero["pick_order"],
                        "hero_code": hero["hero_code"],
                        "artifact": hero["artifact"],
                        "equip": hero["equip"],
                        "banned": (
                            enemydeck["hero_list"][hero["pick_order"] - 1].get("ban", 0)
                            if enemydeck and "hero_list" in enemydeck and len(enemydeck["hero_list"]) >= hero["pick_order"]
                            else 0
                        )
                    }
                    for hero in teamBattleInfoenemy.get("my_team", [])
                ]
            except json.JSONDecodeError as e:
                print("Error parsing teamBettleInfoenemy:", e)
                result["enemy_team"] = []
        else:
            print("No teamBattleInfoenemy data found.")
            result["enemy_team"] = []

        results.append(result)

    return results

def getBattleData(all_players, first_page=1, number_of_pages=3):
    all_battle_data = []

    # Load existing data if available
    try:
        with open("battle_data.json", "r") as f:
            all_battle_data = json.load(f)
            print(f"Loaded {len(all_battle_data)} battles from existing file.")
    except FileNotFoundError:
        print("No existing battle data file found, fetching data from API.")

    total_fetched = len(all_battle_data)

    for player_index, player in enumerate(all_players, start=1):
        nick_no = player.get("nick_no")
        world_code = player.get("world_code")
        if not (nick_no and world_code):
            print(f"Skipping player with missing nick_no or world_code: {player}")
            continue

        print(f"\n=== Processing player {player_index}/{len(all_players)} (nick_no={nick_no}) ===")

        for page in range(first_page, first_page + number_of_pages):
            success = False
            while not success:
                try:
                    battle_data = getBattlePlayer(nick_no, world_code, page)
                    transformed_data = transformBattleData(battle_data)
                    all_battle_data.extend(transformed_data)
                    total_fetched += len(transformed_data)
                    print(f"Page {page} done for {nick_no}. Total battles so far: {total_fetched}")
                    success = True
                    time.sleep(2)  # Be polite to the server

                except requests.exceptions.ReadTimeout:
                    print(f"[Timeout] Player {nick_no}, page {page}. Waiting 2 minutes before retry...")
                    time.sleep(120)

                except requests.exceptions.RequestException as e:
                    print(f"[Network error] {e}. Waiting 2 minutes before retry...")
                    time.sleep(120)

        # Save progress after each player
        with open("battle_data.json", "w") as f:
            json.dump(all_battle_data, f, indent=2)
        print(f"Progress saved after player {nick_no} ({len(all_battle_data)} total battles).")

    # Final save
    with open("battle_data.json", "w") as f:
        json.dump(all_battle_data, f, indent=2)
    print(f"Done. Saved {len(all_battle_data)} battles in 'battle_data.json'.")

def getHeroNames(page=1, grade_code="master", season_code="pvp_rta_ss18", lang="en"):
    URL = "https://epic7.onstove.com/gg/gameApi/getPopularHero"
    params = {
        "season_code": season_code,
        "grade_code": grade_code,
        "current_page": page,
        "lang": lang
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:143.0) Gecko/20100101 Firefox/143.0",
        "Referer": "https://epic7.onstove.com/en/gg/hero",
        "Content-Type": "application/json;charset=UTF-8",
        "Origin": "https://epic7.onstove.com",
        "Accept": "application/json, text/javascript, */*; q=0.01",
    }

    resp = requests.post(URL, params=params, headers=headers, timeout=10)
    resp.raise_for_status()
    return resp.json()

def collect_all_heroes(pages=15):
    hero_dict = {}  # dictionnaire pour éviter les doublons

    for page in range(1, pages + 1):
        print(f"Page {page}...")
        data = getHeroNames(page=page)

        if "result_body" not in data:
            break

        for entry in data["result_body"]:
            hero_names = entry.get("hero_names", {})
            for code, name in hero_names.items():
                hero_dict[code] = name  # écrase les doublons automatiquement

    return hero_dict
    
if __name__ == "__main__":
    '''all_players = []

    #if the top_100_players.json file exists, load it
    try:
        with open("../data/top_100_players.json", "r") as f:
            all_players = json.load(f)
            print(f"Loaded {len(all_players)} players from existing file.")
    except FileNotFoundError:
        print("No existing file found, fetching data from API.")
    
    if len(all_players) < 100:
        all_players = []  # Clear if less than 100 to refetch
        # Loop through 10 pages (10 players each) to get top 100
        for page in range(1, 11):
            players = get_players_by_page(page)
            all_players.extend(players)

        # Save to a json file (open or create)
        with open("../data/top_100_players.json", "w") as f:
            json.dump(all_players, f, indent=2)


    listofdict = lambda d: {k: v for k, v in d.items() if k in ['nick_no', 'world_code']}
    print([listofdict(p) for p in all_players])
    print(f"Total players fetched: {len(all_players)}")

   # getBattleData(all_players, first_page=1, number_of_pages=10)

    '''

    heroes = collect_all_heroes(pages=30)

    print("Héros collectés :")
    for code, name in sorted(heroes.items()):
        print(f"{code}: {name}")

    print(f"\nTotal unique heroes: {len(heroes)}")

    with open("../data/heroes.json", "w", encoding="utf-8") as f:
        json.dump(heroes, f, ensure_ascii=False, indent=4)

    print("Fichier 'heroes.json' sauvegardé avec succès !")




    
            