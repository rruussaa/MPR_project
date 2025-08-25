# mpr2025_KN_4MI0800060_python_Windows(works on all OS)/client.py
import socket
import json
import argparse
import csv
import os
from datetime import datetime
from html import escape

HOST = "127.0.0.1"
PORT = 65432

def request_scrape(make, max_price, limit):
    req = {"cmd": "SCRAPE", "make": make, "max_price": max_price, "limit": limit}
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))
    s.sendall(json.dumps(req, ensure_ascii=False).encode("utf-8"))

    chunks = []
    while True:
        part = s.recv(65536)
        if not part:
            break
        chunks.append(part)
    s.close()

    resp = json.loads(b"".join(chunks).decode("utf-8", errors="ignore"))
    if not resp.get("ok"):
        raise RuntimeError(resp.get("error", "unknown error"))
    return resp["data"]

def save_json(rows, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)

def save_csv(rows, path):
    cols = ["title", "price", "location", "link", "image_url"]
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in cols})

def build_html(rows, out_html, meta):
    """Генерира HTML отчет с изображения (директно от image_url) ама не винаги работи :Д."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    make = escape(str(meta.get("make", "")))
    max_price = escape(str(meta.get("max_price", "")))
    limit = escape(str(meta.get("limit", "")))

    head = f"""<!doctype html>
<html lang="bg">
<head>
<meta charset="utf-8">
<title>Авто отчет – {make} (макс. цена {max_price})</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  body {{ font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif; margin: 24px; }}
  h1 {{ font-size: 1.6rem; margin: 0 0 8px; }}
  .meta {{ color: #555; margin-bottom: 16px; }}
  table {{ width: 100%; border-collapse: collapse; }}
  th, td {{ border-bottom: 1px solid #eee; padding: 10px; vertical-align: top; }}
  th {{ text-align: left; background: #fafafa; }}
  .thumb {{ width: 140px; height: 100px; object-fit: cover; border-radius: 8px; }}
  .title {{ font-weight: 600; }}
  .price {{ white-space: nowrap; }}
  .link a {{ text-decoration: none; color: #0a58ca; }}
  .link a:hover {{ text-decoration: underline; }}
  .grid {{ display: grid; grid-template-columns: 160px 1fr 140px 140px; gap: 12px; align-items: start; }}
  @media (max-width: 900px) {{
    .grid {{ grid-template-columns: 140px 1fr; }}
    .hide-sm {{ display: none; }}
  }}
</style>
</head>
<body>
<h1>Отчет: {make} (максимална цена {max_price})</h1>
<div class="meta">Генериран: {ts} • Резултати: {limit}</div>
<table>
  <thead>
    <tr>
      <th>Снимка</th>
      <th>Оферта</th>
      <th class="hide-sm">Цена</th>
      <th class="hide-sm">Описание</th>
    </tr>
  </thead>
  <tbody>
"""

    rows_html = []
    for r in rows:
        title = escape(r.get("title", ""))
        price = escape(r.get("price", ""))
        location = escape(r.get("location", ""))
        link = escape(r.get("link", ""))
        img = escape(r.get("image_url", ""))

        img_tag = f'<img class="thumb" src="{img}" alt="img">' if img else ""
        link_tag = f'<div class="link"><a href="{link}" target="_blank" rel="noopener">Кликай за да вземемш бавареца(колата, ако не е баварец)</a></div>' if link else ""

        rows_html.append(f"""
    <tr>
      <td>{img_tag}</td>
      <td><div class="title">{title}</div>{link_tag}</td>
      <td class="price hide-sm">{price}</td>
      <td class="hide-sm">{location}</td>
    </tr>
""")

    tail = """  </tbody>
</table>
</body>
</html>
"""
    html = head + "".join(rows_html) + tail
    with open(out_html, "w", encoding="utf-8") as f:
        f.write(html)

def main():

    import sys
    parser = argparse.ArgumentParser()
    parser.add_argument("--make", default=None, help="марка (по подразбиране: bmw)")
    parser.add_argument("--max_price", type=int, default=None, help="максимална цена (по подразбиране: 3000)")
    parser.add_argument("--limit", type=int, default=None, help="брой резултати")
    parser.add_argument("--out_json", default="cars.json")
    parser.add_argument("--out_csv", default="cars.csv")
    parser.add_argument("--out_html", default="report.html")
    args = parser.parse_args()

    make = args.make or input("Марка !!!!вижте как се пише марката в mobile например мерцедес е mercedes-benz(по подразбиране bmw): ").strip() or "bmw"

    def ask_int(prompt, default):
        val = input(f"{prompt} (по подразбиране {default}): ").strip()
        if not val:
            return default
        try:
            return int(val)
        except ValueError:
            print(" Използвам по подразбиране.")
            return default

    max_price = args.max_price if args.max_price is not None else ask_int("Максимална цена", 3000)
    limit = args.limit if args.limit is not None else ask_int("Колко резултата желаеш", 20)

    rows = request_scrape(make, max_price, limit)

    print("!!!!! БАВАРЕЦ СКРЕЙПЪР !!!!!")

    print(f"Получени {len(rows)} резултата")
    for r in rows[:5]:
        print(f"- {r.get('title','')} | {r.get('price','')} | {r.get('location','')}")

    save_json(rows, args.out_json)
    save_csv(rows, args.out_csv)
    build_html(rows, args.out_html, {"make": make, "max_price": max_price, "limit": limit})

    print(f"Записах JSON → {args.out_json}")
    print(f"Записах CSV  → {args.out_csv}")
    print(f"HTML отчет   → {args.out_html}  (отвори с браузър)")
    if os.name == "posix":
        print("Подсказка (Linux/macOS): xdg-open report.html или open report.html")
    else:
        print("Подсказка (Windows): просто двойно кликни report.html")

if __name__ == "__main__":
    main()

#дано тръгне и на вашата машина (на моята върви без проблем)
