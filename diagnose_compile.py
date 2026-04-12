from __future__ import annotations

import argparse
import re
import subprocess
import sys
from html import unescape
from pathlib import Path

try:
    import uharfbuzz as hb
    from fontTools.ttLib import TTFont
except ImportError:
    hb = None
    TTFont = None


ROOT = Path(__file__).resolve().parent
FFPYTHON = ROOT / "spetekkimyo" / "ffpython" / "bin" / "ffpython.exe"
GENERATE = ROOT / "spetekkimyo" / "generate.py"
DEFAULT_OUTPUT = ROOT / "output" / "test.otf"
DEFAULT_SAMPLE = '<span class="ss">tue</span> pb'


def resolve_output_path(raw_path: str) -> Path:
    output_path = Path(raw_path)
    if not output_path.is_absolute():
        output_path = ROOT / output_path
    return output_path.resolve()


def run_compiler(output_path: Path) -> int:
    if not FFPYTHON.exists():
        print(f"Missing ffpython executable: {FFPYTHON}")
        return 1
    if not GENERATE.exists():
        print(f"Missing generator script: {GENERATE}")
        return 1

    output_path.parent.mkdir(parents=True, exist_ok=True)

    print("=== Compile ===")
    print(f"Repo root: {ROOT}")
    print(f"Output: {output_path}")
    print(f"Compiler: {FFPYTHON}")
    print(f"Script: {GENERATE}")

    result = subprocess.run(
        [str(FFPYTHON), str(GENERATE), str(output_path)],
        cwd=str(FFPYTHON.parent),
        capture_output=True,
        text=True,
    )

    print("\n--- stdout ---")
    print(result.stdout.rstrip() or "(none)")
    print("\n--- stderr ---")
    print(result.stderr.rstrip() or "(none)")
    print(f"\nExit code: {result.returncode}")

    if output_path.exists():
        size = output_path.stat().st_size
        print(f"Built file: {output_path} ({size} bytes)")
    else:
        print("Built file: missing")

    return result.returncode


def collect_feature_tags(tt_font: TTFont) -> list[str]:
    tags: list[str] = []
    for table_tag in ("GSUB", "GPOS"):
        if table_tag not in tt_font:
            continue
        table = tt_font[table_tag].table
        feature_list = getattr(table, "FeatureList", None)
        if not feature_list:
            continue
        tags.extend(record.FeatureTag for record in feature_list.FeatureRecord)
    return list(dict.fromkeys(tags))


def extract_font_runs(sample_html: str) -> list[str]:
    runs = [
        unescape(match.group(1))
        for match in re.finditer(r'<span class="ss">(.*?)</span>', sample_html, flags=re.S)
    ]
    if runs:
        return runs
    return [unescape(re.sub(r"<[^>]+>", "", sample_html))]


def inspect_font(font_path: Path, sample_html: str) -> None:
    if hb is None or TTFont is None:
        print("\nSkipping font inspection: fontTools and/or uharfbuzz is unavailable.")
        return

    if not font_path.exists():
        print("\nSkipping font inspection: font file does not exist.")
        return

    tt_font = TTFont(str(font_path))
    feature_tags = collect_feature_tags(tt_font)
    requested_features = {tag: True for tag in feature_tags}
    runs = extract_font_runs(sample_html)
    plain_text = unescape(re.sub(r"<[^>]+>", "", sample_html))

    print("\n=== Font Summary ===")
    print(f"Font: {font_path}")
    print(f"Plain text: {plain_text}")
    print(f"Feature tags ({len(feature_tags)}): {', '.join(feature_tags) if feature_tags else '(none)'}")
    print(f"Font runs ({len(runs)}): {runs}")

    hb_face = hb.Face(font_path.read_bytes())
    hb_font = hb.Font(hb_face)
    hb.ot_font_set_funcs(hb_font)

    for run_index, run_text in enumerate(runs, 1):
        messages: list[str] = []

        def capture_message(message: str) -> bool:
            messages.append(message)
            return True

        buffer = hb.Buffer()
        buffer.add_str(run_text)
        buffer.guess_segment_properties()
        if hasattr(buffer, "set_message_func"):
            buffer.set_message_func(capture_message)
        if requested_features:
            hb.shape(hb_font, buffer, requested_features)
        else:
            hb.shape(hb_font, buffer)

        glyph_names = [tt_font.getGlyphName(info.codepoint) for info in buffer.glyph_infos]

        print(f"\nRun {run_index}: {run_text}")
        print(f"Final glyphs: {glyph_names}")
        if messages:
            print("Lookup trace:")
            for message in messages:
                print(message)
        else:
            print("Lookup trace: unavailable")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compile the font and print diagnostic output.")
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT),
        help="Output font path, relative to the repo root unless absolute.",
    )
    parser.add_argument(
        "--sample",
        default=DEFAULT_SAMPLE,
        help="Sample HTML snippet to shape after compilation.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_path = resolve_output_path(args.output)

    exit_code = run_compiler(output_path)
    if exit_code != 0:
        return exit_code

    inspect_font(output_path, args.sample)
    return 0


if __name__ == "__main__":
    sys.exit(main())
