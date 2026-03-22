"""
drawing.py — all pygame rendering functions.
"""

import math
import pygame

import state
from constants import (
    GRID_SIZE, GATE_DEFINITIONS, GATE_COLORS,
    gold_base, gold_light, MENU, BUILD_MODE,
)

# ---------------------------------------------------------------------------
# Fonts
# ---------------------------------------------------------------------------

font = None  # Initialised in init() after pygame.init()
_font_cache = {}

def init():
    """Must be called after pygame.init()."""
    global font
    font = pygame.font.Font(None, 36)

def _get_font(size):
    if size not in _font_cache:
        _font_cache[size] = pygame.font.Font(None, size)
    return _font_cache[size]

def lerp(a, b, t):
    return a + (b - a) * t

# ---------------------------------------------------------------------------
# Button rect definitions  (module-level so other modules can reference them)
# ---------------------------------------------------------------------------

# Rects are rebuilt each frame in _update_rects() to support window resizing
menu_button_rect         = pygame.Rect(10, 10, 40, 40)
side_menu_rect           = pygame.Rect(0, 0, 200, 600)
exit_button_rect         = pygame.Rect(20, 60, 160, 40)
item_menu_rect           = pygame.Rect(680, 0, 120, 600)
redstone_button_rect     = pygame.Rect(690, 20,  90, 30)
power_button_rect        = pygame.Rect(690, 60,  90, 30)
or_button_rect           = pygame.Rect(690,100,  90, 30)
and_button_rect          = pygame.Rect(690,140,  90, 30)
not_button_rect          = pygame.Rect(690,180,  90, 30)
delete_button_rect       = pygame.Rect(690,220,  90, 30)
xor_button_rect          = pygame.Rect(690,260,  90, 30)
nor_button_rect          = pygame.Rect(690,300,  90, 30)
nand_button_rect         = pygame.Rect(690,340,  90, 30)
lasso_button_rect        = pygame.Rect(690,380,  90, 30)
save_component_button_rect = pygame.Rect(20, 110, 160, 40)
clock_button_rect        = pygame.Rect(690,420,  90, 30)
bridge_button_rect       = pygame.Rect(690,460,  90, 30)
one_way_button_rect      = pygame.Rect(690,490,  90, 30)

def _update_rects(W, H):
    """Reposition all window-edge-relative rects when the window is resized."""
    global menu_button_rect, side_menu_rect, exit_button_rect, item_menu_rect
    global redstone_button_rect, power_button_rect, or_button_rect, and_button_rect
    global not_button_rect, delete_button_rect, xor_button_rect, nor_button_rect
    global nand_button_rect, lasso_button_rect, save_component_button_rect
    global clock_button_rect, bridge_button_rect, one_way_button_rect
    global BUTTON_DEFS

    side_menu_rect        = pygame.Rect(0,       0,   200, H)
    item_menu_rect        = pygame.Rect(W - 120, 0,   120, H)
    redstone_button_rect  = pygame.Rect(W - 110, 20,   90, 30)
    power_button_rect     = pygame.Rect(W - 110, 60,   90, 30)
    or_button_rect        = pygame.Rect(W - 110, 100,  90, 30)
    and_button_rect       = pygame.Rect(W - 110, 140,  90, 30)
    not_button_rect       = pygame.Rect(W - 110, 180,  90, 30)
    delete_button_rect    = pygame.Rect(W - 110, 220,  90, 30)
    xor_button_rect       = pygame.Rect(W - 110, 260,  90, 30)
    nor_button_rect       = pygame.Rect(W - 110, 300,  90, 30)
    nand_button_rect      = pygame.Rect(W - 110, 340,  90, 30)
    lasso_button_rect     = pygame.Rect(W - 110, 380,  90, 30)
    clock_button_rect     = pygame.Rect(W - 110, 420,  90, 30)
    bridge_button_rect    = pygame.Rect(W - 110, 460,  90, 30)
    one_way_button_rect   = pygame.Rect(W - 110, 490,  90, 30)

    BUTTON_DEFS = [
        ("redstone", redstone_button_rect,  "Redstone"),
        ("one_way",  one_way_button_rect,   "One Way"),
        ("bridge",   bridge_button_rect,    "Bridge"),
        ("power",    power_button_rect,     "Power"),
        ("or",       or_button_rect,        "OR"),
        ("and",      and_button_rect,       "AND"),
        ("not",      not_button_rect,       "NOT"),
        ("xor",      xor_button_rect,       "XOR"),
        ("nor",      nor_button_rect,       "NOR"),
        ("nand",     nand_button_rect,      "NAND"),
        ("select",   lasso_button_rect,     "Lasso"),
        ("delete",   delete_button_rect,    "Delete"),
        ("clock",    clock_button_rect,     "Clock"),
    ]

