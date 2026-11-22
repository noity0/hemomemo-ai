# -*- coding: utf-8 -*-
"""HEMOMO ANIMATION ENGINE — local flow-animations (100% Hemomemo AI system).

User-qanoon: "AI flow me ja raha hai to Gemini/Claude jaisi animation banao —
par koi AI-API / UE5 / Higgsfield / kisi platform ka key — NAHI.
Sirf Hemomemo dimagh (local modules) + pure Python (no network).

Flow stages (user-flow v3):
READ-TOKEN → CONVERT-TO-BINARY → READ-BY-AI → THINK → REASONING → THINK-RESEARCH(need-if) → THINK-CONVERT → THINK → RESEARCH → THINK → CONVERT-BINARY-TO-TEXT → ANSWER → READ-AGAIN → LEARN

Har stage ke liye:
- glyph (emoji symbol)
- kind (pulse/orbit/beam/check/burst)
- duration (seconds)
- local frames (opacity/scale/y keyframes)
"""
from typing import Any, Dict, List, Tuple

ANIM_STAGES: List[str] = [
    "READ-TOKEN", "CONVERT-TO-BINARY", "READ-BY-AI", "THINK", "REASONING",
    "THINK-RESEARCH", "THINK-CONVERT", "RESEARCH", "THINK",
    "CONVERT-BINARY-TO-TEXT", "ANSWER", "READ-AGAIN", "LEARN",
    ]

ANIM_CFG: Dict[str, Dict[str, Any]] = {
    "READ-TOKEN":        {"glyph": "📥", "kind": "orbit",      "dur": 0.9},
    "CONVERT-TO-BINARY": {"glyph": "⚙️",  "kind": "pulse",      "dur": 1.6},
    "READ-BY-AI":        {"glyph": "⬇️",  "kind": "beam",       "dur": 1.2},
    "THINK":             {"glyph": "⚡",  "kind": "pulse",      "dur": 2.2},
    "REASONING":         {"glyph": "🔬",  "kind": "scan",       "dur": 2.0},
    "THINK-RESEARCH":    {"glyph": "🌐",  "kind": "orbit",      "dur": 2.5},
    "THINK-CONVERT":     {"glyph": "🔄",  "kind": "swap",       "dur": 0.8},
    "RESEARCH":          {"glyph": "🌐",  "kind": "orbit",      "dur": 2.5},
    "CONVERT-BINARY-TO-TEXT": {"glyph": "🔄", "kind": "swap",       "dur": 0.8},
    "ANSWER":           {"glyph": "✍️",  "kind": "burst",      "dur": 1.0},
    "READ-AGAIN":       {"glyph": "📖",  "kind": "orbit",      "dur": 1.0},
    "LEARN":            {"glyph": "🧬",  "kind": "burst",      "dur": 1.0},
}


def get_animation(stage: str, detail: str = "") -> Dict[str, Any]:
    """Stage → local animation spec (frames + timing, no network)."""
    cfg = ANIM_CFG.get(stage, {"glyph": "◈", "kind": "pulse", "dur": 1.0})
    return {
        "stage": stage,
        "glyph": cfg["glyph"],
        "kind": cfg["kind"],
        "duration": cfg["dur"],
        "label": "%s %s" % (cfg["glyph"], stage),
        "detail": detail or "",
        "t": 0.0,
        "frames": [
            {"t": 0.0, "opacity": 0.0, "scale": 0.6, "y": -8},
            {"t": 0.5, "opacity": 0.85, "scale": 1.0, "y": 0},
            {"t": 1.0, "opacity": 1.0, "scale": 1.0, "y": 0},
        ],
    }


def get_orbit_frames(radius: float = 20.0, steps: int = 36) -> List[Tuple[float, float]]:
    """App ke liye circular animation coords generate kare (local calculation)."""
    import math
    coords = []
    for i in range(steps):
        angle = (2 * math.pi * i) / steps
        x = radius * math.cos(angle)
        y = radius * math.sin(angle)
        coords.append((x, y))
    return coords


def flow_animations(marks) -> List[Dict[str, Any]]:
    """FlowTracker.marks [(stage, dt, note), ...] → animation timeline."""
    out: List[Dict[str, Any]] = []
    for name, dt, note in (marks or []):
        a = get_animation(name, note or "")
        a["mark_dt"] = dt
        out.append(a)
    return out


def stage_anim_json(stage: str, detail: str = "") -> str:
    """HUD/JSON ke liye animation line (local, deterministic)."""
    a = get_animation(stage, detail)
    return '"%s@%s:%s"' % (stage, a["kind"], a["label"])


def render_flow_hud_line(flow_line: str, verbose: bool = False) -> List[Dict[str, Any]]:
    """Flow line (⇄ 📥READ ...) → timeline animation spec (for HUD/UI).
    Local-only; no network. Returns list of animation specs (in order)."""
    import re
    # Parse flow_line me har stage mark ko list banao:
    out: List[Dict[str, Any]] = []
    if not flow_line:
        return out
    # Find each stage name with optional skip-mark or duration
    _FLOW_NAMES = ["READ-TOKEN", "CONVERT-TO-BINARY", "READ-BY-AI", "THINK",
                   "REASONING", "THINK-RESEARCH", "THINK-CONVERT", "RESEARCH",
                   "CONVERT-BINARY-TO-TEXT", "ANSWER", "READ-AGAIN", "LEARN"]
    _FLOW_RX = re.compile("|".join(
        re.escape(n) for n in sorted(_FLOW_NAMES, key=len, reverse=True)) + r"\b")
    for m in _FLOW_RX.finditer(flow_line or ""):
        name = m.group(0).split(":", 1)[0].strip()
        base = re.sub(r"^[^a-zA-Z-]*", "", name)
        out.append(get_animation(base))
