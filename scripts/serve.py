"""Local preview server with the same clean URLs as Vercel (/about -> about.html).

    python scripts/serve.py 5173 website
"""
import http.server
import os
import sys

port = int(sys.argv[1]) if len(sys.argv) > 1 else 5173
root = sys.argv[2] if len(sys.argv) > 2 else "website"


class CleanUrlHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=root, **kwargs)

    def send_head(self):
        path = self.path.split("?", 1)[0].split("#", 1)[0]
        local = os.path.join(root, path.lstrip("/"))
        if path not in ("", "/") and not os.path.exists(local) and os.path.exists(local.rstrip("/") + ".html"):
            self.path = path.rstrip("/") + ".html" + (self.path[len(path):] if len(self.path) > len(path) else "")
        return super().send_head()


http.server.ThreadingHTTPServer(("127.0.0.1", port), CleanUrlHandler).serve_forever()
