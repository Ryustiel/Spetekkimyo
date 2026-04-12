from __future__ import annotations

import argparse
import json
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse


ROOT = Path(__file__).resolve().parent
GLYPH_DIR = ROOT / "input" / "glyphs"


def list_glyph_names() -> list[str]:
    if not GLYPH_DIR.exists():
        return []
    return sorted(
        p.name
        for p in GLYPH_DIR.iterdir()
        if p.is_file() and p.suffix.lower() == ".eps"
    )


def resolve_glyph_path(name: str) -> Path:
    if not name:
        raise ValueError("missing glyph name")

    if Path(name).name != name:
        raise ValueError("invalid glyph name")

    if not name.lower().endswith(".eps"):
        raise ValueError("invalid glyph extension")

    path = GLYPH_DIR / name
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(name)

    return path


class GlyphHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, directory: str | None = None, **kwargs):
        super().__init__(*args, directory=directory or str(ROOT), **kwargs)

    def log_message(self, format: str, *args) -> None:
        print(format % args)

    def send_json(self, payload: object, status: int = 200) -> None:
        data = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def send_text(self, text: str, status: int = 200, content_type: str = "text/plain; charset=utf-8") -> None:
        data = text.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)

        if parsed.path == "/api/glyphs":
            self.send_json({"glyphs": list_glyph_names()})
            return

        if parsed.path == "/api/glyph":
            name = parse_qs(parsed.query).get("name", [""])[0]
            try:
                path = resolve_glyph_path(name)
            except (ValueError, FileNotFoundError) as exc:
                self.send_json({"error": str(exc)}, status=404)
                return

            self.send_text(path.read_text(encoding="utf-8"), status=200, content_type="text/plain; charset=utf-8")
            return

        super().do_GET()

    def do_PUT(self) -> None:
        parsed = urlparse(self.path)

        if parsed.path != "/api/glyph":
            self.send_json({"error": "not found"}, status=404)
            return

        name = parse_qs(parsed.query).get("name", [""])[0]
        try:
            path = resolve_glyph_path(name)
        except (ValueError, FileNotFoundError) as exc:
            self.send_json({"error": str(exc)}, status=404)
            return

        length = int(self.headers.get("Content-Length", "0") or 0)
        content = self.rfile.read(length).decode("utf-8")
        with path.open("w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
        self.send_json({"ok": True, "name": name, "bytes": len(content.encode("utf-8"))})

    def do_POST(self) -> None:
        self.do_PUT()


def main() -> int:
    parser = argparse.ArgumentParser(description="Serve the glyph gallery and glyph file API.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), partial(GlyphHandler, directory=str(ROOT)))
    print(f"Serving {ROOT} on http://{args.host}:{args.port}/glyphs.html")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