# Popup button rects (set each frame inside draw_grid)
copy_button_rect             = None
delete_button_rect_popup     = None
paste_button_rect            = None
paste_component_popup_rect   = None

BUTTON_DEFS = [
    ("redstone", redstone_button_rect,  "Redstone"),
    ("one_way",  one_way_button_rect,   "One Way"),
    ("bridge",   bridge_button_rect,    "Bridge"),
    ("power",    power_button_rect,     "Power"),
    ("or",       or_button_rect,        "OR"),
    ("and",      and_button_rect,       "AND"),
    ("not",      not_button_rect,       "NOT"),
    ("xor",      xor_button_rect,       "XOR"),
    ("nor",      nor_button_rect,       "NOR"),
    ("nand",     nand_button_rect,      "NAND"),
    ("select",   lasso_button_rect,     "Lasso"),
    ("delete",   delete_button_rect,    "Delete"),
    ("clock",    clock_button_rect,     "Clock"),
]

# Initialise button scales in state
if not state.button_scales:
    state.button_scales = {mode: 1.0 for mode, _, _ in BUTTON_DEFS}

glow_colors = [(*gold_light, alpha) for alpha in range(50, 0, -10)]

# ---------------------------------------------------------------------------
# Menu screen
# ---------------------------------------------------------------------------

TARGET_SCALE = 1.15
SCALE_SPEED  = 0.2
_hover_states = {0: False, 1: False, 2: False}
_text_scales  = [1.0, 1.0, 1.0]

