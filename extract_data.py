# -*- coding: utf-8 -*-
"""
Created on Thu Feb  1 16:51:34 2018

@author: Sergio
"""

# Obtener partidas y clasificarlas según la liga en la que se juegue

import requests # para hacer peticiones http
import queue # cola para acc_Ids
import bisect # ordenar cola para optimizar
import random

key1 = "RGAPI-0329819f-e5c4-4d89-b3b7-2221976d6e3b" # spelldown
key2 = "RGAPI-7d84f0cd-55ad-4f03-948f-bc25b71c3a1e" #sean beathurne
key3 = "RGAPI-10251a3a-aef5-4653-a027-7e419bd65695" # garden
key4 = "RGAPI-e6b20e34-1321-4a2a-9f1d-2e853c271f02" # daion
key = key1;
n_key = 1;

def change_key(key, n_key):
    if n_key == 1:
        key = key2
        n_key = 2
    elif n_key == 2:
        key = key3
        n_key = 3
    elif n_key == 3:
        key = key1
        n_key = 4
    elif n_key == 4:
        key = key4
        n_key = 1
    return key, n_key

def calculate_ligue(ligues): # For calculating the average ligue of the game
    pond_dict = {"BRONZE":0,"SILVER":5,"GOLD":15,"PLATINUM":30,"DIAMOND":50,"MASTER":75,"CHALLENGER":100}
    
    pond_list = [pond_dict[li] for li in ligues]
    if len(pond_list) <= 3: # too many unrankeds
        return -1
    else:
        return sum(pond_list)/len(pond_list)

seed_accId = 226447238 # 
max_games_per_player = 20 # max num of games per played saved

queue_account_Ids = queue.Queue(maxsize = 3000)
queue_account_Ids.put(seed_accId)

try:
    with open('games_ID.txt','r') as file:
        games_history = file.readlines()
    
    if len(games_history) > 0:
        games_history = list(map(int, games_history))
    else:
        games_history = []

except:
    games_history = []

try:
    with open('bronze.txt','r') as f:
        cur = f.readlines()
        number_games_bronze = len(cur)
except:
    number_games_bronze = 0

try:
    with open('silver.txt','r') as f:
        cur = f.readlines()
        number_games_silver = len(cur)
except:
    number_games_silver = 0

try:
    with open('gold.txt','r') as f:
        cur = f.readlines()
        number_games_gold = len(cur)
except:
    number_games_gold = 0

try:
    with open('platinum.txt','r') as f:
        cur = f.readlines()
        number_games_platinum = len(cur)
except:
    number_games_platinum = 0

try:
    with open('diamond.txt','r') as f:
        cur = f.readlines()
        number_games_diamond = len(cur)
except:
    number_games_diamond = 0
    
try:
    with open('challenger.txt','r') as f:
        cur = f.readlines()
        number_games_challenger = len(cur)
except:
    number_games_challenger = 0

print("Nº bronze: "+str(number_games_bronze))
print("Nº silver: "+str(number_games_silver))
print("Nº gold: "+str(number_games_gold))
print("Nº platinum: "+str(number_games_platinum))
print("Nº diamond: "+str(number_games_diamond))
print("Nº challenger: "+str(number_games_challenger))
print("Nº Total: "+str(len(games_history)))

all_rep = 0 # used for exit the loop when all games are repeated 
            # and no more accounts are available
