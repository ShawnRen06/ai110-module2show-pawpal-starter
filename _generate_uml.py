"""
_generate_uml.py — generates uml_final.png from the class diagram.
Run once: python _generate_uml.py
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch

# ── layout constants ──────────────────────────────────────────────────────────
BOX_W = 3.2
BOX_H_HEADER = 0.45
ROW_H = 0.28
PAD = 0.12
BG = "#F8F9FA"
HEADER_COLOR = "#2C3E50"
ATTR_COLOR = "#ECF0F1"
METHOD_COLOR = "#D5E8D4"
TEXT_COLOR = "#2C3E50"
BORDER = "#2C3E50"
ARROW_COLOR = "#555555"

fig, ax = plt.subplots(figsize=(14, 9))
ax.set_xlim(0, 14)
ax.set_ylim(0, 9)
ax.axis("off")
fig.patch.set_facecolor(BG)
ax.set_facecolor(BG)


def draw_class(ax, x, y, name, attributes, methods):
    """Draw a UML class box with name, attributes, and methods sections."""
    attrs = attributes or []
    meths = methods or []
    total_rows = len(attrs) + len(meths) + (1 if attrs and meths else 0)
    box_h = BOX_HEADER_H = BOX_H_HEADER + total_rows * ROW_H + PAD * 2

    # Outer border
    rect = mpatches.FancyBboxPatch(
        (x, y - box_h), BOX_W, box_h,
        boxstyle="round,pad=0.02", linewidth=1.5,
        edgecolor=BORDER, facecolor="white"
    )
    ax.add_patch(rect)

    # Header background
    header = mpatches.FancyBboxPatch(
        (x, y - BOX_H_HEADER), BOX_W, BOX_H_HEADER,
        boxstyle="round,pad=0.02", linewidth=0,
        edgecolor=HEADER_COLOR, facecolor=HEADER_COLOR
    )
    ax.add_patch(header)
    ax.text(x + BOX_W / 2, y - BOX_H_HEADER / 2, f"«class»\n{name}",
            ha="center", va="center", fontsize=8.5, fontweight="bold",
            color="white", linespacing=1.4)

    cursor_y = y - BOX_H_HEADER - PAD

    # Attributes section
    if attrs:
        for attr in attrs:
            ax.text(x + 0.12, cursor_y, attr, ha="left", va="top",
                    fontsize=7, color=TEXT_COLOR, family="monospace")
            cursor_y -= ROW_H
        # divider
        if meths:
            ax.plot([x, x + BOX_W], [cursor_y + ROW_H * 0.3, cursor_y + ROW_H * 0.3],
                    color=BORDER, linewidth=0.8, alpha=0.5)

    # Methods section
    for meth in meths:
        ax.text(x + 0.12, cursor_y, meth, ha="left", va="top",
                fontsize=7, color="#1A5276", family="monospace")
        cursor_y -= ROW_H

    return y - box_h   # bottom y of the box


def arrow(ax, x1, y1, x2, y2, label="", style="->"):
    """Draw an arrow between two points with an optional label."""
    mpl_style = "->" if style == "..>" else style
    ls = "dashed" if style == "..>" else "solid"
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle=mpl_style, color=ARROW_COLOR,
                                lw=1.3, linestyle=ls,
                                connectionstyle="arc3,rad=0.0"))
    if label:
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        ax.text(mx + 0.08, my, label, fontsize=7, color=ARROW_COLOR, style="italic")


# ── class definitions ─────────────────────────────────────────────────────────
classes = {
    "Task": {
        "x": 0.4, "y": 8.7,
        "attrs": ["+title: str", "+category: str", "+duration_minutes: int",
                  "+priority: str", "+time: str", "+frequency: str",
                  "+due_date: date|None", "+completed: bool"],
        "methods": ["+mark_complete()", "+reset()"],
    },
    "Pet": {
        "x": 5.0, "y": 8.7,
        "attrs": ["+name: str", "+species: str", "+age: int",
                  "+special_needs: str", "+tasks: list[Task]"],
        "methods": ["+add_task(task)", "+get_tasks()", "+pending_tasks()"],
    },
    "Owner": {
        "x": 9.5, "y": 8.7,
        "attrs": ["+name: str", "+available_minutes: int",
                  "+preferences: list[str]", "+pets: list[Pet]"],
        "methods": ["+add_pet(pet)", "+get_pets()", "+get_all_tasks()"],
    },
    "ScheduledItem": {
        "x": 0.4, "y": 3.8,
        "attrs": ["+pet: Pet", "+task: Task",
                  "+start_minute: int", "+reason: str"],
        "methods": [],
    },
    "Scheduler": {
        "x": 5.0, "y": 3.8,
        "attrs": ["+owner: Owner"],
        "methods": ["+generate_schedule(pet?)",
                    "+sort_by_time(tasks)",
                    "+filter_tasks(pet_name?, completed?)",
                    "+check_conflicts(pet?)",
                    "+explain_plan(schedule)"],
    },
}

bottoms = {}
for name, cfg in classes.items():
    b = draw_class(ax, cfg["x"], cfg["y"],
                   name, cfg["attrs"], cfg["methods"])
    bottoms[name] = b

# ── relationships ─────────────────────────────────────────────────────────────
# Pet 1-->many Task  (Pet right edge → Task right edge, horizontal)
arrow(ax, 5.0, 6.8, 3.6, 6.8, "1 has many", "->")

# Owner 1-->many Pet (horizontal, between class tops)
arrow(ax, 9.5, 7.2, 8.2, 7.2, "1 owns many", "->")

# Scheduler uses Owner
arrow(ax, 8.2, 2.6, 9.5, 6.5, "uses", "->")

# Scheduler uses Pet (upward)
arrow(ax, 6.6, 3.8, 6.6, 5.5, "uses", "->")

# Scheduler produces ScheduledItem (leftward)
arrow(ax, 5.0, 2.2, 3.6, 2.2, "produces", "..>")

# ScheduledItem wraps Task (upward)
arrow(ax, 2.0, 3.8, 2.0, 5.5, "wraps", "->")

# ScheduledItem for Pet
arrow(ax, 3.6, 3.0, 5.0, 5.8, "for", "->")

# ── title ─────────────────────────────────────────────────────────────────────
ax.text(7, 0.35, "PawPal+ — Final Class Diagram",
        ha="center", va="center", fontsize=12, fontweight="bold", color=TEXT_COLOR)

plt.tight_layout(pad=0.5)
plt.savefig("uml_final.png", dpi=150, bbox_inches="tight", facecolor=BG)
print("Saved uml_final.png")
