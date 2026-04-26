import time
import json
import requests
from bs4 import BeautifulSoup
import os
from playwright.sync_api import sync_playwright

TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

URL = "https://www.fmkorea.com/stock"

TARGETS = set(["디깅온유","방화신기","노라무","박현빈샤방샤방"])
SEEN_FILE = "seen.json"

def load_seen():
    try:
        with open(SEEN_FILE, "r") as f:
            return set(json.load(f))
    except:
        return set()

def save_seen(seen):
    with open(SEEN_FILE, "w") as f:
        json.dump(list(seen), f)

seen_posts = load_seen()

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})

def crawl():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(URL)
        page.wait_for_timeout(3000)

        html = page.content()
        browser.close()

    soup = BeautifulSoup(html, "html.parser")

    posts = []
    rows = soup.select("tbody tr")

    print("총 행 개수:", len(rows))

    for r in rows:
        try:
            author = r.select_one(".author")
            title = r.select_one(".title a")

            if not author or not title:
                continue

            nick = author.text.strip()
            title_text = title.text.strip()
            link = "https://www.fmkorea.com" + title.get("href")

            post_id = link.split("/")[-1]

            print("잡힘:", nick, title_text)

            posts.append({
                "id": post_id,
                "nick": nick,
                "title": title_text,
                "link": link
            })

        except:
            continue

    return posts

def main():
    print("🚀 봇 시작됨")
    send_telegram("봇 실행됨")

    while True:
        try:
            print("🔄 새 글 확인 중...")

            posts = crawl()

            for p in posts:
                if p["id"] in seen_posts:
                    continue

                nick = p["nick"]

                if any(t in nick for t in TARGETS):
                    msg = f"🔥 [{nick}]\n{p['title']}\n{p['link']}"
                    send_telegram(msg)

                    seen_posts.add(p["id"])
                    save_seen(seen_posts)

            time.sleep(30)

        except Exception as e:
            print("에러:", e)
            time.sleep(60)

if __name__ == "__main__":
    main()
