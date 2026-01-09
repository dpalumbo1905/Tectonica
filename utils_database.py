import sqlite3
import json
import os
from datetime import datetime

DB_FILE = "tectonica_memory.db"

def init_db():
    """Initializes the SQL database for Projects and a JSON store for AI Learning."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # Create Projects Table
    c.execute('''CREATE TABLE IF NOT EXISTS projects 
                 (id INTEGER PRIMARY KEY, name TEXT UNIQUE, created_at TEXT)''')
    # Create Assets Table
    c.execute('''CREATE TABLE IF NOT EXISTS assets 
                 (id INTEGER PRIMARY KEY, project_id INTEGER, name TEXT, 
                  type TEXT, discipline TEXT, scale TEXT, file_path TEXT)''')
    conn.commit()
    conn.close()
    
    # Initialize Learning Memory (The "Brain")
    if not os.path.exists("ai_learning_memory.json"):
        with open("ai_learning_memory.json", "w") as f:
            json.dump({"false_positives": [], "confirmed_clashes": []}, f)

def save_project(name):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO projects (name, created_at) VALUES (?, ?)", (name, datetime.now()))
        conn.commit()
    except sqlite3.IntegrityError:
        pass # Project exists
    conn.close()

def get_projects():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT name FROM projects")
    data = [row[0] for row in c.fetchall()]
    conn.close()
    return data

def teach_ai(description, decision):
    """
    Saves user feedback to the JSON memory.
    decision: 'safe' (False Positive) or 'clash' (Confirmed)
    """
    with open("ai_learning_memory.json", "r+") as f:
        memory = json.load(f)
        
        entry = {
            "description": description,
            "learned_at": str(datetime.now())
        }
        
        if decision == "safe":
            memory["false_positives"].append(entry)
        else:
            memory["confirmed_clashes"].append(entry)
            
        f.seek(0)
        json.dump(memory, f, indent=4)

def get_ai_memory_context():
    """Retrieves learned rules to inject into the AI Prompt."""
    if not os.path.exists("ai_learning_memory.json"):
        return ""
    
    with open("ai_learning_memory.json", "r") as f:
        memory = json.load(f)
        
    false_positives = [m['description'] for m in memory['false_positives']]
    
    if not false_positives:
        return ""
        
    # This string will be fed to GPT-4o
    return f"LEARNED RULES (IGNORE THESE): The user has explicitly marked these scenarios as SAFE/NOT CLASHES in the past: {'; '.join(false_positives)}."