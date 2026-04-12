import json
import pandas as pd

#Load game_scores.json
def load_scores():
    with open("game_scores.json", "r") as f:
        raw_text = f.read().strip()
        saved_scores = json.loads(raw_text)
    return saved_scores

#Save scorse to game_scores.json
def save_scores(saved_scores):
    with open("game_scores.json", "w") as f:
        json.dump(saved_scores, f, indent=2)

#Load projected records from projected_records.csv
def load_projections():
    with open('projected_records.csv', 'r', encoding='utf-8') as f:
        df = pd.read_csv(f)
        projections = df.to_dict(orient='records')    
    return projections 