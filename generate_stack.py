#!/usr/bin/env python3
"""
Generates stack.svg from the SKILL_GROUPS list below.

TO ADD A SKILL:    add a tuple to the right group's list: ("Name", "simpleicons-slug", "#HEXCOLOR")
TO REMOVE A SKILL:  delete its tuple.
TO ADD A CATEGORY:  add a new ("LABEL", [...]) tuple to SKILL_GROUPS.

Find the correct slug for a new skill at https://simpleicons.org (search the skill,
the slug is shown under "SVG" / used in the URL). If a skill isn't on Simple Icons
(this has happened for Java, AWS, VS Code), set slug to None and instead add its raw
icon SVG file to the FALLBACK_ICONS dict near the bottom (see Java/AWS/VS Code for the
working pattern already used there).

Requires: pip install requests --break-system-packages (only needed to fetch new icons;
already-used icons are cached in icon_cache/ so you won't re-download them every run).

Run:  python3 generate_stack.py
Output: stack.svg in the same folder.
"""

import os, json, urllib.request
from xml.sax.saxutils import escape
import xml.etree.ElementTree as ET

# ============================== EDIT THIS ==================================
SKILL_GROUPS = [
    ("LANGUAGES", [
        ("Java", None, "#ED8B00"),              # no simple-icons slug -> uses fallback (skillicons)
        ("Python", "python", "#3776AB"),
        ("TypeScript", "typescript", "#3178C6"),
        ("JavaScript", "javascript", "#F7DF1E"),
        ("C++", "cplusplus", "#00599C"),
        ("PHP", "php", "#8892BF"),
    ]),
    ("BACKEND & AI", [
        ("Spring Boot", "springboot", "#6DB33F"),
        ("FastAPI", "fastapi", "#009688"),
        ("Node.js", "nodedotjs", "#339933"),
        ("LangChain", "langchain", "#2DD4BF"),
    ]),
    ("FRONTEND", [
        ("React", "react", "#61DAFB"),
        ("Next.js", "nextdotjs", "#E2E8F0"),
        ("Angular", "angular", "#DD0031"),
        ("Tailwind CSS", "tailwindcss", "#06B6D4"),
    ]),
    ("DATA & INFRA", [
        ("PostgreSQL", "postgresql", "#4169E1"),
        ("MySQL", "mysql", "#4479A1"),
        ("Redis", "redis", "#DC382D"),
        ("Supabase", "supabase", "#3FCF8E"),
        ("AWS", None, "#FF9900"),               # fallback icon (jsDelivr, color injected)
        ("Docker", "docker", "#2496ED"),
    ]),
    ("TOOLING", [
        ("Git", "git", "#F05032"),
        ("GitHub Actions", "githubactions", "#2088FF"),
        ("Postman", "postman", "#FF6C37"),
        ("VS Code", None, "#007ACC"),           # fallback icon (jsDelivr, color injected)
    ]),
]

# Icons with no Simple Icons slug: (source_url, inject_color_bool)
FALLBACK_ICON_SOURCES = {
    "Java": ("https://cdn.jsdelivr.net/npm/simple-icons@latest/icons/java.svg", True),
    "AWS": ("https://cdn.jsdelivr.net/npm/simple-icons@latest/icons/amazonaws.svg", True),
    "VS Code": ("https://cdn.jsdelivr.net/npm/simple-icons@latest/icons/visualstudiocode.svg", True),
}
# =============================================================================

CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon_cache")
os.makedirs(CACHE_DIR, exist_ok=True)

CANVAS_W = 1500
LABEL_X = 30
CHIPS_START_X = 290
ROW_HEIGHT = 110
CHIP_HEIGHT = 62
CHIP_Y_OFFSET = (ROW_HEIGHT - CHIP_HEIGHT) // 2
ICON_SIZE = 34
CHIP_GAP = 18
CHIP_PAD_X = 22
ICON_TEXT_GAP = 12
FONT_SIZE_CHIP = 22
FONT_SIZE_LABEL = 28

