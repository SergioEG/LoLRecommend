# -*- coding: utf-8 -*-
"""
Created on Sun Sep 23 23:32:13 2018

@author: Sergio
"""

#################################################
##       Sistema de recomendación final        ##
#################################################

import numpy as np
import pickle
import pandas as pd
import random
###########################################################################
# Importamos estadísticas de campeones y el modelo (+ normalizador)
try:
    with open('Datos/champs_and_stats_8_3_1.txt','r') as inf:
        champs = eval(inf.read()) # champs is a Python dictionary
        champs_keys = list(champs.keys())
        n_total_champs = len(champs)
except:
    print("Error leyendo archivo")

stats_selected = ['armor','armorperlevel','attackdamage', 'attackdamageperlevel',
'attackrange','attackspeedoffset','attackspeedperlevel','hp','hpperlevel','hpregen',
'hpregenperlevel','movespeed','mp','mpperlevel','mpregen','mpregenperlevel','spellblock',
'spellblockperlevel']

num_stats = len(stats_selected)
stats = {}
for i in champs:
    stats[i] = [champs[i].get(x) for x in stats_selected]

model = pickle.load(open('Modelos/model_test.sav', 'rb'))
normalize = pickle.load(open('Modelos/normaliz.sav', 'rb'))
###########################################################################

def recom_9th(list_sel, list_poss):
    
    team = 0 # equipo al que queremos hacer la pred
    num_poss = len(list_poss)
    
    probs = [None]*num_poss
    
    for i in range(num_poss):
        poss_games = [None]*(num_poss-1)
        for j in range(num_poss):
            
            if i != j:
                if (j > i):
                    cur = j - 1
                else:
                    cur = j
                line = list(list_sel)
                line.append(list_poss[i])
                line.append(list_poss[cur])
                
                row_stats = [stats[x] for x in line] # lista cuyos elementos son las estadísticas de cada campeón de la partida
                poss_games[cur] = np.ravel(row_stats)
    
        matrix = normalize.transform(pd.DataFrame(data = poss_games))
        probabs = model.predict_proba(matrix)
        probs[i] = (probabs[:,team]).min()
    
    probs = np.array(probs)
    index_best = probs.argmax()
    
    return list_poss[index_best]

###############################################################################

def recom_10th(list_champs, list_poss):
    
    n_champs_to_check = len(list_poss)
    poss_games = [None]*n_champs_to_check
    
    for i in range(n_champs_to_check):
        
        line = list(list_champs)
        line.insert(10,champs_keys[i])
        
        row_stats = [stats[x] for x in line] # lista cuyos elementos son las estadísticas de cada campeón de la partida
        poss_games[i] = np.ravel(row_stats)
    
    matrix = normalize.transform(pd.DataFrame(data = poss_games))
    probs = model.predict_proba(matrix)
    team = 1
    index_best = (probs[:,team]).argmax()
    print(index_best)
    return "The recommended champion is: "+str(champs_keys[index_best])

###############################################################################

def get_probs(list_selected, list_possible, n_muestras, position):
    
    n_sel = len(list_selected)
    num_poss = len(list_possible)
    probs = [None]*num_poss
    
    if (n_sel in [1,4,5,8]): # Recommendation is for team blue
        team = 0
    else:
        team = 1 # Recomm is for team red
    
    for i in range(num_poss):
        line = list(list_selected) 
        line.append(list_possible[i])
        
        new_champs_poss = list(list_possible)
        new_champs_poss.remove(list_possible[i])
        
        matrix = [None]*n_muestras
        num_champs_rand = 10 - n_sel - 1
        
        for j in range(n_muestras):
            
            random_champs = random.sample(range(0,len(new_champs_poss)), num_champs_rand)
            new_random_champs = [new_champs_poss[k] for k in random_champs]
            line_extra = list(line)
            line_extra.extend(new_random_champs)
            row_stats = [stats[x] for x in line_extra] # lista cuyos elementos son las estadísticas de cada campeón de la partida
            matrix[j] = np.ravel(row_stats)
        matrix = normalize.transform(pd.DataFrame(data = matrix))
        probabs = model.predict_proba(matrix)
        probs[i] = (probabs[:,team]).mean()
    
    return probs

###############################################################################

def recom(list_sel, list_bans, position, n_samples, n_branch):
    
    # n_sel y list_poss
    n_sel = len(list_sel)
    list_poss = list(champs_keys)
    
    for i in range(n_sel): # Delete the selected champs from the list   
        list_poss.remove(list_sel[i])
        
    for i in range(len(list_bans)): # Delete the banned champs from the list
       list_poss.remove(list_bans[i])
    
    # n == 9 and n == 10 ??
    if (n_sel == 8):
        return recom_9th(list_sel, list_poss)
    if (n_sel == 9):
        return recom_10th(list_sel, list_poss)
        
    # Blue or red team?
    if (n_sel in [1,4,5,8]): # Recommendation is for team blue
        team = 0
    else:
        team = 1 # Recomm is for team red
    
    # Max or Min? --> oper
    if (n_sel in [1,3,5,7]):
        oper = "max"
    else:
        oper = "min"
    
    # Get probs
    probs = get_probs(list_sel, list_poss, n_samples, position)
    probs = np.array(probs)
    
    # Find the 'n_branch' champs with higher probs
    all_index = (-probs).argsort() # index in sorted (descendent) way
    index = all_index[0:n_branch] # select 'n_branch' of the max
    array_best = [list_poss[i] for i in index]
    
    final_probs = [None]*n_branch
    
    for cur in range(n_branch):
        champ = array_best[cur]
        list_sel_new = list(list_sel)
        list_sel_new.append(champ)
        list_poss_new = list(list_poss)
        list_poss_new.remove(champ)
        
        probs_new = get_probs(list_sel_new, list_poss_new, n_samples, -1)
        
        if oper == "max":
            final_probs[cur] = max(probs_new)
        else:
            final_probs[cur] = min(probs_new)
            
    final_probs = np.array(final_probs)
    return array_best[final_probs.argmax()]

list_sel = [54, 222, 99, 11, 98, 76, 82, 420]
list_bans = [2, 3, 5, 42, 59, 114, 106, 127, 67, 21]

print(recom(list_sel, list_bans, "sup",  50, 5))
