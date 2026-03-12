import json
import pandas as pd

def LoadScores():
    #Load game_scores.json
    with open("game_scores.json", "r") as f:
        saved_scores = json.load(f)    
    return saved_scores

def SaveScores(saved_scores):
    with open("game_scores.json", "w") as f:
        json.dump(saved_scores, f, indent=2)

def LoadProjections():
    #Load projections.csv
    with open('projected_records.csv', 'r') as f:
        df = pd.read_csv(f)
        projections = df.to_dict(orient='records')    
    return projections 