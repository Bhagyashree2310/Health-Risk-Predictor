import sqlite3
import os
import pandas as pd

DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'health_predictor.db')

def get_connection(db_path=DEFAULT_DB_PATH):
    """Return a connection to the SQLite database."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_path=DEFAULT_DB_PATH):
    """Initialize the SQLite database and create tables if they do not exist."""
    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
    conn = get_connection(db_path)
    cursor = conn.cursor()
    
    # Screenings table for tracking health parameters over time
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS screenings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            name TEXT NOT NULL,
            age INTEGER,
            gender TEXT,
            height REAL,
            weight REAL,
            bmi REAL,
            systolic_bp INTEGER,
            diastolic_bp INTEGER,
            glucose REAL,
            cholesterol REAL,
            smoking_status TEXT,
            alcohol_consumption TEXT,
            physical_activity TEXT,
            family_history TEXT,
            risk_score REAL,
            risk_category TEXT,
            confidence_score REAL
        )
    ''')
    
    # Goals table for saving health goals
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS goals (
            patient_name TEXT PRIMARY KEY,
            target_weight REAL,
            target_glucose REAL,
            target_systolic_bp INTEGER,
            target_diastolic_bp INTEGER
        )
    ''')
    
    # Task completions table for daily plan checklist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS task_completions (
            patient_name TEXT,
            task_label TEXT,
            completed INTEGER,
            PRIMARY KEY (patient_name, task_label)
        )
    ''')
    
    conn.commit()
    conn.close()
    print(f"Database initialized at: {db_path}")

def save_screening(patient_dict, risk_category, risk_score, confidence_score, db_path=DEFAULT_DB_PATH):
    """Save a patient screening result to the database."""
    init_db(db_path)  # Safety check
    conn = get_connection(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO screenings (
            name, age, gender, height, weight, bmi,
            systolic_bp, diastolic_bp, glucose, cholesterol,
            smoking_status, alcohol_consumption, physical_activity, family_history,
            risk_score, risk_category, confidence_score
        ) VALUES (
            ?, ?, ?, ?, ?, ?,
            ?, ?, ?, ?,
            ?, ?, ?, ?,
            ?, ?, ?
        )
    ''', (
        patient_dict.get('name', 'Anonymous'),
        patient_dict.get('age'),
        patient_dict.get('gender'),
        patient_dict.get('height'),
        patient_dict.get('weight'),
        patient_dict.get('bmi'),
        patient_dict.get('systolic_bp'),
        patient_dict.get('diastolic_bp'),
        patient_dict.get('glucose'),
        patient_dict.get('cholesterol'),
        patient_dict.get('smoking_status'),
        patient_dict.get('alcohol_consumption'),
        patient_dict.get('physical_activity'),
        patient_dict.get('family_history'),
        risk_score,
        risk_category,
        confidence_score
    ))
    
    conn.commit()
    inserted_id = cursor.lastrowid
    conn.close()
    return inserted_id

def get_screenings_history(db_path=DEFAULT_DB_PATH):
    """Retrieve all screening records as a pandas DataFrame."""
    if not os.path.exists(db_path):
        init_db(db_path)
        return pd.DataFrame() # empty DataFrame
        
    conn = get_connection(db_path)
    df = pd.read_sql_query("SELECT * FROM screenings ORDER BY timestamp DESC", conn)
    conn.close()
    return df

def clear_history(db_path=DEFAULT_DB_PATH):
    """Clear all records in the screenings table."""
    if os.path.exists(db_path):
        conn = get_connection(db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM screenings")
        conn.commit()
        conn.close()
        return True
    return False

def save_goals(name, target_weight, target_glucose, target_systolic_bp, target_diastolic_bp, db_path=DEFAULT_DB_PATH):
    """Save target goals for a patient."""
    init_db(db_path)
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO goals (patient_name, target_weight, target_glucose, target_systolic_bp, target_diastolic_bp)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(patient_name) DO UPDATE SET
            target_weight=excluded.target_weight,
            target_glucose=excluded.target_glucose,
            target_systolic_bp=excluded.target_systolic_bp,
            target_diastolic_bp=excluded.target_diastolic_bp
    ''', (name, target_weight, target_glucose, target_systolic_bp, target_diastolic_bp))
    conn.commit()
    conn.close()

def get_goals(name, db_path=DEFAULT_DB_PATH):
    """Retrieve target goals for a patient."""
    if not os.path.exists(db_path):
        init_db(db_path)
        return None
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM goals WHERE patient_name = ?", (name,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None

def save_task_completion(name, task_label, completed, db_path=DEFAULT_DB_PATH):
    """Save checked status of a daily checklist task."""
    init_db(db_path)
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO task_completions (patient_name, task_label, completed)
        VALUES (?, ?, ?)
        ON CONFLICT(patient_name, task_label) DO UPDATE SET
            completed=excluded.completed
    ''', (name, task_label, int(completed)))
    conn.commit()
    conn.close()

def get_task_completions(name, db_path=DEFAULT_DB_PATH):
    """Load all task completions for a patient."""
    if not os.path.exists(db_path):
        init_db(db_path)
        return {}
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT task_label, completed FROM task_completions WHERE patient_name = ?", (name,))
    rows = cursor.fetchall()
    conn.close()
    return {row['task_label']: bool(row['completed']) for row in rows}

def save_sample_history(db_path=DEFAULT_DB_PATH):
    """Saves realistic mock clinical history for Jane Doe to simulate trends."""
    init_db(db_path)
    conn = get_connection(db_path)
    cursor = conn.cursor()
    
    # Check to avoid inserting repeatedly
    cursor.execute("SELECT COUNT(*) as count FROM screenings WHERE name = 'Jane Doe'")
    if cursor.fetchone()['count'] >= 3:
        conn.close()
        return
        
    # Clean-up existing Jane Doe to avoid conflicts
    cursor.execute("DELETE FROM screenings WHERE name = 'Jane Doe'")
    
    # 2 months ago (Screening 1)
    cursor.execute('''
        INSERT INTO screenings (timestamp, name, age, gender, height, weight, bmi, systolic_bp, diastolic_bp, glucose, cholesterol, smoking_status, alcohol_consumption, physical_activity, family_history, risk_score, risk_category, confidence_score)
        VALUES (datetime('now', '-60 days'), 'Jane Doe', 45, 'Female', 165.0, 78.0, 28.7, 140, 90, 120.0, 230.0, 'Non-Smoker', 'Moderate', 'Moderate', 'No', 52.0, 'Moderate Risk', 0.85)
    ''')
    # 1 month ago (Screening 2)
    cursor.execute('''
        INSERT INTO screenings (timestamp, name, age, gender, height, weight, bmi, systolic_bp, diastolic_bp, glucose, cholesterol, smoking_status, alcohol_consumption, physical_activity, family_history, risk_score, risk_category, confidence_score)
        VALUES (datetime('now', '-30 days'), 'Jane Doe', 45, 'Female', 165.0, 76.5, 28.1, 137, 87, 115.0, 220.0, 'Non-Smoker', 'Moderate', 'Moderate', 'No', 48.0, 'Moderate Risk', 0.88)
    ''')
    # Current (Screening 3)
    cursor.execute('''
        INSERT INTO screenings (timestamp, name, age, gender, height, weight, bmi, systolic_bp, diastolic_bp, glucose, cholesterol, smoking_status, alcohol_consumption, physical_activity, family_history, risk_score, risk_category, confidence_score)
        VALUES (datetime('now'), 'Jane Doe', 45, 'Female', 165.0, 75.0, 27.5, 135, 85, 110.0, 215.0, 'Non-Smoker', 'Moderate', 'Moderate', 'No', 43.9, 'Moderate Risk', 0.90)
    ''')
    
    # Set default goals for Jane Doe
    cursor.execute('''
        INSERT INTO goals (patient_name, target_weight, target_glucose, target_systolic_bp, target_diastolic_bp)
        VALUES ('Jane Doe', 68.0, 90.0, 120, 80)
        ON CONFLICT(patient_name) DO UPDATE SET
            target_weight=excluded.target_weight,
            target_glucose=excluded.target_glucose,
            target_systolic_bp=excluded.target_systolic_bp,
            target_diastolic_bp=excluded.target_diastolic_bp
    ''')
    
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
