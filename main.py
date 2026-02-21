from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
import random
from sqlalchemy import create_engine, text
from datetime import datetime
from pydantic import BaseModel
from contextlib import asynccontextmanager
from fastapi.templating import Jinja2Templates
from fastapi import Request


engine = create_engine(
    "sqlite:///test.db", echo=True, connect_args={"check_same_thread": False}
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_table()
    yield


app = FastAPI(lifespan=lifespan)


class URLRequest(BaseModel):
    url: str


# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],  # change in production
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )


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


templates = Jinja2Templates(directory="templates")


@app.get("/")
async def main(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


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
    if len(shortened) != 6:
        return {"error": "Invalid shortened URL"}

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


@app.post("/create_url/shorten")
async def shorten_url(request: URLRequest):
    url = request.url

    with engine.connect() as conn:
        while True:
            url_shortened = "".join(
                random.choices("abcdefghijklmnopqrstuvwxyz0123456789", k=6)
            )

            result = conn.execute(
                text("SELECT url_shortened FROM urls WHERE url = :url"),
                {"url": url},
            ).fetchone()

            if result:
                return {"shortened_url": result[0]}

            conn.execute(
                text("""
                INSERT INTO urls (url, url_shortened, count, date, last_accessed)
                VALUES (:url, :short, :count, :date, :last_accessed)
            """),
                {
                    "url": url,
                    "short": url_shortened,
                    "count": 0,
                    "date": str(datetime.now()),
                    "last_accessed": str(datetime.now()),
                },
            )
            conn.commit()

    return {"shortened_url": url_shortened}
