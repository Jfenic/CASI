#!/usr/bin/env python3
"""Generate an animated terminal demo GIF for CASI using Pillow."""

from __future__ import annotations

import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

WIDTH = 920
HEIGHT = 580
BG_COLOR = (11, 15, 25)
TITLEBAR_BG = (15, 23, 42)
BORDER_COLOR = (40, 50, 70)
TEXT_WHITE = (240, 246, 252)
TEXT_MUTED = (140, 155, 175)
TEXT_CYAN = (56, 189, 248)
TEXT_GREEN = (74, 222, 128)
TEXT_RED = (248, 113, 113)
TEXT_YELLOW = (250, 204, 21)
TEXT_PURPLE = (192, 132, 252)

FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
FONT_BOLD_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"


def get_fonts():
    try:
        font = ImageFont.truetype(FONT_PATH, 13)
        font_bold = ImageFont.truetype(FONT_BOLD_PATH, 13)
        title_font = ImageFont.truetype(FONT_PATH, 11)
    except Exception:
        font = ImageFont.load_default()
        font_bold = font
        title_font = font
    return font, font_bold, title_font


def draw_window_frame(draw: ImageDraw.ImageDraw, title_font: ImageFont.ImageFont):
    # Titlebar background
    draw.rectangle([(0, 0), (WIDTH, 36)], fill=TITLEBAR_BG)
    # Window border
    draw.rectangle([(0, 0), (WIDTH - 1, HEIGHT - 1)], outline=BORDER_COLOR, width=1)
    draw.line([(0, 36), (WIDTH, 36)], fill=BORDER_COLOR, width=1)

    # Traffic light window dots
    draw.ellipse([(14, 12), (24, 22)], fill=(244, 63, 94))
    draw.ellipse([(32, 12), (42, 22)], fill=(251, 191, 36))
    draw.ellipse([(50, 12), (60, 22)], fill=(34, 197, 94))

    # Window title
    title = "casi ~ supervised-sandbox (Docker • Ollama)"
    draw.text((WIDTH // 2 - 140, 11), title, font=title_font, fill=TEXT_MUTED)


def render_frame(lines: list[tuple[str, tuple[int, int, int], bool]]) -> Image.Image:
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)
    font, font_bold, title_font = get_fonts()

    draw_window_frame(draw, title_font)

    y = 50
    line_height = 19
    for text, color, is_bold in lines:
        active_font = font_bold if is_bold else font
        draw.text((24, y), text, font=active_font, fill=color)
        y += line_height

    return img


def main():
    os.makedirs("docs/assets", exist_ok=True)
    frames: list[Image.Image] = []
    durations: list[int] = []

    # SCENE 1: casi doctor
    f1 = [
        ("$ casi doctor", TEXT_GREEN, True),
        ("", TEXT_MUTED, False),
        ("╭─ CASI Doctor • Environment Health ──────────────────────────────────────╮", TEXT_CYAN, False),
        ("│ • Python Runtime: [OK]  Python 3.12.3 (>= 3.11)                         │", TEXT_WHITE, False),
        ("│ • Git Workspace : [OK]  casi-code-agent [git: feat/advanced-agent-v2]   │", TEXT_WHITE, False),
        ("│ • Ollama Server : [OK]  Online (http://127.0.0.1:11434)                 │", TEXT_WHITE, False),
        ("│ • LLM Model     : [OK]  qwen2.5-coder:7b (installed)                    │", TEXT_WHITE, False),
        ("│ • Docker Daemon : [OK]  Running and accessible                           │", TEXT_WHITE, False),
        ("│ • Sandbox Image : [OK]  casi-sandbox:latest found                        │", TEXT_WHITE, False),
        ("╰─────────────────────────────────────────────────────────────────────────╯", TEXT_CYAN, False),
        ("✔ All checks passed! Your environment is ready.", TEXT_GREEN, True),
    ]
    frames.append(render_frame(f1))
    durations.append(2500)

    # SCENE 2: casi interactive start
    f2 = [
        ("$ casi interactive --repo .", TEXT_GREEN, True),
        ("", TEXT_MUTED, False),
        ("╭─ CASI ────────────────────────────────────────────────────────── v0.1.0 ─╮", TEXT_CYAN, False),
        ("│   ____ ___    _____ ____                                                 │", TEXT_CYAN, True),
        ("│  / __//   |  / ___//  _/   CASI • Local AI Software Engineer             │", TEXT_CYAN, True),
        ("│ / /  / /| |  \\__ \\ / /     Model   : qwen2.5-coder:7b (ollama)           │", TEXT_WHITE, False),
        ("│ / /__/ ___ | ___/ // /     Sandbox : Docker isolated (casi-sandbox)      │", TEXT_WHITE, False),
        ("│ \\___/_/  |_|/____//___/    Branch  : feat/advanced-agent-v2 (clean)      │", TEXT_WHITE, False),
        ("│                                                                          │", TEXT_MUTED, False),
        ("│  Guard   : apply_patch requires human confirmation [y/N/v/save/?]        │", TEXT_YELLOW, False),
        ("│  Commands: /help • /status • /explain • /diff • /undo • /exit            │", TEXT_MUTED, False),
        ("╰──────────────────────────────────────────────────────────────────────────╯", TEXT_CYAN, False),
        ("◆ CASI interactive mode. Type /help for commands.", TEXT_CYAN, False),
        ("", TEXT_MUTED, False),
        ("casi ❯ Fix ZeroDivisionError in @src/analytics/metrics.py", TEXT_WHITE, True),
    ]
    frames.append(render_frame(f2))
    durations.append(3000)

    # SCENE 3: running tests & docker fail
    f3 = list(f2) + [
        ("├─ [1/3] 🔍 search_code('def calculate_metrics') ➜ src/analytics/metrics.py", TEXT_MUTED, False),
        ("├─ [2/3] 🧪 run_tests() [Docker Sandbox • network=NONE]", TEXT_YELLOW, False),
        ("│        ❌ FAILED tests/test_metrics.py::test_empty_dataset", TEXT_RED, True),
        ("│        ZeroDivisionError: division by zero at line 34", TEXT_RED, False),
        ("├─ [3/3] ✏️  propose_file('src/analytics/metrics.py') in worktree", TEXT_PURPLE, False),
    ]
    frames.append(render_frame(f3))
    durations.append(2500)

    # SCENE 4: tests pass in sandbox
    f4 = list(f3) + [
        ("│        🧪 Re-running tests in Docker container against patch...", TEXT_YELLOW, False),
        ("│        ✅ 18 passed in 0.38s! All tests green.", TEXT_GREEN, True),
    ]
    frames.append(render_frame(f4))
    durations.append(2000)

    # SCENE 5: proposed diff
    f5 = [
        ("Proposed Patch (1 file changed, 2 insertions(+)):", TEXT_WHITE, True),
        ("--- a/src/analytics/metrics.py", TEXT_MUTED, False),
        ("+++ b/src/analytics/metrics.py", TEXT_MUTED, False),
        ("@@ -32,4 +32,6 @@ def calculate_metrics(values: list[float]) -> dict:", TEXT_CYAN, False),
        ("+    if not values:", TEXT_GREEN, True),
        ("+        return {'count': 0, 'mean': 0.0, 'variance': 0.0}", TEXT_GREEN, True),
        ("     mean = sum(values) / len(values)", TEXT_MUTED, False),
        ("     variance = sum((x - mean) ** 2 for x in values) / len(values)", TEXT_MUTED, False),
        ("", TEXT_MUTED, False),
        ("Human Approval: Apply this patch to your repository? [y/N/v/save/?]: y", TEXT_YELLOW, True),
        ("✅ Patch applied cleanly to src/analytics/metrics.py", TEXT_GREEN, True),
        ("", TEXT_MUTED, False),
        ("casi ❯ /undo", TEXT_WHITE, True),
        ("⏪ PatchMemento: Reverted last patch (restored src/analytics/metrics.py)", TEXT_PURPLE, True),
    ]
    frames.append(render_frame(f5))
    durations.append(4000)

    # Save animated GIF
    out_path = Path("docs/assets/demo.gif")
    frames[0].save(
        out_path,
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=0,
        optimize=True,
    )
    print(f"Generated animated demo GIF at {out_path} ({os.path.getsize(out_path)} bytes)")


if __name__ == "__main__":
    main()