def draw_menu(screen, clock):
    screen.fill((30, 30, 30))
    mouse_pos = pygame.mouse.get_pos()
    menu_items = [("Make New Component", 250), ("View Components", 320), ("Exit", 390)]
    dt = clock.get_time() / 16.67

    for i, (text, y) in enumerate(menu_items):
        btn_rect = pygame.Rect(250, y - 10, 300, 60)
        _hover_states[i] = btn_rect.collidepoint(mouse_pos)
        target_scale = TARGET_SCALE if _hover_states[i] else 1.0
        _text_scales[i] += (target_scale - _text_scales[i]) * SCALE_SPEED * dt

        size = max(24, min(48, int(36 * _text_scales[i])))
        size += size % 2
        current_font = _get_font(size)

        text_surf = current_font.render(text, True, gold_base)
        text_rect = text_surf.get_rect(center=(400, y + 25))

        for alpha_color in glow_colors[:3]:
            glow_surf = current_font.render(text, True, alpha_color)
            screen.blit(glow_surf, glow_surf.get_rect(center=(400, y + 25)))

        screen.blit(text_surf, text_rect)

        if _text_scales[i] > 1.05:
            ul_len = int(text_rect.width * min(1.0, (_text_scales[i] - 1.0) / (TARGET_SCALE - 1.0)))
            pygame.draw.line(screen, gold_light,
                             (400 - ul_len // 2, text_rect.bottom + 2),
                             (400 + ul_len // 2, text_rect.bottom + 2), 2)

# ---------------------------------------------------------------------------
# Build mode — main grid draw
# ---------------------------------------------------------------------------

def draw_grid(screen, clock):
    global copy_button_rect, delete_button_rect_popup, paste_button_rect, paste_component_popup_rect

    screen.fill((30, 30, 30))

    # Smooth camera / zoom
    state.zoom     = lerp(state.zoom,     state.target_zoom,     0.1)
    state.camera_x = lerp(state.camera_x, state.target_camera_x, 0.15)
    state.camera_y = lerp(state.camera_y, state.target_camera_y, 0.15)

    grid_size_zoomed = round(GRID_SIZE * state.zoom)
    grid_color_fade  = (100, 100, 100)

    start_x = max(0, int(state.camera_x // GRID_SIZE) - 1)
    end_x   = min(state.grid_width,  int((state.camera_x + screen.get_width()  / state.zoom) // GRID_SIZE) + 2)
    start_y = max(0, int(state.camera_y // GRID_SIZE) - 1)
    end_y   = min(state.grid_height, int((state.camera_y + screen.get_height() / state.zoom) // GRID_SIZE) + 2)

    if grid_size_zoomed < 2:
        step = max(1, int(5 / state.zoom))
        for x in range(start_x, end_x, step):
            for y in range(start_y, end_y, step):
                if state.grid[y][x]["type"] != "empty":
                    gx = round((x * GRID_SIZE - state.camera_x) * state.zoom)
                    gy = round((y * GRID_SIZE - state.camera_y) * state.zoom)
                    pygame.draw.rect(screen, (100, 100, 100),
                                     (gx, gy, max(1, grid_size_zoomed), max(1, grid_size_zoomed)))
        return _draw_overlay(screen, clock)

    for x in range(start_x, end_x):
        for y in range(start_y, end_y):
            gx = round((x * GRID_SIZE - state.camera_x) * state.zoom)
            gy = round((y * GRID_SIZE - state.camera_y) * state.zoom)
            if -grid_size_zoomed < gx < screen.get_width() and -grid_size_zoomed < gy < screen.get_height():
                rect = pygame.Rect(gx, gy, grid_size_zoomed, grid_size_zoomed)
                pygame.draw.rect(screen, grid_color_fade, rect, 1)
                _draw_cell(screen, x, y, rect)

    _draw_lasso(screen)
    _draw_placement_preview(screen)
    copy_button_rect, delete_button_rect_popup, paste_button_rect, paste_component_popup_rect = \
        _draw_selection_popup(screen)
    _draw_selected_highlights(screen)

    return _draw_overlay(screen, clock)


def _draw_cell(screen, x, y, rect):
    cell = state.grid[y][x]
    if cell["type"] == "empty":
        return

    ctype = cell["type"]

    if ctype == "redstone":
        color = (255, 0, 0) if cell["powered"] else (100, 0, 0)
        pygame.draw.rect(screen, color, rect)

    elif ctype == "bridge":
        pygame.draw.rect(screen, (120, 120, 255), rect)
        pygame.draw.line(screen, (200, 200, 255), rect.midleft,  rect.midright, 3)
        pygame.draw.line(screen, (200, 200, 255), rect.midtop,   rect.midbottom, 3)

    elif ctype == "power":
        pygame.draw.rect(screen, (255, 255, 0), rect)

    elif ctype == "clock":
        color = (0, 200, 200) if cell["powered"] else (0, 100, 100)
        pygame.draw.rect(screen, color, rect)

    elif ctype.endswith("one_way"):
        _draw_one_way(screen, cell, rect)

    elif ctype == "gate":
        _draw_gate(screen, cell, rect)


def _draw_one_way(screen, cell, rect):
    pygame.draw.rect(screen, (255, 100, 0), rect)
    cx, cy = rect.center
    s = rect.width
    try:
        rot = int(cell["type"][0])
    except (ValueError, IndexError):
        rot = 0
    arrows = {
        0: [(cx - s//4, cy - s//4), (cx - s//4, cy + s//4), (cx + s//4, cy)],
        1: [(cx - s//4, cy - s//4), (cx + s//4, cy - s//4), (cx, cy + s//4)],
        2: [(cx + s//4, cy - s//4), (cx + s//4, cy + s//4), (cx - s//4, cy)],
        3: [(cx - s//4, cy + s//4), (cx + s//4, cy + s//4), (cx, cy - s//4)],
    }
    pygame.draw.polygon(screen, (255, 200, 0), arrows.get(rot, arrows[0]))


def _draw_gate(screen, cell, rect):
    gate_type = cell["gate_type"]
    gate_def  = GATE_DEFINITIONS.get(gate_type, {})
    local_pos = cell.get("local_pos", (0, 0))
    inputs    = gate_def.get("inputs", [])
    output    = gate_def.get("output", (-1, -1))
    u_shape   = inputs + [output]

    logic = gate_type.split("-", 1)[1] if "-" in gate_type else gate_type
    rot   = int(gate_type.split("-")[0])

    COLOR_MAP = {
        "not":  ((30, 30, 180),   (90, 140, 255)),
        "xor":  ((255, 255, 0),   (0, 200, 200)),
        "nor":  ((130, 0, 0),     (255, 80, 120)),
        "nand": ((90, 0, 140),    (200, 0, 255)),
        "or":   ((255, 130, 0),   (255, 200, 0)),
        "and":  ((0, 120, 0),     (0, 255, 0)),
    }
    off_col, on_col = COLOR_MAP.get(logic, ((80, 80, 80), (200, 200, 200)))

    if local_pos in u_shape:
        color = off_col if not cell["powered"] else on_col
        pygame.draw.rect(screen, color, rect)

    # NOT arrow overlay
    if logic == "not" and local_pos in u_shape:
        cx, cy = rect.center
        aw = max(4, rect.width // 3)
        ah = max(6, rect.height // 2)
        arrows = {
            0: [(cx, rect.bottom - 3), (cx - aw, rect.bottom - ah), (cx + aw, rect.bottom - ah)],
            1: [(rect.right - 3, cy),  (rect.right - ah, cy - aw),  (rect.right - ah, cy + aw)],
            2: [(cx, rect.top + 3),    (cx - aw, rect.top + ah),    (cx + aw, rect.top + ah)],
            3: [(rect.left + 3, cy),   (rect.left + ah, cy - aw),   (rect.left + ah, cy + aw)],
        }
        col = (80, 180, 255) if local_pos in inputs else (255, 220, 80)
        pygame.draw.polygon(screen, col, arrows.get(rot, arrows[0]))


def _draw_lasso(screen):
    if state.placement_mode == "select" and state.lasso_start and state.lasso_end:
        x1, y1 = state.lasso_start
        x2, y2 = state.lasso_end
        gx1 = round((x1 * GRID_SIZE - state.camera_x) * state.zoom)
        gy1 = round((y1 * GRID_SIZE - state.camera_y) * state.zoom)
        gx2 = round((x2 * GRID_SIZE - state.camera_x) * state.zoom)
        gy2 = round((y2 * GRID_SIZE - state.camera_y) * state.zoom)
        rect = pygame.Rect(min(gx1, gx2), min(gy1, gy2),
                           abs(gx2 - gx1) + GRID_SIZE, abs(gy2 - gy1) + GRID_SIZE)
        pygame.draw.rect(screen, (100, 200, 255), rect, 2)


def _draw_placement_preview(screen):
    pm = state.placement_mode
    if pm not in ["redstone", "power", "or", "and", "not", "xor", "nor", "nand"]:
        return
    mx, my = pygame.mouse.get_pos()
    gx = int((mx / state.zoom + state.camera_x) // GRID_SIZE)
    gy = int((my / state.zoom + state.camera_y) // GRID_SIZE)
    if not (0 <= gx < state.grid_width and 0 <= gy < state.grid_height):
        return

    sx = round((gx * GRID_SIZE - state.camera_x) * state.zoom)
    sy = round((gy * GRID_SIZE - state.camera_y) * state.zoom)
    sz = round(GRID_SIZE * state.zoom)

    if pm in ["redstone", "power"]:
        pygame.draw.rect(screen, (255, 248, 189), pygame.Rect(sx, sy, sz, sz), 3)
    else:
        type_key = f"{state.rotation}-{pm}"
        gate_def = GATE_DEFINITIONS.get(type_key)
        if gate_def:
            for dx, dy in gate_def["inputs"]:
                _preview_cell(screen, gx + dx, gy + dy, (0, 255, 0))
            _preview_cell(screen, gx + gate_def["output"][0], gy + gate_def["output"][1], (255, 200, 0))


def _preview_cell(screen, gx, gy, color):
    if not (0 <= gx < state.grid_width and 0 <= gy < state.grid_height):
        return
    sx = round((gx * GRID_SIZE - state.camera_x) * state.zoom)
    sy = round((gy * GRID_SIZE - state.camera_y) * state.zoom)
    sz = round(GRID_SIZE * state.zoom)
    pygame.draw.rect(screen, color, pygame.Rect(sx, sy, sz, sz), 3)


def _draw_selection_popup(screen):
    """Draw copy/delete/paste/component buttons when cells are selected.
    Returns (copy_rect, delete_rect, paste_rect, component_rect) or all None."""
    if not state.selected_cells:
        if hasattr(_draw_selection_popup, "scales"):
            _draw_selection_popup.scales = {k: 1.0 for k in _draw_selection_popup.scales}
        return None, None, None, None

    xs = [x for x, _ in state.selected_cells]
    ys = [y for _, y in state.selected_cells]
    px = round((max(xs) * GRID_SIZE - state.camera_x) * state.zoom) + 10
    py = round((min(ys) * GRID_SIZE - state.camera_y) * state.zoom) - 160
    bw, bh = 80, 30

    defs = [
        ("copy",      pygame.Rect(px, py,                    bw, bh), "Copy",      (100, 200, 100)),
        ("delete",    pygame.Rect(px, py + (bh + 5),         bw, bh), "Delete",    (200, 80, 80)),
        ("paste",     pygame.Rect(px, py + 2 * (bh + 5),     bw, bh), "Paste",     (80, 180, 255) if state.clipboard else (120, 120, 120)),
        ("component", pygame.Rect(px, py + 3 * (bh + 5),     bw, bh), "Component", (255, 180, 80)),
    ]

    if not hasattr(_draw_selection_popup, "scales"):
        _draw_selection_popup.scales = {name: 1.0 for name, *_ in defs}
    scales = _draw_selection_popup.scales

    gold = (255, 248, 189)
    mouse_pos = pygame.mouse.get_pos()
    for name, rect, label, _ in defs:
        hover = rect.collidepoint(mouse_pos)
        scales[name] += ((1.13 if hover else 1.0) - scales[name]) * 0.18
        sc = scales[name]
        dr = pygame.Rect(0, 0, int(rect.width * sc), int(rect.height * sc))
        dr.center = rect.center

        if hover:
            gs = pygame.Surface((dr.width + 20, dr.height + 20), pygame.SRCALPHA)
            gc = (gs.get_width() // 2, gs.get_height() // 2)
            for i in range(8, 0, -1):
                a = int(40 * i / 8)
                r = int((min(dr.width, dr.height) // 2 + 10) * i / 8)
                for rr in range(r, 0, -2):
                    pygame.draw.circle(gs, (*gold, max(1, int(a * rr / r))), gc, rr)
            screen.blit(gs, (dr.x - 10, dr.y - 10))
            border = pygame.Rect(dr.x - 2, dr.y - 2, dr.width + 4, dr.height + 4)
            pygame.draw.rect(screen, gold, border, 3, border_radius=10)

        pygame.draw.rect(screen, gold if hover else (50, 50, 50), dr, border_radius=8)
        fsz = 22 if len(label) > 8 else 24
        txt = _get_font(fsz).render(label, True, (30, 30, 30) if hover else (255, 255, 255))
        screen.blit(txt, txt.get_rect(center=dr.center))

    return defs[0][1], defs[1][1], defs[2][1], defs[3][1]


def _draw_selected_highlights(screen):
    sz = round(GRID_SIZE * state.zoom)
    for x, y in state.selected_cells:
        gx = round((x * GRID_SIZE - state.camera_x) * state.zoom)
        gy = round((y * GRID_SIZE - state.camera_y) * state.zoom)
        if -sz < gx < screen.get_width() and -sz < gy < screen.get_height():
            pygame.draw.rect(screen, (255, 255, 0), (gx, gy, sz, sz), 3)


# ---------------------------------------------------------------------------
# Overlay (HUD elements drawn on top of grid)
# ---------------------------------------------------------------------------

def _draw_overlay(screen, clock):
    _draw_hamburger_icon(screen)
    _draw_cell_inspector(screen, clock)
    _draw_component_placement_error(screen)
    _draw_no_component_error(screen)
    zoom_info = _draw_zoom_bar(screen)
    _draw_side_toolbar(screen)
    if state.menu_open:
        _draw_side_menu(screen)
    return zoom_info


def _draw_hamburger_icon(screen):
    mouse_pos = pygame.mouse.get_pos()
    state.menu_icon_hover = menu_button_rect.collidepoint(mouse_pos)
    target = 1.0 if (state.menu_icon_hover or state.menu_open) else 0.0
    state.menu_icon_animation = lerp(state.menu_icon_animation, target, 0.2)

    x, y, w, t, sp = 20, 15, 24, 3, 5
    base = (200, 200, 200); hov = (240, 240, 240)
    a = state.menu_icon_animation
    col = (int(lerp(base[0], hov[0], a)), int(lerp(base[1], hov[1], a)), int(lerp(base[2], hov[2], a)))

    if not state.menu_open:
        for i in range(3):
            pygame.draw.rect(screen, col, (x, y + i * (t + sp + 3 * a), w, t))
    else:
        cx, cy = x + w // 2, y + (t * 2 + sp * 2) // 2
        ll = w * min(1.0, a * 1.5)
        for angle in [45, -45]:
            ex = cx + ll * math.cos(math.radians(angle))
            ey = cy + ll * math.sin(math.radians(angle))
            pygame.draw.line(screen, col,
                             (cx - ll * math.cos(math.radians(angle)),
                              cy - ll * math.sin(math.radians(angle))),
                             (ex, ey), t)


def _draw_cell_inspector(screen, clock):
    # FPS update
    state.frame_count += 1
    state.fps_timer += clock.get_time()
    if state.fps_timer >= 1000:
        state.current_fps = state.frame_count
        state.frame_count = 0
        state.fps_timer = 0

    mx, my = pygame.mouse.get_pos()
    gx = int((mx / state.zoom + state.camera_x) // GRID_SIZE)
    gy = int((my / state.zoom + state.camera_y) // GRID_SIZE)
    if not (0 <= gx < state.grid_width and 0 <= gy < state.grid_height):
        return

    cell = state.grid[gy][gx]
    lines = [
        f"FPS: {state.current_fps}",
        f"Cell: ({gx}, {gy})",
        f"Type: {cell.get('type', 'empty')}",
        f"Powered: {cell.get('powered', False)}",
    ]
    if cell["type"] == "gate":
        gate_def = GATE_DEFINITIONS.get(cell.get("gate_type"))
        local_pos = cell.get("local_pos", "?")
        lines += [
            f"Gate ID: {cell.get('gate_id', 'N/A')}",
            f"Gate type: {cell.get('gate_type', '?')}",
            f"Local pos: {local_pos}",
        ]
        if gate_def:
            lines.append(f"Inputs: {gate_def['inputs']}")
            lines.append(f"Output: {gate_def['output']}")
    elif cell["type"] == "clock":
        lines += [f"Frequency: {cell.get('frequency', '?')}", f"Timer: {cell.get('timer', '?')}"]

    insp_font = pygame.font.Font(None, 24)
    rendered = [insp_font.render(str(l), True, (255, 255, 255)) for l in lines]
    bw = max(s.get_width() for s in rendered) + 16
    bh = sum(s.get_height() + 2 for s in rendered) + 10
    box = pygame.Rect(10, 10, bw, bh)
    pygame.draw.rect(screen, (30, 30, 30), box)
    pygame.draw.rect(screen, (80, 200, 255), box, 2)
    iy = box.y + 5
    for s in rendered:
        screen.blit(s, (box.x + 8, iy))
        iy += s.get_height() + 2


def _draw_component_placement_error(screen):
    if state.placement_error_timer <= 0:
        return
    _draw_error(screen, "Cannot place component here!", state.placement_error_timer)
    state.placement_error_timer -= 1


def _draw_no_component_error(screen):
    if state.no_components_error <= 0:
        return
    _draw_error(screen, "You need to create a component first!", state.no_components_error)
    state.no_components_error -= 1


def _draw_error(screen, text, timer):
    ef = pygame.font.Font(None, 32)
    surf = ef.render(text, True, (255, 100, 100))
    er = surf.get_rect(center=(screen.get_width() // 2, screen.get_height() // 2))
    bg = er.inflate(20, 10)
    alpha = min(255, timer * 8)
    fade = pygame.Surface(bg.size, pygame.SRCALPHA)
    fade.fill((50, 20, 20, alpha))
    screen.blit(fade, bg)
    pygame.draw.rect(screen, (200, 100, 100), bg, 2, border_radius=8)
    surf.set_alpha(alpha)
    screen.blit(surf, er)


def _draw_zoom_bar(screen):
    mouse_x, mouse_y = pygame.mouse.get_pos()
    target_anim = 1.0 if mouse_y > screen.get_height() - 100 else 0.0
    state.zoom_bar_anim += (target_anim - state.zoom_bar_anim) * 0.3
    if state.zoom_bar_anim < 0.01:
        return None

    bh = state.zoom_bar_height
    bar_y = screen.get_height() - int(bh * state.zoom_bar_anim)
    pygame.draw.rect(screen, (40, 40, 40), pygame.Rect(0, bar_y, screen.get_width(), bh))
    pygame.draw.rect(screen, (80, 80, 80), pygame.Rect(0, bar_y, screen.get_width(), 2))

    zf = pygame.font.Font(None, 24)
    screen.blit(zf.render("Zoom:", True, (255, 255, 255)), (20, bar_y + 20))
    screen.blit(zf.render(f"{int(state.zoom * 100)}%", True, (255, 255, 255)), (80, bar_y + 20))

    sx, sy, sw, sh = 180, bar_y + 25, 200, 10
    slider_track = pygame.Rect(sx, sy, sw, sh)
    pygame.draw.rect(screen, (60, 60, 60), slider_track, border_radius=5)
    min_z, max_z = 0.05, 3.0
    ratio = max(0.0, min(1.0, (state.zoom - min_z) / (max_z - min_z)))
    handle = pygame.Rect(sx + int(ratio * sw) - 5, sy - 5, 10, sh + 10)
    pygame.draw.rect(screen, (120, 120, 255), handle, border_radius=3)

    mouse_pos = pygame.mouse.get_pos()
    zoom_out = pygame.Rect(400, bar_y + 15, 30, 30)
    zoom_in  = pygame.Rect(440, bar_y + 15, 30, 30)
    reset    = pygame.Rect(480, bar_y + 15, 60, 30)
    propagate_btn = pygame.Rect(550, bar_y + 15, 100, 30)

    for btn, label in [(zoom_out, "-"), (zoom_in, "+")]:
        col = (80, 80, 200) if btn.collidepoint(mouse_pos) else (60, 60, 60)
        pygame.draw.rect(screen, col, btn, border_radius=5)
        t = zf.render(label, True, (255, 255, 255))
        screen.blit(t, t.get_rect(center=btn.center))

    rcol = (80, 80, 200) if reset.collidepoint(mouse_pos) else (60, 60, 60)
    pygame.draw.rect(screen, rcol, reset, border_radius=5)
    rt = zf.render("Reset", True, (255, 255, 255))
    screen.blit(rt, rt.get_rect(center=reset.center))

    pcol = (175, 225, 175) if state.propagation_mode else (191, 96, 87)
    pygame.draw.rect(screen, pcol, propagate_btn, border_radius=5)
    pt = zf.render("Propagate", True, (255, 255, 255))
    screen.blit(pt, pt.get_rect(center=propagate_btn.center))

    return {
        "zoom_out_button":      zoom_out,
        "zoom_in_button":       zoom_in,
        "reset_button":         reset,
        "slider_track":         slider_track,
        "propagate_mode_button": propagate_btn,
        "visible":              state.zoom_bar_anim > 0.01,
    }


def _draw_side_toolbar(screen):
    offset = int(120 * (1 - state.item_menu_anim))
    panel = item_menu_rect.move(offset, 0)
    pygame.draw.rect(screen, (60, 60, 60), panel)

    mouse_pos = pygame.mouse.get_pos()
    for mode, rect, label in BUTTON_DEFS:
        moved = rect.move(offset, 0)
        hover = moved.collidepoint(mouse_pos)
        active = state.placement_mode == mode
        tgt = 1.15 if (hover or active) else 1.0
        state.button_scales[mode] = state.button_scales.get(mode, 1.0)
        state.button_scales[mode] += (tgt - state.button_scales[mode]) * 0.18
        sc = state.button_scales[mode]
        dr = pygame.Rect(0, 0, int(rect.width * sc), int(rect.height * sc))
        dr.center = moved.center

        base = GATE_COLORS.get(mode, (255, 255, 255))
        pastel = tuple(min(255, int(c * 0.6 + 255 * 0.4)) for c in base)
        fill = pastel if (hover or active) else (0, 0, 0)

        if hover or active:
            gs = pygame.Surface((dr.width, dr.height), pygame.SRCALPHA)
            gc = (dr.width // 2, dr.height // 2)
            mr = int(min(dr.width, dr.height) * 0.95)
            for i in range(10, 0, -1):
                pygame.draw.circle(gs, (*base, int(80 * i / 10)), gc, int(mr * i / 10))
            screen.blit(gs, dr.topleft)

        pygame.draw.rect(screen, fill, dr, border_radius=8)
        fsz = 24 if len(label) > 8 else 28
        txt = _get_font(fsz).render(label, True, (255, 255, 255))
        screen.blit(txt, txt.get_rect(center=dr.center))


def _draw_side_menu(screen):
    pygame.draw.rect(screen, (50, 50, 50), side_menu_rect)
    mouse_pos = pygame.mouse.get_pos()

    for attr, rect, label, base in [
        ("exit_button_scale", exit_button_rect, "Exit", (200, 80, 80)),
        ("save_button_scale", save_component_button_rect, "Save Component", (80, 180, 255)),
    ]:
        sc = getattr(_draw_side_menu, attr, 1.0)
        hover = rect.collidepoint(mouse_pos)
        sc += ((1.13 if hover else 1.0) - sc) * 0.18
        setattr(_draw_side_menu, attr, sc)

        dr = pygame.Rect(0, 0, int(rect.width * sc), int(rect.height * sc))
        dr.center = rect.center
        pastel = tuple(min(255, int(c * 0.6 + 255 * 0.4)) for c in base)
        fill = pastel if hover else (50, 50, 50)

        if hover:
            gs = pygame.Surface((dr.width, dr.height), pygame.SRCALPHA)
            gc = (dr.width // 2, dr.height // 2)
            mr = int(min(dr.width, dr.height) * 0.95)
            for i in range(10, 0, -1):
                pygame.draw.circle(gs, (*base, int(80 * i / 10)), gc, int(mr * i / 10))
            screen.blit(gs, dr.topleft)

        pygame.draw.rect(screen, fill, dr, border_radius=8)
        txt = _get_font(28).render(label, True, (255, 255, 255))
        screen.blit(txt, txt.get_rect(center=dr.center))

# ---------------------------------------------------------------------------
# Component list screen
# ---------------------------------------------------------------------------

_component_delete_rects = []

def draw_components_list(screen, components, selected_index, paste_mode=False):
    global _component_delete_rects
    screen.fill((30, 30, 30))

    back_rect = pygame.Rect(20, 20, 80, 40)
    pygame.draw.rect(screen, (80, 80, 80), back_rect, border_radius=8)
    screen.blit(_get_font(32).render("Back", True, (255, 255, 255)), back_rect.move(10, 5))

    title = "Select Component to Paste" if paste_mode else "Components"
    title_col = (100, 255, 100) if paste_mode else (255, 255, 255)
    ts = _get_font(36).render(title, True, title_col)
    screen.blit(ts, (screen.get_width() // 2 - ts.get_width() // 2, 50))

    _component_delete_rects = []
    y = 100
    for i, comp in enumerate(components):
        col = (255, 255, 0) if i == selected_index else (200, 200, 200)
        screen.blit(font.render(comp["name"], True, col), (100, y))
        if not paste_mode:
            dr = pygame.Rect(350, y, 80, 32)
            pygame.draw.rect(screen, (200, 80, 80), dr, border_radius=8)
            dt = _get_font(28).render("Delete", True, (255, 255, 255))
            screen.blit(dt, dt.get_rect(center=dr.center))
            _component_delete_rects.append(dr)
        else:
            _component_delete_rects.append(None)
        y += 40

    if components:
        hint = "Click to paste" if paste_mode else "Click to edit"
        screen.blit(font.render(hint, True, (100, 255, 100) if paste_mode else (180, 180, 255)), (400, 80))

    return _component_delete_rects

# ---------------------------------------------------------------------------
# Naming prompt screen
# ---------------------------------------------------------------------------

def draw_naming_prompt(screen, input_text):
    screen.fill((30, 30, 30))
    pf = _get_font(40)
    ps = pf.render("Enter component name:", True, (255, 255, 255))
    screen.blit(ps, (screen.get_width() // 2 - ps.get_width() // 2, screen.get_height() // 2 - 80))

    box = pygame.Rect(screen.get_width() // 2 - 150, screen.get_height() // 2 - 20, 300, 50)
    pygame.draw.rect(screen, (80, 80, 80), box, border_radius=8)
    inf = _get_font(36)
    screen.blit(inf.render(input_text, True, (0, 255, 0)), (box.x + 10, box.y + 10))

    save_rect = pygame.Rect(screen.get_width() // 2 - 60, screen.get_height() // 2 + 50, 120, 40)
    pygame.draw.rect(screen, (0, 200, 0), save_rect, border_radius=8)
    screen.blit(inf.render("Save", True, (255, 255, 255)), save_rect.move(20, 5))
    return save_rect