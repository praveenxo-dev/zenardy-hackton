from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
import random
from sqlalchemy import create_engine, text
from datetime import datetime
from pydantic import BaseModel

app = FastAPI()


class URLRequest(BaseModel):
    url: str


engine = create_engine("sqlite:///test.db", echo=True)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # change in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event():
    create_table()


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


@app.get("/stats/{shortened}")
async def stats(shortened: str):
    with engine.connect() as conn:
        result = conn.execute(
            text(
                "SELECT url, count, date, last_accessed FROM urls WHERE url_shortened = :short"
            ),
            {"short": shortened},
        ).fetchone()

        if not result:
            return {"error": "URL not found"}

        url, count, date, last_accessed = result

    return {
        "original_url": url,
        "access_count": count,
        "created_date": date,
        "last_accessed": last_accessed,
    }


@app.get("/{shortened}")
async def redirect_webpage_url(shortened: str):
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
    return RedirectResponse(url=url)


# @app.post("/create_url/shorten")
# async def shorten_url(request: URLRequest):
#     url = request.url

#     with engine.connect() as conn:
#         while True:
#             url_shortened = "".join(
#                 random.choices("abcdefghijklmnopqrstuvwxyz0123456789", k=6)
#             )

#             result = conn.execute(
#                 text("SELECT 1 FROM urls WHERE url_shortened = :short"),
#                 {"short": url_shortened},
#             ).fetchone()

#             if not result:
#                 break

#         conn.execute(
#             text("""
#                 INSERT INTO urls (url, url_shortened, count, date, last_accessed)
#                 VALUES (:url, :short, :count, :date, :last_accessed)
#             """),
#             {
#                 "url": url,
#                 "short": url_shortened,
#                 "count": 0,
#                 "date": str(datetime.now()),
#                 "last_accessed": str(datetime.now()),
#             },
#         )
#         conn.commit()

#     return {"shortened_url": url_shortened}
