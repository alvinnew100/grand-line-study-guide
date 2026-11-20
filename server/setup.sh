#!/usr/bin/env bash
# Sky Castle judge server setup for Ubuntu 22.04/24.04. Safe to run again.
# Usage:  curl -fsSL https://raw.githubusercontent.com/alvinnew100/grand-line-study-guide/main/server/setup.sh | sudo bash
set -euo pipefail
[ "$(id -u)" = 0 ] || { echo "Please run with sudo."; exit 1; }
RAW=https://raw.githubusercontent.com/alvinnew100/grand-line-study-guide/main/server
export DEBIAN_FRONTEND=noninteractive

echo "==> 1/6 Installing Docker"
apt-get update -y >/dev/null
apt-get install -y docker.io curl python3 >/dev/null
systemctl enable --now docker >/dev/null

echo "==> 2/6 Adding 2 GB of swap (protects the machine if a compile uses a lot of memory)"
if ! swapon --show | grep -q .; then
  fallocate -l 2G /swapfile && chmod 600 /swapfile && mkswap /swapfile >/dev/null && swapon /swapfile
  grep -q '^/swapfile' /etc/fstab || echo '/swapfile none swap sw 0 0' >> /etc/fstab
fi

echo "==> 3/6 Downloading the language images (a few minutes)"
for image in python:3.12-slim node:22-slim eclipse-temurin:21-jdk golang:1.23; do docker pull -q "$image" >/dev/null; echo "    $image"; done

echo "==> 4/6 Building the Go image with a warmed build cache"
build=$(mktemp -d)
cat > "$build/main.go" <<'GO'
package main

import (
	"bufio"
	"encoding/json"
	"errors"
	"fmt"
	"math"
	"os"
	"sort"
	"strconv"
	"strings"
	"sync"
	"time"
)

func main() {
	var wg sync.WaitGroup
	r := bufio.NewReader(os.Stdin)
	b, _ := json.Marshal(map[string]int{"a": 1})
	xs := []int{3, 1, 2}
	sort.Ints(xs)
	fmt.Println(r != nil, string(b), errors.New("x"), math.Sqrt(4), strconv.Itoa(1), strings.ToUpper("a"), time.Now().Year(), xs)
	wg.Wait()
}
GO
cat > "$build/Dockerfile" <<'DOCKER'
FROM golang:1.23
ENV GOCACHE=/gocache GOFLAGS=-mod=mod GOPROXY=off GOTOOLCHAIN=local
COPY main.go /warm/main.go
RUN mkdir -p /gocache && cd /warm && go mod init warm && go build -o /dev/null . && chmod -R 777 /gocache
DOCKER
docker build -q -t judge-go "$build" >/dev/null
rm -r "$build"

echo "==> 5/6 Installing the gateway service"
mkdir -p /opt/judge/jobs
[ -s /opt/judge/secret ] || (umask 077; head -c 32 /dev/urandom | od -An -tx1 | tr -d ' \n' > /opt/judge/secret)
curl -fsSL "$RAW/gateway.py" -o /opt/judge/gateway.py
cat > /etc/systemd/system/judge.service <<'UNIT'
[Unit]
Description=Sky Castle judge gateway
After=docker.service
Requires=docker.service

[Service]
ExecStart=/usr/bin/python3 /opt/judge/gateway.py
Restart=always
RestartSec=2

[Install]
WantedBy=multi-user.target
UNIT
systemctl daemon-reload
systemctl enable judge >/dev/null 2>&1
systemctl restart judge
sleep 2

echo "==> 6/6 Self-test (runs a hello-world in each language)"
python3 - <<'PY'
import hashlib, hmac, json, time, urllib.request
secret = open("/opt/judge/secret").read().strip().encode()
programs = {
    "python": ("main.py", 'print("hello from python")'),
    "node": ("main.js", 'console.log("hello from node")'),
    "java": ("Main.java", 'public class Main { public static void main(String[] a) { System.out.println("hello from java " + Runtime.version().feature()); } }'),
    "go": ("main.go", 'package main\nimport ("fmt"; "runtime")\nfunc main() { fmt.Println("hello from", runtime.Version()) }'),
}
ok = True
for lang, (name, code) in programs.items():
    body = json.dumps({"user": "selftest", "language": lang, "files": [{"name": name, "content": code}]}).encode()
    ts = str(int(time.time()))
    sig = hmac.new(secret, ts.encode() + b"." + body, hashlib.sha256).hexdigest()
    req = urllib.request.Request("http://127.0.0.1:8443/run", data=body, headers={"X-Ts": ts, "X-Sig": sig})
    try:
        r = json.load(urllib.request.urlopen(req, timeout=90))
        good = r["code"] == 0
        print(f"    {lang:7s} {'OK  ' if good else 'FAIL'} {r['ms']:6d} ms  {(r['stdout'] or r['stderr']).strip()[:80]}")
        ok = ok and good
    except Exception as e:
        ok = False
        print(f"    {lang:7s} FAIL  {e}")
print("    Self-test passed." if ok else "    Self-test had failures: send the lines above to Claude.")
PY

ip=$(curl -fsS https://checkip.amazonaws.com || echo "<your instance's public IP>")
echo
echo "Done. Two values you will paste into Supabase in the next step (keep the secret private, do not post it anywhere):"
echo "  JUDGE_URL    = http://$ip:8443/run"
echo "  JUDGE_SECRET = shown by:  sudo cat /opt/judge/secret"
echo "Also: in the Lightsail console, Networking tab, add an IPv4 firewall rule: Custom, TCP, port 8443."
