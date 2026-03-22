"""
components.py — saving, loading, and placing named circuit components.
"""

import json
import os

import state
from constants import COMPONENTS_FILE, GATE_DEFINITIONS


def save_component(name=None):
    """Save every non-empty cell in the current grid as a named component."""
    min_x, max_x = state.grid_width, -1
    min_y, max_y = state.grid_height, -1

    for y in range(state.grid_height):
        for x in range(state.grid_width):
            if state.grid[y][x]["type"] != "empty":
                min_x, max_x = min(min_x, x), max(max_x, x)
                min_y, max_y = min(min_y, y), max(max_y, y)

    if max_x == -1:
        component_grid = [[{"type": "empty", "powered": False}]]
        width, height = 1, 1
    else:
        width  = max_x - min_x + 1
        height = max_y - min_y + 1
        component_grid = [
            [state.grid[y][x].copy() for x in range(min_x, max_x + 1)]
            for y in range(min_y, max_y + 1)
        ]

    if not name:
        name = "Component"

    component = {"name": name, "width": width, "height": height, "grid": component_grid}
    components = load_components()
    components.append(component)

    path = _components_path()
    with open(path, "w") as f:
        json.dump(components, f)
    print(f"Component '{name}' saved!")


def load_components():
    path = _components_path()
    if not os.path.exists(path):
        return []
    with open(path, "r") as f:
        return json.load(f)


def delete_component(index):
    components = load_components()
    if 0 <= index < len(components):
        del components[index]
        with open(_components_path(), "w") as f:
            json.dump(components, f)


def can_place_component(component, x, y):
    comp_w, comp_h = component["width"], component["height"]
    if x + comp_w > state.grid_width or y + comp_h > state.grid_height:
        return False
    for dy in range(comp_h):
        for dx in range(comp_w):
            if state.grid[y + dy][x + dx]["type"] != "empty":
                return False
    return True


def place_component(component, x, y):
    comp_w, comp_h = component["width"], component["height"]
    comp_grid = component["grid"]
    old_to_new = {}

    for dy in range(comp_h):
        for dx in range(comp_w):
            cell = comp_grid[dy][dx].copy()
            if cell.get("type") == "gate" and "local_pos" in cell:
                if isinstance(cell["local_pos"], list):
                    cell["local_pos"] = tuple(cell["local_pos"])
                old_id = cell.get("gate_id")
                if old_id is not None:
                    if old_id not in old_to_new:
                        old_to_new[old_id] = state.gate_counter
                        state.gate_counter += 1
                    cell["gate_id"] = old_to_new[old_id]
            state.grid[y + dy][x + dx] = cell

    print(f"Component '{component['name']}' placed at ({x}, {y})")


def load_component_to_grid(component, index=None):
    """Replace the entire grid with the contents of a saved component (for editing)."""
    comp_w, comp_h = component["width"], component["height"]
    comp_grid = component["grid"]
    state.grid_width, state.grid_height = comp_w, comp_h

    state.grid = []
    for row in comp_grid:
        new_row = []
        for cell in row:
            new_cell = cell.copy()
            if new_cell.get("type") == "gate" and isinstance(new_cell.get("local_pos"), list):
                new_cell["local_pos"] = tuple(new_cell["local_pos"])
            new_row.append(new_cell)
        state.grid.append(new_row)

    # Reassign gate IDs to guarantee uniqueness
    state.gate_counter = 0
    for y in range(state.grid_height):
        for x in range(state.grid_width):
            cell = state.grid[y][x]
            if cell.get("type") == "gate" and cell.get("local_pos") == (0, 0):
                gate_type = cell.get("gate_type")
                if gate_type in GATE_DEFINITIONS:
                    gate_def = GATE_DEFINITIONS[gate_type]
                    w, h = gate_def["size"]
                    new_id = state.gate_counter
                    for dy in range(h):
                        for dx in range(w):
                            gx, gy = x + dx, y + dy
                            if (0 <= gx < state.grid_width and 0 <= gy < state.grid_height
                                    and state.grid[gy][gx].get("gate_type") == gate_type):
                                state.grid[gy][gx]["gate_id"] = new_id
                    state.gate_counter += 1

    state.editing_component_index = index

    # Reset camera so small components are visible
    state.camera_x = 0.0
    state.camera_y = 0.0
    state.target_camera_x = 0.0
    state.target_camera_y = 0.0
    state.zoom = 1.0
    state.target_zoom = 1.0


# ---------------------------------------------------------------------------
# Internal
# ---------------------------------------------------------------------------

def _components_path():
    base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, COMPONENTS_FILE)