test = 0
while True:
    try:
        
        # First check we have available games
        if all_rep == 1:
            if queue_account_Ids.empty() : 
                print("All games repeated/No available games")
                break
            else:
                all_rep = 0
    
        acc_Id = queue_account_Ids.get()
        url = "https://euw1.api.riotgames.com/lol/match/v3/matchlists/by-account/"+str(acc_Id)+"?api_key="+key+"&queue=420&endTime=1519252257000&beginTime=1518654700000"
        req = requests.get(url)
        player = req.json()
        if 'status' in player:
            if (test == 0):
                all_rep = 1
                test = 1
            key,n_key = change_key(key,n_key)
            continue
        totalGames = player['totalGames']
        minim = min(max_games_per_player,totalGames)
        count_rep = 0
        
        for x in random.sample(range(totalGames), minim):
            
            
            
            game_Id = player['matches'][x]['gameId']
            
            if game_Id in games_history:
                count_rep = count_rep + 1
                if (count_rep == minim):
                    all_rep = 1
                continue
            
            url = "https://euw1.api.riotgames.com/lol/match/v3/matches/"+str(game_Id)+"?api_key="+key
            req = requests.get(url)
            game = req.json()
            if 'status' in game:
                key,n_key = change_key(key,n_key)
                continue
        
            for n in random.sample(range(10), 2):
                if not queue_account_Ids.full():
                    queue_account_Ids.put(game['participantIdentities'][n]['player']['accountId'])
            
            game_list_unordered = [None]*10 # Champs are saved
            game_list = [None]*11 # # Where winner team and champs ordered are saved
            game_list[0] = 0 # team 1 wins
            ligues = [] # list that contains the ligues of players
            roles = [None]*10 # list with the roles (TOP, JUNGLE, MIDDLE, BOTTOM)
            
            
            if game['teams'][0]['win'] == "Fail":
                game_list[0] = 1
            
            for y in range(10):
                game_list_unordered[y] = game['participants'][y]['championId']
                
                lig = game['participants'][y]['highestAchievedSeasonTier']
                if lig != ("UNRANKED"):
                    ligues.append(lig)
                
                roles[y] = game['participants'][y]['timeline']['lane']
                
            ligue = calculate_ligue(ligues)
            
            # ORDENAMOS LOS CHAMPS
            for j in range(10):
                p = 0
                if j >=5:
                    p = 5
                if roles[j] == "TOP":
                    game_list[1+p] = game_list_unordered[j]
                if roles[j] == "JUNGLE":
                    game_list[2+p] = game_list_unordered[j]
                if roles[j] == "MIDDLE":
                    game_list[3+p] = game_list_unordered[j]
                if roles[j] == "BOTTOM":
                    if game['participants'][j]['timeline']['role'] == "DUO_CARRY":
                        game_list[4+p] = game_list_unordered[j]
                    else:
                        game_list[5+p] = game_list_unordered[j]
                    
            
            with open("games_ID.txt", "a") as myfile:
                myfile.write("\n"+str(game_Id))  
            
            if ligue == -1: # too many unrankeds
                bisect.insort_left(games_history,game_Id)
                continue
            if None in game_list:
                continue
                
            if ligue < 4: # Bronze
                
                with open("bronze.txt", "a") as myfile:
                    myfile.write("\n"+" ".join(map(str,game_list)))
                    number_games_bronze += 1
                    bisect.insort_left(games_history,game_Id)
                    print("Total Bronce games: "+str(number_games_bronze)+" (key"+str(n_key)+")")
                
            if 4 <= ligue < 13: # Silver
                
                with open("silver.txt", "a") as myfile:
                    myfile.write("\n"+" ".join(map(str,game_list)))
                    number_games_silver += 1
                    bisect.insort_left(games_history,game_Id)
                    print("Total Silver games: "+str(number_games_silver)+" (key"+str(n_key)+")")
                    
            if 13 <= ligue < 25: # Gold
                
                with open("gold.txt", "a") as myfile:
                    myfile.write("\n"+" ".join(map(str,game_list)))
                    number_games_gold += 1
                    bisect.insort_left(games_history,game_Id)
                    print("Total Gold games: "+str(number_games_gold)+" (key"+str(n_key)+")")
                    
            if 25 <= ligue < 45: # Platinum
                
                with open("platinum.txt", "a") as myfile:
                    myfile.write("\n"+" ".join(map(str,game_list)))
                    number_games_platinum += 1
                    bisect.insort_left(games_history,game_Id)
                    print("Total Platinum games: "+str(number_games_platinum)+" (key"+str(n_key)+")")
                    
            if 45 <= ligue < 70: # Diamond
                
                with open("diamond.txt", "a") as myfile:
                    myfile.write("\n"+" ".join(map(str,game_list)))
                    number_games_diamond += 1
                    bisect.insort_left(games_history,game_Id)
                    print("Total Diamond games: "+str(number_games_diamond)+" (key"+str(n_key)+")")
                    
            if ligue >= 70: # Challenger
                
                with open("challenger.txt", "a") as myfile:
                    myfile.write("\n"+" ".join(map(str,game_list)))
                    number_games_challenger += 1
                    bisect.insort_left(games_history,game_Id)
                    print("Total Challenger games: "+str(number_games_challenger)+" (key"+str(n_key)+")")
        
        if queue_account_Ids.empty() :
            print("No available accounts")
            
            break
        
        
    except KeyboardInterrupt:
        break
    except:
        print("Fail in Main Loop")
        continue