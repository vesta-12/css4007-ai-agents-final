"""Run locally with python3 src/inbox_server.py."""
import argparse
import csv
import json
import os
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit

from dotenv import load_dotenv
from openai import OpenAI, APIError

import bondscope
import evidence

ASSETS = {"/mark.svg": ("mark.svg", "image/svg+xml"), "/": ("index.html", "text/html"), "/inbox.css": ("inbox.css", "text/css"),
          "/inbox.js": ("inbox.js", "text/javascript")}
REVIEW_LOCK = threading.Lock()


def material_preview(name):
    if not name.lower().endswith(".csv"):
        return evidence.find_evidence(bondscope.CASE, name, "")

    result = {"file": name, "status": "unavailable", "evidence": []}
    if name not in {item["file"] for item in bondscope.list_materials(bondscope.CASE)}:
        return result
    path = bondscope.ROOT / "cases" / bondscope.CASE / name
    with path.open(encoding="utf-8-sig", newline="") as handle:
        if os.fstat(handle.fileno()).st_size > 512_000:
            return dict(result, status="size_limit")
        header_line = handle.readline().rstrip("\r\n")
        handle.seek(0)
        reader = csv.reader(handle, strict=True)
        records = []
        start_line = 1
        for cells in reader:
            records.append({"line": start_line, "cells": cells})
            start_line = reader.line_num + 1
    if header_line.strip():
        result["evidence"].append({"file": name, "line": 1, "quote": header_line})
    return dict(result, status="found" if records else "no_match", table=records)


def local_symbols():
    if sys.platform != "darwin":
        return {}
    try:
        result = subprocess.run(
            ["/usr/bin/osascript", "-l", "JavaScript", str(bondscope.ROOT / "frontend" / "macos-symbols.js")],
            capture_output=True, text=True, check=True, timeout=4,
        )
        return json.loads(result.stdout)
    except (OSError, subprocess.SubprocessError, ValueError):
        return {}


class Inbox(BaseHTTPRequestHandler):
    def send_body(self, code, body, mime):
        self.send_response(code)
        self.send_header("Content-Type", mime + "; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def json(self, code, data):
        self.send_body(code, json.dumps(data, ensure_ascii=False).encode(), "application/json")

    def allowed_hosts(self):
        return {f"127.0.0.1:{self.server.server_port}", f"localhost:{self.server.server_port}"}

    def do_GET(self):
        if self.headers.get("Host") not in self.allowed_hosts():
            return self.json(403, {"error": "Недопустимый адрес запроса."})
        url = urlsplit(self.path)
        if url.path in ASSETS:
            name, mime = ASSETS[url.path]
            return self.send_body(200, (bondscope.ROOT / "frontend" / name).read_bytes(), mime)
        try:
            if url.path == "/api/symbols":
                return self.json(200, self.server.symbols)
            if url.path == "/api/case":
                return self.json(200, {"name": "BondScope", "question": evidence.QUESTION,
                    "model": os.getenv("LLM_MODEL") or "gpt-4.1-mini",
                    "materials": bondscope.list_materials(bondscope.CASE)})
            if url.path == "/api/material":
                name = parse_qs(url.query).get("name", [""])[0]
                data = material_preview(name)
                return self.json(200 if data["status"] in {"found", "no_match"} else 404, data)
        except csv.Error:
            return self.json(422, {"error": "Не удалось разобрать структуру CSV."})
        except (ValueError, OSError):
            return self.json(400, {"error": "Материал недоступен."})
        self.json(404, {"error": "Не найдено."})

    def do_POST(self):
        if self.path != "/api/review":
            return self.json(404, {"error": "Не найдено."})
        host = self.headers.get("Host")
        if (host not in self.allowed_hosts() or self.headers.get("Origin") != f"http://{host}"
                or self.headers.get("X-BondScope-Action") != "review"):
            return self.json(403, {"error": "Запускайте проверку из локального интерфейса."})
        key = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
        if not key:
            return self.json(503, {"error": "Добавьте LLM_API_KEY в .env и перезапустите сервер."})
        if not REVIEW_LOCK.acquire(blocking=False):
            return self.json(409, {"error": "Проверка уже выполняется."})
        try:
            with OpenAI(api_key=key, timeout=45, max_retries=1) as client:
                report = evidence.review(client, os.getenv("LLM_MODEL") or "gpt-4.1-mini")
        except (APIError, ValueError, OSError) as exc:
            return self.json(502, {"error": f"Не удалось получить проверенный отчёт ({type(exc).__name__})."})
        finally:
            REVIEW_LOCK.release()
        self.json(200, report)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    load_dotenv(bondscope.ROOT / ".env")
    with ThreadingHTTPServer(("127.0.0.1", args.port), Inbox) as server:
        server.symbols = local_symbols()
        print(f"ОТК.ai: http://127.0.0.1:{server.server_port}", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
