# mpr2025_KN_4MI0800060_python_Windows(works on all OS)/server.py
import socket
import threading
import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import chardet

HOST = "127.0.0.1"
PORT = 65432
BASE = "https://www.mobile.bg"

def scrape_mobile_bg(make="bmw", min_price=3000, limit=20):
    url = f"{BASE}/obiavi/avtomobili-dzhipove/{make}?price1={min_price}"
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()

    enc = chardet.detect(resp.content)["encoding"] or "utf-8"
    html = resp.content.decode(enc, errors="ignore")
    soup = BeautifulSoup(html, "html.parser")

    items = soup.select("div.item")
    out = []
    for it in items:
        try:
            title = it.select_one(".zaglavie")
            price = it.select_one(".price")
            location = it.select_one(".text")
            link_a = it.select_one("a")
            img = it.select_one("img")

            title_txt = title.get_text(strip=True) if title else ""
            price_txt = price.get_text(strip=True) if price else ""
            location_txt = location.get_text(strip=True) if location else ""
            link = urljoin(BASE, link_a["href"]) if link_a and link_a.has_attr("href") else ""
            image_url = urljoin(BASE, img["src"]) if img and img.has_attr("src") else ""

            out.append({
                "title": title_txt,
                "price": price_txt,
                "location": location_txt,
                "link": link,
                "image_url": image_url
            })
            if len(out) >= limit:
                break
        except Exception:
            continue
    return out

def handle_client(conn, addr):
    try:
        buf = conn.recv(65536).decode("utf-8", errors="ignore")
        req = json.loads(buf)
        cmd = req.get("cmd")

        if cmd == "SCRAPE":
            make = req.get("make", "bmw")
            min_price = int(req.get("min_price", 3000))
            limit = int(req.get("limit", 20))
            data = scrape_mobile_bg(make=make, min_price=min_price, limit=limit)
            resp = {"ok": True, "data": data}
        else:
            resp = {"ok": False, "error": "unknown_command"}

        conn.sendall(json.dumps(resp, ensure_ascii=False).encode("utf-8"))
    except Exception as e:
        err = {"ok": False, "error": str(e)}
        try:
            conn.sendall(json.dumps(err, ensure_ascii=False).encode("utf-8"))
        except Exception:
            pass
    finally:
        conn.close()

def main():
    print(f"Сървъра бачка на: {HOST}:{PORT}")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((HOST, PORT))
    sock.listen()
    while True:
        conn, addr = sock.accept()
        t = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
        t.start()

if __name__ == "__main__":
    main()
