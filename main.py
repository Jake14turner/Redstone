"""
main.py — game loop and event handling for Redstone Logic simulator.
"""

import pygame
from pygame.locals import *

import state
from constants import (
    WIDTH, HEIGHT, GRID_SIZE,
    MENU, BUILD_MODE, VIEW_COMPONENTS, NAMING_COMPONENT, PASTE_COMPONENT,
)
import drawing as draw
import grid_logic as gl
import components as comp_mgr


# ---------------------------------------------------------------------------
# Initialise pygame and screen
# ---------------------------------------------------------------------------

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT), RESIZABLE)
clock  = pygame.time.Clock()

draw.init()  # Must be called after pygame.init() so fonts are ready
draw._update_rects(WIDTH, HEIGHT)


# ---------------------------------------------------------------------------
# Initialise grid
# ---------------------------------------------------------------------------

def _new_grid(w, h):
    return [[{"type": "empty", "powered": False, "frequency": None, "timer": 0}
             for _ in range(w)] for _ in range(h)]

state.grid = _new_grid(state.grid_width, state.grid_height)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _clear_lasso():
    state.selected_cells.clear()
    state.lasso_start = None
    state.lasso_end   = None


def _delete_gate_at(x, y):
    cell = state.grid[y][x]
    if cell["type"] == "gate":
        from constants import GATE_DEFINITIONS
        gate_def  = GATE_DEFINITIONS[cell["gate_type"]]
        w, h      = gate_def["size"]
        lp        = cell["local_pos"]
        ox, oy    = x - lp[0], y - lp[1]
        for dy in range(h):
            for dx in range(w):
                gx, gy = ox + dx, oy + dy
                if (0 <= gx < state.grid_width and 0 <= gy < state.grid_height
                        and state.grid[gy][gx].get("gate_type") == cell["gate_type"]):
                    state.grid[gy][gx] = {"type": "empty", "powered": False}
    else:
        state.grid[y][x] = {"type": "empty", "powered": False}


def _maybe_propagate():
    if state.propagation_mode:
        gl.propagate_power()


