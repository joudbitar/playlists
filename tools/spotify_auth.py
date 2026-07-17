#!/usr/bin/env python3
"""One-time Spotify OAuth. Reads client_id/client_secret from ../.secrets.json,
opens the browser to authorize, captures the callback on 127.0.0.1:8888,
and saves the refresh token back into .secrets.json. Stdlib only."""
import base64
import http.server
import json
import secrets as pysecrets
import sys
import threading
import urllib.parse
import urllib.request
import webbrowser
from pathlib import Path

SECRETS = Path(__file__).parent.parent / ".secrets.json"
REDIRECT = "http://127.0.0.1:8888/callback"
SCOPES = "playlist-modify-public playlist-modify-private"

creds = json.loads(SECRETS.read_text())
if not creds.get("client_id") or not creds.get("client_secret"):
    sys.exit("Fill client_id and client_secret in .secrets.json first.")

state = pysecrets.token_urlsafe(16)
got = {}


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        if q.get("state", [""])[0] != state or "code" not in q:
            self.send_response(400); self.end_headers()
            self.wfile.write(b"Bad callback. Re-run the script.")
            return
        got["code"] = q["code"][0]
        self.send_response(200)
        self.send_header("Content-Type", "text/html"); self.end_headers()
        self.wfile.write(b"<h2>Authorized. You can close this tab.</h2>")

    def log_message(self, *a):
        pass


server = http.server.HTTPServer(("127.0.0.1", 8888), Handler)
threading.Thread(target=server.handle_request, daemon=True).start()

url = "https://accounts.spotify.com/authorize?" + urllib.parse.urlencode({
    "client_id": creds["client_id"], "response_type": "code",
    "redirect_uri": REDIRECT, "scope": SCOPES, "state": state})
print("Opening browser for Spotify consent…\nIf nothing opens, visit:\n" + url)
webbrowser.open(url)

import time
for _ in range(1800):
    if "code" in got:
        break
    time.sleep(0.2)
else:
    sys.exit("Timed out waiting for the callback.")

basic = base64.b64encode(
    f"{creds['client_id']}:{creds['client_secret']}".encode()).decode()
req = urllib.request.Request(
    "https://accounts.spotify.com/api/token",
    data=urllib.parse.urlencode({
        "grant_type": "authorization_code", "code": got["code"],
        "redirect_uri": REDIRECT}).encode(),
    headers={"Authorization": f"Basic {basic}",
             "Content-Type": "application/x-www-form-urlencoded"})
tok = json.loads(urllib.request.urlopen(req).read())
creds["refresh_token"] = tok["refresh_token"]
SECRETS.write_text(json.dumps(creds, indent=2) + "\n")
print("Refresh token saved to .secrets.json — auth done.")
