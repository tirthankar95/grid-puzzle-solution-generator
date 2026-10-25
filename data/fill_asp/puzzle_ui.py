"""Tiny web UI to fill in ASP solutions for puzzles in asp-tbd.csv.

Shows a random puzzle whose Code column is empty, lets you write or paste ASP
code, and saves it into the Code column on submit.

Usage:
    python3 puzzle_ui.py [--csv PATH] [--port 8000]
"""

import argparse
import csv
import json
import os
import random
import tempfile
import threading
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CSV = os.path.join(HERE, "asp-tbd.csv")
FIELDS = ["Puzzle", "Key", "Code", "Solution"]

csv.field_size_limit(10**9)
lock = threading.Lock()


def load_rows(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def save_rows(path, rows):
    # Write to a temp file in the same directory, then atomically replace.
    directory = os.path.dirname(path)
    fd, tmp = tempfile.mkstemp(dir=directory, suffix=".csv")
    with os.fdopen(fd, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    os.replace(tmp, path)


def make_handler(csv_path):
    class Handler(BaseHTTPRequestHandler):
        def _send(self, status, body, content_type="application/json"):
            data = body.encode("utf-8") if isinstance(body, str) else body
            self.send_response(status)
            self.send_header("Content-Type", content_type + "; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        def _json(self, status, payload):
            self._send(status, json.dumps(payload))
        def do_GET(self):
            if self.path == "/":
                self._send(HTTPStatus.OK, PAGE, "text/html")
            elif self.path == "/api/random":
                with lock:
                    pending = [r for r in load_rows(csv_path) if not r["Code"].strip()]
                if not pending:
                    self._json(HTTPStatus.NOT_FOUND, {"error": "No puzzles without Code left."})
                    return
                row = random.choice(pending)
                self._json(HTTPStatus.OK, {"key": row["Key"], "puzzle": row["Puzzle"]})
            else:
                self._json(HTTPStatus.NOT_FOUND, {"error": "Not found"})
        def do_POST(self):
            if self.path != "/api/save":
                self._json(HTTPStatus.NOT_FOUND, {"error": "Not found"})
                return
            try:
                length = int(self.headers.get("Content-Length", 0))
                payload = json.loads(self.rfile.read(length) or b"{}")
            except (ValueError, json.JSONDecodeError):
                self._json(HTTPStatus.BAD_REQUEST, {"error": "Invalid JSON"})
                return
            key = payload.get("key", "")
            code = (payload.get("code") or "").strip()
            if not key or not code:
                self._json(HTTPStatus.BAD_REQUEST, {"error": "Both key and code are required."})
                return
            with lock:
                rows = load_rows(csv_path)
                matches = [r for r in rows if r["Key"] == key]
                if len(matches) != 1:
                    self._json(HTTPStatus.NOT_FOUND, {"error": "Puzzle key not found."})
                    return
                if matches[0]["Code"].strip():
                    self._json(HTTPStatus.CONFLICT, {"error": "Puzzle already has Code."})
                    return
                matches[0]["Code"] = code
                save_rows(csv_path, rows)
            self._json(HTTPStatus.OK, {"saved": key})
        def log_message(self, fmt, *args):
            pass
    return Handler


PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>ASP Solution Filler</title>
<style>
  body { font-family: -apple-system, system-ui, sans-serif; margin: 0; background: #f5f5f7; color: #222; }
  header { padding: 12px 20px; background: #2d3748; color: #fff; display: flex; justify-content: space-between; align-items: center; }
  main { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; padding: 16px 20px; height: calc(100vh - 60px); box-sizing: border-box; }
  section { background: #fff; border-radius: 6px; padding: 12px; display: flex; flex-direction: column; min-height: 0; }
  h2 { margin: 0 0 8px; font-size: 15px; color: #555; }
  pre#puzzle { flex: 1; overflow: auto; margin: 0; white-space: pre-wrap; font-size: 13px; line-height: 1.4; }
  textarea { flex: 1; font-family: Menlo, Consolas, monospace; font-size: 13px; padding: 8px; border: 1px solid #ccc; border-radius: 4px; resize: none; }
  .actions { display: flex; gap: 8px; margin-top: 8px; align-items: center; }
  button { padding: 8px 14px; border: 0; border-radius: 4px; background: #3182ce; color: #fff; cursor: pointer; font-size: 14px; }
  button:disabled { background: #a0aec0; cursor: default; }
  #status { font-size: 13px; color: #555; }
  #status.error { color: #c53030; }
  #status.ok { color: #2f855a; }
</style>
</head>
<body>
<header>
  <strong>ASP Solution Filler</strong>
</header>
<main>
  <section>
    <h2>Puzzle <small id="key"></small></h2>
    <pre id="puzzle">Loading...</pre>
  </section>
  <section>
    <h2>ASP code</h2>
    <textarea id="code" placeholder="Write or paste ASP code here..."></textarea>
    <div class="actions">
      <button id="submit">Submit</button>
      <button id="next" style="background:#718096">Skip / Next</button>
      <span id="status"></span>
    </div>
  </section>
</main>
<script>
let currentKey = null;

function setStatus(msg, cls) {
  const s = document.getElementById("status");
  s.textContent = msg;
  s.className = cls || "";
}

async function loadRandom() {
  const submit = document.getElementById("submit");
  setStatus("");
  const res = await fetch("/api/random");
  if (!res.ok) {
    currentKey = null;
    document.getElementById("puzzle").textContent = "";
    document.getElementById("key").textContent = "";
    submit.disabled = true;
    setStatus((await res.json()).error, "ok");
    return;
  }
  const data = await res.json();
  currentKey = data.key;
  document.getElementById("puzzle").textContent = data.puzzle;
  document.getElementById("key").textContent = "(" + data.key + ")";
  document.getElementById("code").value = "";
  submit.disabled = false;
}

async function submitCode() {
  const code = document.getElementById("code").value.trim();
  if (!code) { setStatus("Code is empty.", "error"); return; }
  const submit = document.getElementById("submit");
  submit.disabled = true;
  const res = await fetch("/api/save", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ key: currentKey, code: code }),
  });
  const data = await res.json();
  if (!res.ok) {
    setStatus(data.error, "error");
    submit.disabled = false;
    return;
  }
  setStatus("Saved.", "ok");
  await loadRandom();
}

document.getElementById("submit").addEventListener("click", submitCode);
document.getElementById("next").addEventListener("click", loadRandom);
document.getElementById("code").addEventListener("keydown", (e) => {
  if ((e.metaKey || e.ctrlKey) && e.key === "Enter") submitCode();
});

loadRandom();
</script>
</body>
</html>
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--csv", default=DEFAULT_CSV, help="path to the puzzle CSV")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    server = ThreadingHTTPServer(("127.0.0.1", args.port), make_handler(os.path.abspath(args.csv)))
    print(f"Serving {args.csv} at http://127.0.0.1:{args.port}  (Ctrl+C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
