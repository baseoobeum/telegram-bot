import time
import json
import requests
from bs4 import BeautifulSoup
import os

# =========================
# 환경 변수 (Railway에서 설정)
# =========================
TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# =========================
# 설정
# =========================
URL = "https://www.fmkorea.com/stock"

TARGETS = set(["디깅온유","방화신기","노라무","박현빈샤방샤방"])

SEEN_FILE = "seen.json"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept-Language": "ko-KR,ko;q=0.9",
    "Accept": "text/html,application/xhtml+xml",
    "Connection": "keep-alive"
}

# =========================
# 중복 관리
# =========================
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

# =========================
# 텔레그램 전송
# =========================
def send_telegram(msg):
    if not TOKEN or not CHAT_ID:
        print("❌ TOKEN 또는 CHAT_ID 없음")
        return

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": msg,
        "disable_web_page_preview": False
    }

    try:
        res = requests.post(url, data=data, timeout=10)
        print("텔레그램 응답:", res.status_code)
    except Exception as e:
        print("텔레그램 전송 실패:", e)

# =========================
# 크롤링
# =========================
def crawl():
    try:
        res = requests.get(URL, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")

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

            except Exception as e:
                print("파싱 에러:", e)
                continue

        return posts

    except Exception as e:
        print("크롤링 에러:", e)
        return []

# =========================
# 메인 루프
# =========================
def main():
    print("🚀 봇 시작됨")

    # 테스트 메시지 (처음 1회)
    send_telegram("봇 실행됨 테스트")

    while True:
        try:
            print("🔄 새 글 확인 중...")

            posts = crawl()

            for p in posts:
                if p["id"] in seen_posts:
                    continue

                nick = p["nick"]

                # 닉네임 필터 (부분 일치)
                if any(t in nick for t in TARGETS):
                    msg = f"🔥 [{nick}]\n{p['title']}\n{p['link']}"

                    print("전송됨:", msg)
                    send_telegram(msg)

                    seen_posts.add(p["id"])
                    save_seen(seen_posts)

            time.sleep(30)

        except Exception as e:
            print("메인 루프 에러:", e)
            time.sleep(60)

# =========================
# 실행
# =========================
if __name__ == "__main__":
    main()