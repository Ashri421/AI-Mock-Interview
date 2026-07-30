import sqlite3


# -----------------------------
# Create Database
# -----------------------------
def create_database():

    connection = sqlite3.connect("database.db")
    cursor = connection.cursor()

    # Candidates Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT,
            job_role TEXT,
            experience TEXT
        )
    """)

    # Answers Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS answers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            candidate_id INTEGER,
            question TEXT,
            answer TEXT,
            score INTEGER
        )
    """)

    connection.commit()
    connection.close()


# -----------------------------
# Save Candidate
# -----------------------------
def save_candidate(name, email, job_role, experience):

    connection = sqlite3.connect("database.db")
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO candidates
        (name, email, job_role, experience)
        VALUES (?, ?, ?, ?)
    """, (name, email, job_role, experience))

    candidate_id = cursor.lastrowid

    connection.commit()
    connection.close()

    return candidate_id


# -----------------------------
# Save Answer
# -----------------------------
def save_answer(candidate_id, question, answer):

    connection = sqlite3.connect("database.db")
    cursor = connection.cursor()

    # Simple AI Score
    score = min(len(answer.split()), 10)

    cursor.execute("""
        INSERT INTO answers
        (candidate_id, question, answer, score)
        VALUES (?, ?, ?, ?)
    """, (candidate_id, question, answer, score))

    connection.commit()
    connection.close()


# -----------------------------
# Get All Candidates
# -----------------------------
def get_candidates():

    connection = sqlite3.connect("database.db")
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM candidates")

    candidates = cursor.fetchall()

    connection.close()

    return candidates


# -----------------------------
# Get One Candidate
# -----------------------------
def get_candidate(candidate_id):

    connection = sqlite3.connect("database.db")
    cursor = connection.cursor()

    cursor.execute(
        "SELECT * FROM candidates WHERE id=?",
        (candidate_id,)
    )

    candidate = cursor.fetchone()

    connection.close()

    return candidate


# -----------------------------
# Get Answers of One Candidate
# -----------------------------
def get_candidate_answers(candidate_id):

    connection = sqlite3.connect("database.db")
    cursor = connection.cursor()

    cursor.execute("""
        SELECT question, answer, score
        FROM answers
        WHERE candidate_id=?
    """, (candidate_id,))

    answers = cursor.fetchall()

    connection.close()

    return answers


# -----------------------------
# Calculate Overall Score
# -----------------------------
def get_total_score(candidate_id):

    connection = sqlite3.connect("database.db")
    cursor = connection.cursor()

    cursor.execute("""
        SELECT SUM(score)
        FROM answers
        WHERE candidate_id=?
    """, (candidate_id,))

    total = cursor.fetchone()[0]

    connection.close()

    if total is None:
        total = 0

    return total


# -----------------------------
# Calculate Percentage
# -----------------------------
def get_percentage(candidate_id):

    total = get_total_score(candidate_id)

    percentage = (total / 50) * 100

    return percentage
# -----------------------------
# Delete Candidate
# -----------------------------
def delete_candidate(candidate_id):

    connection = sqlite3.connect("database.db")
    cursor = connection.cursor()

    # Delete candidate answers
    cursor.execute(
        "DELETE FROM answers WHERE candidate_id=?",
        (candidate_id,)
    )

    # Delete candidate
    cursor.execute(
        "DELETE FROM candidates WHERE id=?",
        (candidate_id,)
    )

    connection.commit()
    connection.close()

create_database()