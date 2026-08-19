# Copyright 2025 qBraid
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Generate the qBraid-SDK runtime diagram as light and dark SVG variants.

Both variants come from this one definition so they cannot drift apart. Run after
editing the pipeline stages::

    python bin/generate_runtime_diagram.py

"""

FONT = "Space Grotesk, Inter, system-ui, -apple-system, Segoe UI, Helvetica, Arial, sans-serif"
MONO = "JetBrains Mono, SFMono-Regular, Menlo, Consolas, monospace"

THEMES = {
    "light": {
        "ink": "#171717",
        "muted": "#6B6B6B",
        "accent": "#8B5CF6",
        "fill": "#FFFFFF",
        "soft": "#F7F5FF",
        "rule": "#D9D4E8",
    },
    "dark": {
        "ink": "#EDEDED",
        "muted": "#9A94A8",
        "accent": "#A855F7",
        "fill": "#18141F",
        "soft": "#1F1A29",
        "rule": "#332B44",
    },
}

# Mirrors QuantumDevice.apply_runtime_profile() followed by submit().
STAGES = [
    ("transpile", "any &#8594; target type"),
    ("transform", "device-specific passes"),
    ("validate", "against device profile"),
    ("submit", "serialized IR"),
]

WIDTH, HEIGHT = 1040, 430
SDK_X, SDK_Y, SDK_W, SDK_H = 200, 252, 640, 140
BOX_W, BOX_H, BOX_Y = 136, 72, 296
GAP = 21
STAGE_X = [216 + i * (BOX_W + GAP) for i in range(len(STAGES))]
MID_Y = BOX_Y + BOX_H / 2
SUBMIT_CX = STAGE_X[-1] + BOX_W / 2


def build(theme: dict) -> str:
    """Return the complete diagram SVG for one theme."""
    # The nested helpers below are drawing primitives: geometry and style are
    # genuinely separate parameters, and bundling them would only add indirection.
    # pylint: disable=too-many-arguments
    out = []

    def rect(x, y, w, h, fill, stroke, rx=10, dash=""):
        dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
        out.append(
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" '
            f'stroke="{stroke}" stroke-width="1.5"{dash_attr}/>'
        )

    def label(x, y, content, size, fill, weight="500", anchor="middle", font=FONT):
        out.append(
            f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" '
            f'text-anchor="{anchor}" fill="{fill}" font-family="{font}">{content}</text>'
        )

    def arrow(x1, y1, x2, y2, both=False):
        start = ' marker-start="url(#ar)"' if both else ""
        out.append(
            f'<path d="M{x1} {y1}L{x2} {y2}" stroke="{theme["muted"]}" '
            f'stroke-width="1.5" marker-end="url(#ar)"{start}/>'
        )

    def node(x, y, w, h, title, *subtitles, mono=False, soft=False):
        rect(x, y, w, h, theme["soft"] if soft else theme["fill"], theme["rule"])
        label(
            x + w / 2,
            y + 30,
            title,
            15.5 if mono else 14.5,
            theme["ink"],
            "600",
            font=MONO if mono else FONT,
        )
        for i, sub in enumerate(subtitles):
            label(x + w / 2, y + 50 + i * 15, sub, 11, theme["muted"], "400")

    out.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" '
        f'width="{WIDTH}" height="{HEIGHT}" font-family="{FONT}" fill="none">'
    )
    out.append(
        '<defs><marker id="ar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" '
        'markerHeight="7" orient="auto-start-reverse">'
        f'<path d="M0 0 10 5 0 10z" fill="{theme["muted"]}"/></marker></defs>'
    )

    node(655, 30, 200, 62, "QPU / simulator", "provider hardware", soft=True)
    node(655, 146, 200, 62, "Provider REST API", "job submission &#183; polling", soft=True)
    arrow(SUBMIT_CX, 146, SUBMIT_CX, 92, both=True)
    arrow(SUBMIT_CX, BOX_Y, SUBMIT_CX, 208, both=True)
    label(SUBMIT_CX + 10, 236, "HTTPS", 11, theme["muted"], "400", "start", MONO)

    rect(SDK_X, SDK_Y, SDK_W, SDK_H, "none", theme["accent"], rx=14, dash="6 5")
    label(SDK_X + 14, SDK_Y - 10, "qBraid SDK", 14, theme["accent"], "600", "start")

    for i, (name, sub) in enumerate(STAGES):
        node(STAGE_X[i], BOX_Y, BOX_W, BOX_H, name, sub, mono=True)
        if i < len(STAGES) - 1:
            arrow(STAGE_X[i] + BOX_W + 3, MID_Y, STAGE_X[i] + BOX_W + GAP - 3, MID_Y)

    node(
        16,
        290,
        150,
        84,
        "Quantum program",
        "Qiskit &#183; Cirq &#183; Braket",
        "pyQuil &#183; OpenQASM &#183; &#8230;",
        soft=True,
    )
    arrow(169, 332, 197, 332)

    node(874, 290, 150, 84, "Result", "counts &#183; probabilities", "provider metadata", soft=True)
    arrow(843, 332, 871, 332)

    out.append("</svg>")
    return "\n".join(out)


def main() -> None:
    """Write both theme variants to docs/_static/."""
    for name, theme in THEMES.items():
        path = f"docs/_static/qbraid_runtime_{name}.svg"
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(build(theme))
        print(f"wrote {path}")


if __name__ == "__main__":
    main()
