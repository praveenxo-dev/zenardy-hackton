import streamlit as st
import random
from sqlalchemy import create_engine, text
from datetime import datetime

# ---------- Database Setup ----------

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


create_table()

# ---------- UI ----------

st.title("🔗 URL Shortener (Streamlit Version)")

menu = st.sidebar.selectbox(
    "Choose Option",
    ["Create Short URL", "Redirect", "View Stats", "all shortened urls"],
)

# ---------- Create Short URL ----------

if menu == "Create Short URL":
    st.header("Create a Short URL")

    url = st.text_input("Enter URL")

    if st.button("Shorten URL"):
        if not url:
            st.warning("Please enter a valid URL")
        if url and not (url.startswith("http://") or url.startswith("https://")):
            st.warning("URL should start with http:// or https://")
        else:
            with engine.connect() as conn:
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
                        "date": str(datetime.now()),
                        "last_accessed": str(datetime.now()),
                    },
                )
                conn.commit()

            st.success(f"Short URL created: http://localhost:8000/{url_shortened}")
            st.code(url_shortened)


# ---------- Redirect ----------

elif menu == "Redirect":
    st.header("Redirect to Original URL")

    shortened = st.text_input("Enter shortened code")
    if shortened and len(shortened) != 6:
        st.warning("Shortened code should be 6 characters long")

    if st.button("Go"):
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT url, count FROM urls WHERE url_shortened = :short"),
                {"short": shortened},
            ).fetchone()

            if not result:
                st.error("URL not found")
            else:
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

                st.success("successfully redirected!")
                st.markdown(f"[Click here to open]({url})")


# ---------- Stats ----------

elif menu == "View Stats":
    st.header("URL Statistics")

    shortened = st.text_input("Enter shortened code for stats")

    if st.button("Get Stats"):
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT url, count, date, last_accessed
                    FROM urls
                    WHERE url_shortened = :short
                """),
                {"short": shortened},
            ).fetchone()

            if not result:
                st.error("URL not found")
            else:
                url, count, date, last_accessed = result

                st.info(f"""
                Original URL: {url}\n
                Access Count: {count}\n
                Created Date: {date}\n
                Last Accessed: {last_accessed}
                """)

elif menu == "all shortened urls":
    st.header("All Shortened URLs")

    with engine.connect() as conn:
        results = conn.execute(
            text("""
                SELECT url, url_shortened, count, date, last_accessed
                FROM urls
            """)
        ).fetchall()

        if not results:
            st.info("No URLs found")
        else:
            for url, short, count, date, last_accessed in results:
                st.info(f"""
                Original URL: {url}\n
                Shortened Code: {short}\n
                Access Count: {count}\n
                Created Date: {date}\n
                Last Accessed: {last_accessed}
                """)
