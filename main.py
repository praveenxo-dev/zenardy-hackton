from fastapi import FastAPI
import random
from sqlalchemy import create_engine, text
from datetime import datetime

app = FastAPI()

engine = create_engine("sqlite:///test.db", echo=True)


def create_table():
    with engine.connect() as conn:
        conn.execute(
            text("""
            CREATE TABLE IF NOT EXISTS urls (
                id INTEGER PRIMARY KEY,
                url TEXT,
                url_shortened TEXT UNIQUE,
                count INTEGER,
                date TEXT,
                last_accessed TEXT
            )
        """)
        )
        conn.commit()


@app.get("/")
async def main():
    return {"message": "app is working"}


@app.post("/shorten")
async def shorten_url(url: str):
    create_table()

    with engine.connect() as conn:
        # Keep generating until unique
        while True:
            url_shortened = "".join(
                random.choices("abcdefghijklmnopqrstuvwxyz0123456789", k=6)
            )

            result = conn.execute(
                text("SELECT 1 FROM urls WHERE url_shortened = :short"),
                {"short": url_shortened},
            ).fetchone()

            if not result:
                break

        conn.execute(
            text("""
                INSERT INTO urls (url, url_shortened, count, date, last_accessed)
                VALUES (:url, :short, :count, :date, :last_accessed)
            """),
            {
                "url": url,
                "short": url_shortened,
                "count": 0,
                "date": str(datetime.now().date()),
                "last_accessed": str(datetime.now()),
            },
        )
        conn.commit()

    return {"shortened_url": url_shortened}


@app.get("/{shortened}")
async def redirect(shortened: str):
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT url, count FROM urls WHERE url_shortened = :short"),
            {"short": shortened},
        ).fetchone()

        if not result:
            return {"error": "URL not found"}

        url, count = result
        conn.execute(
            text("""
                UPDATE urls
                SET count = :count, last_accessed = :last_accessed
                WHERE url_shortened = :short
            """),
            {
                "count": count + 1,
                "last_accessed": str(datetime.now()),
                "short": shortened,
            },
        )
        conn.commit()

    return {"url": url}
