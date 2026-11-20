#!/usr/bin/env python3
"""Sky Castle judge gateway.

Runs one learner program per request inside a throwaway Docker container that has
no network, a memory/CPU/process cap and an unprivileged user, then returns its output.
Requests must be signed with the shared secret (HMAC-SHA256 over "<timestamp>.<body>"),
so only the site's Supabase function can use it.
"""
import hashlib
import hmac
import json
import os
import re
import shutil
import subprocess
import tempfile
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

SECRET = open("/opt/judge/secret").read().strip().encode()
JOBS = "/opt/judge/jobs"
PORT = 8443
SLOTS = threading.Semaphore(2)          # programs running at once
RATE, RATE_LOCK = {}, threading.Lock()  # user -> recent request times
PER_MINUTE = 30
MAX_BODY, MAX_OUT, WALL_SECONDS = 300_000, 65_536, 25
NAME_OK = re.compile(r"^[A-Za-z0-9_.-]{1,64}$")
COMPILE_FAILED = 97

LANGS = {
    "python": dict(image="python:3.12-slim", cmd="cd /work && exec python3 main.py"),
    "node": dict(image="node:22-slim", cmd="cd /work && exec node main.js"),
    "java": dict(image="eclipse-temurin:21-jdk",
                 cmd="mkdir -p /tmp/out && cd /work && javac -d /tmp/out *.java 2>/tmp/cerr || { cat /tmp/cerr >&2; exit 97; }; "
                     "exec java -XX:+UseSerialGC -Xmx256m -cp /tmp/out Main"),
    "go": dict(image="judge-go",
               cmd="mkdir -p /tmp/src && cp /work/*.go /tmp/src/ && cd /tmp/src && go mod init judge >/dev/null 2>&1; "
                   "go build -o /tmp/prog . 2>/tmp/cerr || { cat /tmp/cerr >&2; exit 97; }; exec /tmp/prog"),
}


def allowed(user):
    now = time.time()
    with RATE_LOCK:
        recent = [t for t in RATE.get(user, []) if now - t < 60]
        if len(recent) >= PER_MINUTE:
            RATE[user] = recent
            return False
        recent.append(now)
        RATE[user] = recent
        return True


def run_job(language, files, stdin):
    cfg = LANGS[language]
    workdir = tempfile.mkdtemp(dir=JOBS)
    name = "job-" + uuid.uuid4().hex[:12]
    try:
        os.chmod(workdir, 0o755)
        for f in files:
            path = os.path.join(workdir, f["name"])
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(f["content"])
            os.chmod(path, 0o644)
        cmd = ["docker", "run", "--rm", "-i", "--name", name, "--network", "none",
               "--memory", "512m", "--memory-swap", "512m", "--cpus", "1", "--pids-limit", "128",
               "--cap-drop", "ALL", "--security-opt", "no-new-privileges", "--user", "65534:65534",
               "--tmpfs", "/tmp:rw,exec,size=256m,mode=1777", "-e", "HOME=/tmp",
               "-v", workdir + ":/work:ro", cfg["image"], "sh", "-c", cfg["cmd"]]
        started = time.time()
        timed_out = False
        try:
            p = subprocess.run(cmd, input=(stdin or "").encode(), capture_output=True, timeout=WALL_SECONDS)
            code, out, err = p.returncode, p.stdout, p.stderr
        except subprocess.TimeoutExpired as e:
            subprocess.run(["docker", "kill", name], capture_output=True)
            timed_out, code, out, err = True, -1, e.stdout or b"", e.stderr or b""
        return {
            "code": code, "timed_out": timed_out, "compile_error": code == COMPILE_FAILED,
            "stdout": out[:MAX_OUT].decode("utf-8", "replace"), "stderr": err[:MAX_OUT].decode("utf-8", "replace"),
            "ms": int((time.time() - started) * 1000),
        }
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


def validate(req):
    if req.get("language") not in LANGS:
        return "Unsupported language"
    files = req.get("files")
    if not isinstance(files, list) or not 1 <= len(files) <= 10:
        return "Send between 1 and 10 files"
    for f in files:
        if not isinstance(f, dict) or not NAME_OK.match(str(f.get("name", ""))) or not isinstance(f.get("content"), str):
            return "Bad file entry"
    if not isinstance(req.get("user"), str) or not req["user"]:
        return "Missing user"
    return None


class Handler(BaseHTTPRequestHandler):
    def reply(self, status, payload):
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        self.reply(200, {"ok": True, "languages": sorted(LANGS)}) if self.path == "/health" else self.reply(404, {"error": "not found"})

    def do_POST(self):
        if self.path != "/run":
            return self.reply(404, {"error": "not found"})
        length = int(self.headers.get("Content-Length") or 0)
        if not 0 < length <= MAX_BODY:
            return self.reply(413, {"error": "Request too large"})
        body = self.rfile.read(length)
        ts, sig = self.headers.get("X-Ts", ""), self.headers.get("X-Sig", "")
        expected = hmac.new(SECRET, ts.encode() + b"." + body, hashlib.sha256).hexdigest()
        if not ts.isdigit() or abs(time.time() - int(ts)) > 120 or not hmac.compare_digest(sig, expected):
            return self.reply(401, {"error": "Bad signature"})
        try:
            req = json.loads(body)
        except ValueError:
            return self.reply(400, {"error": "Body is not JSON"})
        problem = validate(req)
        if problem:
            return self.reply(400, {"error": problem})
        if not allowed(req["user"]):
            return self.reply(429, {"error": "Too many runs, wait a minute"})
        with SLOTS:
            self.reply(200, run_job(req["language"], req["files"], req.get("stdin", "")))

    def log_message(self, fmt, *args):
        pass


if __name__ == "__main__":
    os.makedirs(JOBS, exist_ok=True)
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