def text_width(s, font_size):
    return len(s) * (font_size * 0.56)

def fetch(url, cache_key):
    cache_path = os.path.join(CACHE_DIR, cache_key + ".svg")
    if os.path.exists(cache_path):
        return open(cache_path, encoding="utf-8").read()
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; stack-svg-generator/1.0)"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        content = resp.read().decode("utf-8")
    with open(cache_path, "w", encoding="utf-8") as f:
        f.write(content)
    return content

def get_icon_geometry(name, slug, color):
    ns = {"svg": "http://www.w3.org/2000/svg"}
    if slug:
        url = f"https://cdn.simpleicons.org/{slug}"
        content = fetch(url, slug)
    else:
        src_url, inject = FALLBACK_ICON_SOURCES[name]
        content = fetch(src_url, name.lower().replace(" ", "_").replace(".", ""))
    root = ET.fromstring(content)
    vb = root.attrib.get("viewBox", "0 0 24 24")
    vb_w = float(vb.split()[2])
    paths = root.findall(".//svg:path", ns)
    d_list = [(p.attrib.get("d", ""), color) for p in paths]
    return vb_w, d_list

def render_icon(name, slug, color, icon_x, icon_y):
    vb_w, d_list = get_icon_geometry(name, slug, color)
    scale = ICON_SIZE / vb_w
    parts = [f'<g transform="translate({icon_x},{icon_y}) scale({scale})">']
    for d, fill in d_list:
        parts.append(f'<path d="{escape(d)}" fill="{fill}"/>')
    parts.append("</g>")
    return "\n".join(parts)

def build_svg():
    svg_parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {CANVAS_W} {ROW_HEIGHT * len(SKILL_GROUPS)}" font-family="Verdana, Geneva, sans-serif">']

    for row_idx, (label, skills) in enumerate(SKILL_GROUPS):
        y = row_idx * ROW_HEIGHT
        chip_y = y + CHIP_Y_OFFSET
        label_cy = y + ROW_HEIGHT / 2 + FONT_SIZE_LABEL * 0.35
        svg_parts.append(f'<text x="{LABEL_X}" y="{label_cy}" font-size="{FONT_SIZE_LABEL}" font-weight="700" fill="#ffffff">{escape(label)}</text>')

        x = CHIPS_START_X
        for name, slug, color in skills:
            tw = text_width(name, FONT_SIZE_CHIP)
            chip_w = CHIP_PAD_X + ICON_SIZE + ICON_TEXT_GAP + tw + CHIP_PAD_X
            svg_parts.append(f'<rect x="{x}" y="{chip_y}" width="{chip_w}" height="{CHIP_HEIGHT}" rx="16" ry="16" fill="rgba(148,163,184,0.16)" stroke="rgba(148,163,184,0.35)" stroke-width="1"/>')
            icon_x = x + CHIP_PAD_X
            icon_y = chip_y + (CHIP_HEIGHT - ICON_SIZE) / 2
            svg_parts.append(render_icon(name, slug, color, icon_x, icon_y))
            text_x = icon_x + ICON_SIZE + ICON_TEXT_GAP
            text_cy = chip_y + CHIP_HEIGHT / 2 + FONT_SIZE_CHIP * 0.35
            svg_parts.append(f'<text x="{text_x}" y="{text_cy}" font-size="{FONT_SIZE_CHIP}" font-weight="600" fill="#f1f5f9">{escape(name)}</text>')
            x += chip_w + CHIP_GAP

    svg_parts.append("</svg>")
    return "\n".join(svg_parts)

if __name__ == "__main__":
    svg = build_svg()
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stack.svg")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(svg)
    # Validate before declaring success
    ET.parse(out_path)
    print(f"stack.svg written and validated ({len(svg)} bytes)")
