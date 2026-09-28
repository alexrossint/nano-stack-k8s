import os
import psycopg2
from flask import Flask

app = Flask(__name__)

def get_connection():
    return psycopg2.connect(
        host=os.environ.get("DB_HOST", "localhost"),
        dbname=os.environ.get("DB_NAME", "nanostack"),
        user=os.environ.get("DB_USER", "postgres"),
        password=os.environ.get("DB_PASSWORD", "postgres"),
    )

@app.route("/")
def index():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS visits (id INT PRIMARY KEY, count INT)")
    cur.execute("INSERT INTO visits (id, count) VALUES (1, 0) ON CONFLICT DO NOTHING")
    cur.execute("UPDATE visits SET count = count + 1 WHERE id = 1 RETURNING count")
    count = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return f"<h1>Nano Stack ☕</h1><p>You are visitor number {count}</p>"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)