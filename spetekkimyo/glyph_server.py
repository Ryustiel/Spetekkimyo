from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import subprocess
import shutil
import tempfile
import threading
import time
from dataclasses import dataclass, field
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

try:
    import uharfbuzz as hb
    from fontTools.ttLib import TTFont
except ImportError:
    hb = None
    TTFont = None


ROOT = Path(__file__).resolve().parent
INPUT_DIR = ROOT / "input"
GLYPH_DIR = INPUT_DIR / "glyphs"
LIVE_DIR = ROOT / "_live"
LIVE_OUTPUT = LIVE_DIR / "preview.otf"
LIVE_STAMP = LIVE_DIR / "preview.stamp"
LIVE_OUTPUT_URL = f"/{LIVE_OUTPUT.relative_to(ROOT).as_posix()}"
GENERATE = ROOT / "generate.py"
FFPYTHON = next(
    (
        path
        for path in (
            ROOT / "ffpython" / "bin" / "ffpython.exe",
            ROOT / "ffpython" / "bin" / "ffpython",
        )
        if path.exists()
    ),
    ROOT / "ffpython" / "bin" / "ffpython.exe",
)


def compiler_available() -> bool:
    return FFPYTHON.exists() and GENERATE.exists()


def list_glyph_names() -> list[str]:
    if not GLYPH_DIR.exists():
        return []
    return sorted(
        path.name for path in GLYPH_DIR.iterdir() if path.is_file() and path.suffix.lower() == ".eps"
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


def iter_source_files() -> list[Path]:
    files: list[Path] = []
    if GENERATE.exists():
        files.append(GENERATE)
    if INPUT_DIR.exists():
        for path in sorted(INPUT_DIR.rglob("*"), key=lambda p: p.as_posix()):
            if path.is_file():
                files.append(path)
    return files


def compute_source_stamp() -> str:
    digest = hashlib.sha256()
    count = 0
    for path in iter_source_files():
        try:
            stat = path.stat()
        except OSError:
            continue
        digest.update(path.relative_to(ROOT).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(str(stat.st_mtime_ns).encode("ascii"))
        digest.update(b"\0")
        digest.update(str(stat.st_size).encode("ascii"))
        digest.update(b"\n")
        count += 1
    return f"{count}:{digest.hexdigest()}"


def read_published_stamp() -> str | None:
    try:
        value = LIVE_STAMP.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    return value or None


def write_published_stamp(stamp: str) -> None:
    LIVE_DIR.mkdir(parents=True, exist_ok=True)
    LIVE_STAMP.write_text(stamp, encoding="utf-8")


def compile_font_to_live_output() -> dict[str, object]:
    if not compiler_available():
        missing = []
        if not FFPYTHON.exists():
            missing.append(f"ffpython executable: {FFPYTHON}")
        if not GENERATE.exists():
            missing.append(f"generator script: {GENERATE}")
        return {
            "ok": False,
            "exit_code": None,
            "stdout": "",
            "stderr": "",
            "error": "Missing " + ", ".join(missing) if missing else "Compiler unavailable.",
            "output_path": str(LIVE_OUTPUT),
            "output_url": LIVE_OUTPUT_URL if LIVE_OUTPUT.exists() else None,
            "bytes": LIVE_OUTPUT.stat().st_size if LIVE_OUTPUT.exists() else 0,
        }

    LIVE_DIR.mkdir(parents=True, exist_ok=True)
    try:
        fd, temp_name = tempfile.mkstemp(suffix=".otf")
        os.close(fd)
        temp_output = Path(temp_name)
        try:
            result = subprocess.run(
                [str(FFPYTHON), str(GENERATE), str(temp_output)],
                cwd=str(ROOT),
                capture_output=True,
                text=True,
                errors="replace",
            )
            stdout = result.stdout or ""
            stderr = result.stderr or ""
            error = ""
            if result.returncode != 0:
                error = f"generator returned exit code {result.returncode}"
            elif not temp_output.exists():
                error = "generator exited successfully but did not create the output font"
            if not error:
                try:
                    temp_output.replace(LIVE_OUTPUT)
                except OSError:
                    try:
                        shutil.copy2(temp_output, LIVE_OUTPUT)
                    except OSError as exc:
                        error = f"compiled font could not be published: {exc}"
            return {
                "ok": not error,
                "exit_code": result.returncode,
                "stdout": stdout,
                "stderr": stderr,
                "error": error,
                "output_path": str(LIVE_OUTPUT),
                "output_url": LIVE_OUTPUT_URL if LIVE_OUTPUT.exists() else None,
                "bytes": LIVE_OUTPUT.stat().st_size if LIVE_OUTPUT.exists() else 0,
            }
        finally:
            if temp_output.exists():
                try:
                    temp_output.unlink()
                except OSError:
                    pass
    except OSError as exc:
        return {
            "ok": False,
            "exit_code": None,
            "stdout": "",
            "stderr": "",
            "error": str(exc),
            "output_path": str(LIVE_OUTPUT),
            "output_url": LIVE_OUTPUT_URL if LIVE_OUTPUT.exists() else None,
            "bytes": LIVE_OUTPUT.stat().st_size if LIVE_OUTPUT.exists() else 0,
        }


def shape_text(font_path: Path, text: str) -> dict[str, object]:
    if hb is None or TTFont is None:
        raise RuntimeError("Missing fontTools and/or uharfbuzz; cannot shape text.")
    if not font_path.exists():
        raise FileNotFoundError("No compiled preview font available yet. Click Compile font first.")

    font_bytes = font_path.read_bytes()
    tt_font = TTFont(io.BytesIO(font_bytes))
    try:
        head = tt_font["head"] if "head" in tt_font else None
        upem = int(getattr(head, "unitsPerEm", 1000) or 1000)

        hb_face = hb.Face(font_bytes)
        hb_font = hb.Font(hb_face)
        hb_font.scale = (upem, upem)
        hb.ot_font_set_funcs(hb_font)

        buffer = hb.Buffer()
        buffer.add_str(text)
        buffer.guess_segment_properties()
        hb.shape(hb_font, buffer)

        glyphs = []
        for index, (info, pos) in enumerate(zip(buffer.glyph_infos, buffer.glyph_positions)):
            try:
                glyph_name = tt_font.getGlyphName(info.codepoint)
            except Exception:
                glyph_name = f"gid{info.codepoint}"
            glyphs.append(
                {
                    "index": index,
                    "gid": info.codepoint,
                    "name": glyph_name,
                    "cluster": info.cluster,
                    "advance_x": pos.x_advance,
                    "advance_y": pos.y_advance,
                    "offset_x": pos.x_offset,
                    "offset_y": pos.y_offset,
                }
            )
        return {"text": text, "glyphs": glyphs, "glyph_count": len(glyphs)}
    finally:
        close = getattr(tt_font, "close", None)
        if callable(close):
            close()


@dataclass
class PreviewManager:
    lock: threading.Lock = field(default_factory=threading.Lock)
    compile_running: bool = False
    dirty_override: bool = False
    last_compile_started: float | None = None
    last_compile_finished: float | None = None
    last_compile_ok: bool | None = None
    last_compile_exit_code: int | None = None
    last_compile_error: str = ""
    last_compiled_source_stamp: str | None = None

    def mark_dirty(self) -> None:
        with self.lock:
            self.dirty_override = True

    def status(self) -> dict[str, object]:
        current_stamp = compute_source_stamp()
        preview_available = LIVE_OUTPUT.exists()
        preview_size = LIVE_OUTPUT.stat().st_size if preview_available else 0
        with self.lock:
            stored_stamp = self.last_compiled_source_stamp or read_published_stamp()
            dirty = self.dirty_override or stored_stamp is None or stored_stamp != current_stamp
            return {
                "compiler_available": compiler_available(),
                "compiler_executable": str(FFPYTHON) if FFPYTHON.exists() else None,
                "shape_available": hb is not None and TTFont is not None,
                "compile_running": self.compile_running,
                "dirty": dirty,
                "preview_available": preview_available,
                "preview_size_bytes": preview_size,
                "font_url": LIVE_OUTPUT_URL if preview_available else None,
                "font_path": str(LIVE_OUTPUT),
                "last_compile_ok": self.last_compile_ok,
                "last_compile_exit_code": self.last_compile_exit_code,
                "last_compile_error": self.last_compile_error,
                "last_compile_started": self.last_compile_started,
                "last_compile_finished": self.last_compile_finished,
            }

    def compile(self) -> dict[str, object] | None:
        with self.lock:
            if self.compile_running:
                return None
            self.compile_running = True
            self.last_compile_started = time.time()

        stamp_before = compute_source_stamp()
        result = compile_font_to_live_output()
        stamp_after = compute_source_stamp()

        with self.lock:
            self.compile_running = False
            self.last_compile_finished = time.time()
            self.last_compile_ok = bool(result.get("ok"))
            exit_code = result.get("exit_code")
            self.last_compile_exit_code = exit_code if isinstance(exit_code, int) else None
            self.last_compile_error = str(result.get("error", ""))
            if result.get("ok"):
                stored_stamp = stamp_after if stamp_after == stamp_before else stamp_before
                self.last_compiled_source_stamp = stored_stamp
                self.dirty_override = stamp_after != stamp_before
                try:
                    write_published_stamp(stored_stamp)
                except OSError:
                    pass
        return {"status": self.status(), "result": result}

    def shape(self, text: str) -> dict[str, object]:
        status = self.status()
        if not status["preview_available"]:
            if status["compile_running"]:
                raise FileNotFoundError("Compile is still running.")
            raise FileNotFoundError("No compiled preview font available yet. Click Compile font first.")
        payload = shape_text(LIVE_OUTPUT, text)
        payload["status"] = self.status()
        payload["font_url"] = LIVE_OUTPUT_URL
        return payload


PREVIEW = PreviewManager()


class GlyphHandler(SimpleHTTPRequestHandler):
    extensions_map = {
        **SimpleHTTPRequestHandler.extensions_map,
        ".otf": "font/otf",
        ".ttf": "font/ttf",
        ".woff": "font/woff",
        ".woff2": "font/woff2",
    }

    def __init__(self, *args, directory: str | None = None, **kwargs):
        super().__init__(*args, directory=directory or str(ROOT), **kwargs)

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, format: str, *args) -> None:
        print(format % args)

    def send_json(self, payload: object, status: int = 200) -> None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def send_text(self, text: str, status: int = 200, content_type: str = "text/plain; charset=utf-8") -> None:
        data = text.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def redirect(self, location: str) -> None:
        self.send_response(302)
        self.send_header("Location", location)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def read_request_text(self) -> str:
        try:
            length = int(self.headers.get("Content-Length", "0") or 0)
        except ValueError as exc:
            raise ValueError("invalid content length") from exc
        return "" if length <= 0 else self.rfile.read(length).decode("utf-8")

    def read_shape_text(self) -> str:
        content_type = (self.headers.get("Content-Type") or "").split(";", 1)[0].strip().lower()
        raw = self.read_request_text()
        if not raw:
            return ""
        if content_type == "application/json":
            payload = json.loads(raw)
            if not isinstance(payload, dict):
                raise ValueError("json body must be an object")
            return str(payload.get("text", ""))
        return raw

    def handle_shape(self, text: str) -> None:
        try:
            self.send_json(PREVIEW.shape(text))
        except FileNotFoundError as exc:
            self.send_json({"error": str(exc), "status": PREVIEW.status()}, status=409)
        except RuntimeError as exc:
            self.send_json({"error": str(exc), "status": PREVIEW.status()}, status=500)
        except Exception as exc:
            self.send_json({"error": f"shape failed: {exc}", "status": PREVIEW.status()}, status=500)

    def handle_compile(self) -> None:
        payload = PREVIEW.compile()
        if payload is None:
            self.send_json({"error": "compile already running", "status": PREVIEW.status()}, status=409)
        else:
            self.send_json(payload)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path in {"", "/", "/live", "/live.html"}:
            self.redirect("/live_glyphs.html")
            return
        if parsed.path == "/api/status":
            self.send_json(PREVIEW.status())
            return
        if parsed.path == "/api/glyphs":
            self.send_json({"glyphs": list_glyph_names()})
            return
        if parsed.path == "/api/glyph":
            name = parse_qs(parsed.query, keep_blank_values=True).get("name", [""])[0]
            try:
                path = resolve_glyph_path(name)
            except (ValueError, FileNotFoundError) as exc:
                self.send_json({"error": str(exc)}, status=404)
                return
            self.send_text(path.read_text(encoding="utf-8"))
            return
        if parsed.path == "/api/shape":
            self.handle_shape(parse_qs(parsed.query, keep_blank_values=True).get("text", [""])[0])
            return
        super().do_GET()

    def do_PUT(self) -> None:
        if urlparse(self.path).path != "/api/glyph":
            self.send_json({"error": "not found"}, status=404)
            return
        name = parse_qs(urlparse(self.path).query, keep_blank_values=True).get("name", [""])[0]
        try:
            path = resolve_glyph_path(name)
        except (ValueError, FileNotFoundError) as exc:
            self.send_json({"error": str(exc)}, status=404)
            return
        content = self.read_request_text()
        path.write_text(content, encoding="utf-8", newline="\n")
        PREVIEW.mark_dirty()
        self.send_json({"ok": True, "name": name, "bytes": len(content.encode("utf-8")), "status": PREVIEW.status()})

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/compile":
            self.handle_compile()
            return
        if parsed.path == "/api/shape":
            try:
                self.handle_shape(self.read_shape_text())
            except ValueError as exc:
                self.send_json({"error": str(exc)}, status=400)
            return
        if parsed.path == "/api/glyph":
            self.do_PUT()
            return
        self.send_json({"error": "not found"}, status=404)


def main() -> int:
    parser = argparse.ArgumentParser(description="Serve the glyph editor plus live shaping preview.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), partial(GlyphHandler, directory=str(ROOT)))
    print(f"Serving {ROOT}")
    print(f"Live page:   http://{args.host}:{args.port}/live_glyphs.html")
    print(f"Editor only: http://{args.host}:{args.port}/glyphs.html")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