def _grid_pos(mx, my):
    return (int((mx / state.zoom + state.camera_x) // GRID_SIZE),
            int((my / state.zoom + state.camera_y) // GRID_SIZE))


def _in_bounds(x, y):
    return 0 <= x < state.grid_width and 0 <= y < state.grid_height


# ---------------------------------------------------------------------------
# Event handlers
# ---------------------------------------------------------------------------

def _handle_keydown(event):
    if state.state == NAMING_COMPONENT:
        if event.key == pygame.K_RETURN:
            if state.component_name_input.strip():
                comp_mgr.save_component(state.component_name_input.strip())
                state.state = BUILD_MODE
        elif event.key == pygame.K_BACKSPACE:
            state.component_name_input = state.component_name_input[:-1]
        elif len(state.component_name_input) < 20 and event.unicode.isprintable():
            state.component_name_input += event.unicode

    elif state.state == PASTE_COMPONENT and event.key == pygame.K_ESCAPE:
        state.state     = BUILD_MODE
        state.paste_mode = False

    if event.key == pygame.K_r:
        state.rotation = (state.rotation + 1) % 4


def _handle_mousedown(event, zoom_bar_info):
    mx, my = event.pos

    # --- Zoom bar buttons ---
    if state.state == BUILD_MODE and zoom_bar_info and zoom_bar_info.get("visible"):
        zb = zoom_bar_info
        if zb["zoom_out_button"].collidepoint(mx, my):
            state.target_zoom = max(0.05, state.target_zoom / 1.2); return
        if zb["zoom_in_button"].collidepoint(mx, my):
            state.target_zoom = min(3.0, state.target_zoom * 1.2); return
        if zb["reset_button"].collidepoint(mx, my):
            state.target_zoom = 1.0; return
        if zb["propagate_mode_button"].collidepoint(mx, my):
            state.propagation_mode = not state.propagation_mode
            if state.propagation_mode:
                gl.propagate_power()
            return
        if zb["slider_track"].collidepoint(mx, my):
            state.zoom_slider_dragging = True
            r = max(0.0, min(1.0, (mx - zb["slider_track"].x) / zb["slider_track"].width))
            state.target_zoom = 0.05 + r * 2.95; return

    # --- Naming prompt ---
    if state.state == NAMING_COMPONENT:
        save_rect = draw.draw_naming_prompt(screen, state.component_name_input)
        if save_rect.collidepoint(mx, my) and state.component_name_input.strip():
            comp_mgr.save_component(state.component_name_input.strip())
            state.state = BUILD_MODE
        return

    # --- Selection popup buttons ---
    if state.selected_cells:
        cr  = draw.copy_button_rect
        dr  = draw.delete_button_rect_popup
        pr  = draw.paste_button_rect
        pcr = draw.paste_component_popup_rect

        if cr and cr.collidepoint(mx, my):
            xs = [x for x, _ in state.selected_cells]
            ys = [y for _, y in state.selected_cells]
            mnx, mny = min(xs), min(ys)
            state.clipboard = [(x - mnx, y - mny, state.grid[y][x].copy())
                               for x, y in state.selected_cells]
            return

        if dr and dr.collidepoint(mx, my):
            for x, y in state.selected_cells:
                state.grid[y][x] = {"type": "empty", "powered": False}
            state.selected_cells.clear(); return

        if pr and pr.collidepoint(mx, my) and state.clipboard:
            xs = [x for x, _ in state.selected_cells]
            ys = [y for _, y in state.selected_cells]
            bx, by = min(xs), min(ys)
            for dx, dy, cell in state.clipboard:
                gx, gy = bx + dx, by + dy
                if _in_bounds(gx, gy):
                    state.grid[gy][gx] = cell.copy()
            return

        if pcr and pcr.collidepoint(mx, my):
            state.components_list = comp_mgr.load_components()
            if state.components_list:
                state.selected_component_index = 0
                state.paste_mode = True
                state.state = PASTE_COMPONENT
            else:
                state.no_components_error = 120
            return

    # --- Menu screen ---
    if state.state == MENU:
        if 250 <= my <= 300:
            state.grid_width, state.grid_height = 2000, 500
            state.grid = _new_grid(state.grid_width, state.grid_height)
            _clear_lasso()
            state.gate_counter = 0
            state.state = BUILD_MODE
        elif 320 <= my <= 370:
            state.components_list = comp_mgr.load_components()
            state.selected_component_index = 0
            state.state = VIEW_COMPONENTS
        elif 390 <= my <= 440:
            pygame.event.post(pygame.event.Event(pygame.QUIT))
        return

    # --- Build mode ---
    if state.state == BUILD_MODE:
        _handle_build_mousedown(event, mx, my)
        return

    # --- View components ---
    if state.state == VIEW_COMPONENTS:
        _handle_view_mousedown(mx, my); return

    # --- Paste component ---
    if state.state == PASTE_COMPONENT:
        _handle_paste_mousedown(mx, my); return


def _handle_build_mousedown(event, mx, my):
    # Hamburger menu
    if draw.menu_button_rect.collidepoint(mx, my):
        state.menu_open = not state.menu_open

    # Toolbar buttons
    toolbar = [
        (draw.redstone_button_rect, "redstone"),
        (draw.one_way_button_rect, "one_way"),
        (draw.bridge_button_rect, "bridge"),
        (draw.power_button_rect, "power"),
        (draw.or_button_rect, "or"),
        (draw.and_button_rect, "and"),
        (draw.not_button_rect, "not"),
        (draw.xor_button_rect, "xor"),
        (draw.nor_button_rect, "nor"),
        (draw.nand_button_rect, "nand"),
        (draw.lasso_button_rect, "select"),
        (draw.delete_button_rect, "delete"),
        (draw.clock_button_rect, "clock"),
    ]
    for rect, mode in toolbar:
        if rect.collidepoint(mx, my):
            state.placement_mode = mode
            if mode != "select":
                _clear_lasso()
            return

    # Side-menu buttons
    if state.menu_open:
        if draw.exit_button_rect.collidepoint(mx, my):
            state.state = MENU
            state.menu_open = False
            return
        if draw.save_component_button_rect.collidepoint(mx, my):
            state.state = NAMING_COMPONENT
            state.component_name_input = ""
            return

    if event.button == 1:
        if state.placement_mode == "select":
            state.lasso_start = state.lasso_end = _grid_pos(mx, my)
        else:
            x, y = _grid_pos(mx, my)
            if _in_bounds(x, y):
                state.dragging_placement = True
                _place_item(x, y)

    elif event.button == 3:
        state.panning = True
        state.last_mouse_x, state.last_mouse_y = mx, my
    elif event.button == 4:
        state.target_zoom = min(3.0, state.target_zoom * 1.1)
    elif event.button == 5:
        state.target_zoom = max(0.05, state.target_zoom / 1.1)


def _place_item(x, y):
    pm = state.placement_mode
    if pm == "redstone":
        state.grid[y][x] = {"type": "redstone", "powered": False}
    elif pm == "bridge":
        state.grid[y][x] = {"type": "bridge", "powered": False}
    elif pm == "power":
        state.grid[y][x] = {"type": "power", "powered": True}
    elif pm == "clock":
        state.grid[y][x] = {"type": "clock", "powered": False, "frequency": 30, "timer": 0}
    elif pm in ("or", "and", "not", "xor", "nor", "nand"):
        gl.place_gate(x, y, pm, state.rotation)
    elif pm == "one_way":
        gl.place_one_way(x, y, state.rotation)
    elif pm == "delete":
        _delete_gate_at(x, y)
    _maybe_propagate()


def _handle_view_mousedown(mx, my):
    delete_rects = draw._component_delete_rects
    if 20 <= mx <= 100 and 20 <= my <= 60:
        state.state = MENU; return

    for idx, dr in enumerate(delete_rects):
        if dr and dr.collidepoint(mx, my):
            comp_mgr.delete_component(idx)
            state.components_list = comp_mgr.load_components()
            state.selected_component_index = 0
            return

    idx = (my - 100) // 40
    if 0 <= idx < len(state.components_list):
        comp_mgr.load_component_to_grid(state.components_list[idx])
        state.state = BUILD_MODE


def _handle_paste_mousedown(mx, my):
    if 20 <= mx <= 100 and 20 <= my <= 60:
        state.state = BUILD_MODE
        state.paste_mode = False
        return

    idx = (my - 100) // 40
    if 0 <= idx < len(state.components_list):
        selected = state.components_list[idx]
        state.selected_paste_component = selected
        state.state = BUILD_MODE
        state.paste_mode = False
        state.placement_mode = "paste_component"

        # Try to place immediately at last known grid position
        # (user may click again if position invalid)
        if state.selected_cells:
            xs = [x for x, _ in state.selected_cells]
            ys = [y for _, y in state.selected_cells]
            px, py = min(xs), min(ys)
            if comp_mgr.can_place_component(selected, px, py):
                comp_mgr.place_component(selected, px, py)
                _maybe_propagate()
                state.placement_mode = "select"
                state.selected_paste_component = None
            else:
                state.placement_error_timer = 60


def _handle_mousemotion(event):
    mx, my = event.pos

    if state.zoom_slider_dragging:
        # Will be handled in main loop after zoom_bar_info is known
        return

    if state.dragging_placement and state.state == BUILD_MODE:
        x, y = _grid_pos(mx, my)
        if _in_bounds(x, y):
            pm = state.placement_mode
            if pm == "redstone" and state.grid[y][x]["type"] == "empty":
                state.grid[y][x] = {"type": "redstone", "powered": False}; _maybe_propagate()
            elif pm == "bridge" and state.grid[y][x]["type"] == "empty":
                state.grid[y][x] = {"type": "bridge", "powered": False};  _maybe_propagate()
            elif pm == "power" and state.grid[y][x]["type"] == "empty":
                state.grid[y][x] = {"type": "power", "powered": True};    _maybe_propagate()
            elif pm == "delete" and state.grid[y][x]["type"] != "empty":
                _delete_gate_at(x, y); _maybe_propagate()

    elif state.placement_mode == "select" and state.lasso_start:
        state.lasso_end = _grid_pos(mx, my)

    elif state.panning:
        dx = mx - state.last_mouse_x
        dy = my - state.last_mouse_y
        state.target_camera_x -= dx / state.zoom
        state.target_camera_y -= dy / state.zoom
        state.last_mouse_x, state.last_mouse_y = mx, my


def _handle_mouseup(event, zoom_bar_info):
    if event.button == 1:
        state.zoom_slider_dragging = False
        state.dragging_placement   = False

        if state.placement_mode == "select" and state.lasso_start:
            x1, y1 = state.lasso_start
            x2, y2 = state.lasso_end
            xmin, xmax = sorted([x1, x2])
            ymin, ymax = sorted([y1, y2])
            state.selected_cells.clear()
            for y in range(ymin, ymax + 1):
                for x in range(xmin, xmax + 1):
                    if _in_bounds(x, y):
                        state.selected_cells.add((x, y))
            state.lasso_start = state.lasso_end = None

    elif event.button == 3:
        state.panning = False


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

zoom_bar_info = None
running = True
_last_size = (WIDTH, HEIGHT)

while running:
    # Detect window resize (works on macOS/SDL2 where VIDEORESIZE may not fire)
    _cur_size = screen.get_size()
    if _cur_size != _last_size:
        _last_size = _cur_size
        draw._update_rects(*_cur_size)

    # --- Draw ---
    if state.state == MENU:
        draw.draw_menu(screen, clock)
    elif state.state in (VIEW_COMPONENTS, PASTE_COMPONENT):
        paste = (state.state == PASTE_COMPONENT)
        draw.draw_components_list(screen, state.components_list, state.selected_component_index, paste)
    elif state.state == NAMING_COMPONENT:
        draw.draw_naming_prompt(screen, state.component_name_input)
    else:
        zoom_bar_info = draw.draw_grid(screen, clock)

    # Animate item menu slide-in
    mouse_x, _ = pygame.mouse.get_pos()
    tgt = 1.0 if mouse_x > screen.get_width() - 180 else 0.0
    state.item_menu_anim += (tgt - state.item_menu_anim) * 0.3

    # Handle zoom slider drag (needs current zoom_bar_info)
    if state.zoom_slider_dragging and zoom_bar_info and zoom_bar_info.get("visible"):
        mx, _ = pygame.mouse.get_pos()
        track = zoom_bar_info["slider_track"]
        r = max(0.0, min(1.0, (mx - track.x) / track.width))
        state.target_zoom = 0.05 + r * 2.95

    # --- Events ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == VIDEORESIZE:
            screen = pygame.display.set_mode(event.dict['size'], RESIZABLE)
            draw._update_rects(event.w, event.h)
        elif event.type == VIDEOEXPOSE:
            draw._update_rects(*screen.get_size())
        elif event.type == pygame.KEYDOWN:
            _handle_keydown(event)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            _handle_mousedown(event, zoom_bar_info)
        elif event.type == pygame.MOUSEMOTION:
            _handle_mousemotion(event)
        elif event.type == pygame.MOUSEBUTTONUP:
            _handle_mouseup(event, zoom_bar_info)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()