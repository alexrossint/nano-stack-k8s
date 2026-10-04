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
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="UTF-8">
      <title>Nano Stack</title>
      <style>
        body {{
          font-family: -apple-system, sans-serif;
          background: #121212;
          color: #e5e5e5;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          height: 100vh;
          margin: 0;
        }}
        .logo {{
          font-size: 48px;
          margin-bottom: 8px;
          opacity: 0.85;
        }}
        .title {{
          font-size: 26px;
          font-weight: 600;
          margin-bottom: 24px;
          letter-spacing: -0.3px;
          color: #d4d4d4;
        }}
        .label {{
          font-size: 10px;
          color: #737373;
          margin-bottom: 10px;
        }}
        .count {{
          font-size: 50px;
          font-weight: 700;
          color: #D3A53D;
        }}
      </style>
    </head>
    <body>
      <div class="logo">💩</div>
      <div class="title">NANO STACK</div>
      <div class="label">You are visitor number:</div>
      <div class="count">{count}</div>
    </body>
    </html>
    """

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)