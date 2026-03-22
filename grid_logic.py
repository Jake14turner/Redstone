"""
grid_logic.py — power propagation, gate evaluation, and grid placement.
"""

import state
from constants import GATE_DEFINITIONS, ONE_WAY_TYPES


# ---------------------------------------------------------------------------
# Placement helpers
# ---------------------------------------------------------------------------

def assign_gate_id_to_group(x, y, w, h):
    gate_id = state.gate_counter
    for dy in range(h):
        for dx in range(w):
            state.grid[y + dy][x + dx]["gate_id"] = gate_id
    state.gate_counter += 1


def place_gate(x, y, gate_type, rotation):
    type_key = f"{rotation}-{gate_type}"
    definition = GATE_DEFINITIONS[type_key]
    w, h = definition["size"]

    for dy in range(h):
        for dx in range(w):
            gx, gy = x + dx, y + dy
            if not (0 <= gx < state.grid_width and 0 <= gy < state.grid_height):
                return
            if state.grid[gy][gx]["type"] != "empty":
                return

    for dy in range(h):
        for dx in range(w):
            gx, gy = x + dx, y + dy
            state.grid[gy][gx] = {
                "type": "gate",
                "gate_type": type_key,
                "local_pos": (dx, dy),
                "powered": False,
                "previous_output": False,
                "evaluated_this_cycle": False,
            }

    assign_gate_id_to_group(x, y, w, h)


def place_one_way(x, y, rotation):
    for dy in range(1):
        for dx in range(1):
            gx, gy = x + dx, y + dy
            if not (0 <= gx < state.grid_width and 0 <= gy < state.grid_height):
                return
            if state.grid[gy][gx]["type"] != "empty":
                return

    state.grid[y][x] = {"type": f"{rotation}-one_way", "powered": False}


# ---------------------------------------------------------------------------
# Propagation — main entry point
# ---------------------------------------------------------------------------

def propagate_power():
    real_list = set()
    gates_by_id, real_list = _collect_gates_by_id(real_list)
    _store_previous_gate_outputs(gates_by_id)
    real_list = _reset_power_states(real_list)
    real_list = _process_power_sources_and_clocks(real_list)

    gate_origins = _get_sorted_gate_origins(gates_by_id)

    changed = True
    iterations = 0
    max_iterations = 1
    while changed and iterations < max_iterations:
        changed = False
        iterations += 1
        _reset_gate_evaluation_flags(gates_by_id)
        for x, y, cell in gate_origins:
            gate_def = GATE_DEFINITIONS.get(cell["gate_type"])
            if gate_def:
                _evaluate_single_gate(x, y, cell, gate_def, real_list)


# ---------------------------------------------------------------------------
# Internal propagation helpers
# ---------------------------------------------------------------------------

def _collect_gates_by_id(real_list):
    gates_by_id = {}
    for y in range(state.grid_height):
        for x in range(state.grid_width):
            cell = state.grid[y][x]
            if cell["type"] == "gate" and "gate_id" in cell:
                gates_by_id.setdefault(cell["gate_id"], []).append((x, y, cell))
            if cell["type"] != "empty":
                real_list.add((x, y))
    return gates_by_id, real_list


def _store_previous_gate_outputs(gates_by_id):
    for gate_cells in gates_by_id.values():
        for x, y, cell in gate_cells:
            if cell["local_pos"] == (0, 0):
                gate_def = GATE_DEFINITIONS.get(cell["gate_type"])
                if gate_def:
                    out_dx, out_dy = gate_def["output"]
                    out_x, out_y = x + out_dx, y + out_dy
                    if 0 <= out_x < state.grid_width and 0 <= out_y < state.grid_height:
                        out_cell = state.grid[out_y][out_x]
                        out_cell["previous_output"] = out_cell.get("powered", False)


def _reset_power_states(real_list):
    for x, y in real_list:
        if state.grid[y][x]["type"] != "clock":
            state.grid[y][x]["powered"] = False
    return real_list


def _process_power_sources_and_clocks(real_list):
    for x, y in real_list:
        cell = state.grid[y][x]
        if cell["type"] == "power":
            propagate_from(x, y, real_list)
        elif cell["type"] == "clock":
            cell["timer"] += 1
            if cell["timer"] >= cell["frequency"]:
                cell["powered"] = not cell["powered"]
                cell["timer"] = 0
            if cell["powered"]:
                propagate_from(x, y, real_list)
    return real_list


def _get_sorted_gate_origins(gates_by_id):
    origins = []
    for gate_cells in gates_by_id.values():
        for x, y, cell in gate_cells:
            if cell["local_pos"] == (0, 0):
                origins.append((x, y, cell))
    origins.sort(key=lambda g: (g[0], g[1]))
    return origins


def _reset_gate_evaluation_flags(gates_by_id):
    for gate_cells in gates_by_id.values():
        for x, y, cell in gate_cells:
            cell["evaluated_this_cycle"] = False


def _evaluate_single_gate(x, y, cell, gate_def, real_list):
    out_x, out_y, output_logic = _evaluate_gate_output(x, y, gate_def, real_list)

    if not (0 <= out_x < state.grid_width and 0 <= out_y < state.grid_height):
        return False

    out_cell = state.grid[out_y][out_x]
    out_cell["evaluated_this_cycle"] = True

    if out_cell["powered"] != output_logic:
        out_cell["powered"] = output_logic
        if output_logic:
            propagate_from(out_x, out_y, real_list)
        else:
            propagate_no_power(out_x, out_y, real_list)
        return True
    return False


def _evaluate_gate_output(x, y, definition, real_list):
    current_gate_id = state.grid[y][x].get("gate_id") if 0 <= x < state.grid_width and 0 <= y < state.grid_height else None

    inputs_powered = []
    for dx, dy in definition["inputs"]:
        gx, gy = x + dx, y + dy
        if 0 <= gx < state.grid_width and 0 <= gy < state.grid_height:
            inputs_powered.append(_trace_power_source(gx, gy, real_list, current_gate_id))

    logic = definition["logic"]
    if logic == "or":
        output_logic = any(inputs_powered)
    elif logic == "and":
        output_logic = all(inputs_powered) and len(inputs_powered) == len(definition["inputs"])
    elif logic == "not":
        output_logic = not inputs_powered[0] if inputs_powered else True
    elif logic == "xor":
        output_logic = sum(inputs_powered) == 1
    elif logic == "nor":
        output_logic = not any(inputs_powered)
    elif logic == "nand":
        output_logic = not all(inputs_powered)
    else:
        output_logic = False

    out_dx, out_dy = definition["output"]
    return x + out_dx, y + out_dy, output_logic


def _trace_power_source(x, y, real_list, exclude_gate_id=None):
    visited = set()
    stack = []

    for nx, ny, ndir in [(x+1, y, "horizontal"), (x-1, y, "horizontal"),
                          (x, y+1, "vertical"),   (x, y-1, "vertical")]:
        if 0 <= nx < state.grid_width and 0 <= ny < state.grid_height:
            if exclude_gate_id is None or state.grid[ny][nx].get("gate_id") != exclude_gate_id:
                stack.append((nx, ny, ndir))

    while stack:
        cx, cy, direction = stack.pop()
        if (cx, cy, direction) in visited:
            continue
        if (cx, cy) not in real_list:
            visited.add((cx, cy, direction))
            continue
        visited.add((cx, cy, direction))

        if not (0 <= cx < state.grid_width and 0 <= cy < state.grid_height):
            continue

        cell = state.grid[cy][cx]
        if exclude_gate_id is not None and cell.get("gate_id") == exclude_gate_id:
            continue

        if cell["type"] == "power":
            return cell.get("powered", False)
        elif cell["type"] == "clock":
            return cell.get("powered", False)
        elif cell["type"] == "gate":
            gate_def = GATE_DEFINITIONS.get(cell["gate_type"], {})
            local_pos = cell.get("local_pos", (0, 0))
            if local_pos == gate_def.get("output"):
                if cell.get("evaluated_this_cycle", False):
                    return cell.get("powered", False)
                else:
                    return cell.get("previous_output", False)
            elif local_pos in gate_def.get("inputs", []):
                continue
        elif cell["type"] in ["redstone", "power", "or", "clock"]:
            for nx, ny, ndir in [(cx+1, cy, "horizontal"), (cx-1, cy, "horizontal"),
                                  (cx, cy+1, "vertical"),   (cx, cy-1, "vertical")]:
                if (nx, ny, ndir) not in visited:
                    stack.append((nx, ny, ndir))
        elif cell["type"] == "bridge":
            _push_bridge(stack, visited, cx, cy, direction)

    return False


# ---------------------------------------------------------------------------
# propagate_from / propagate_no_power
# ---------------------------------------------------------------------------

def propagate_from(x, y, real_list, direction=None):
    stack = [(x, y, direction)]
    visited = set()

    while stack:
        cx, cy, direction = stack.pop()
        if (cx, cy, direction) in visited:
            continue
        if (cx, cy) not in real_list:
            visited.add((cx, cy, direction))
            continue
        visited.add((cx, cy, direction))

        if not (0 <= cx < state.grid_width and 0 <= cy < state.grid_height):
            continue

        cell = state.grid[cy][cx]

        if cell["type"] in ["redstone", "power", "or", "clock"]:
            if not cell["powered"] or cell["type"] == "clock":
                cell["powered"] = True
                for nx, ny, ndir in [(cx+1, cy, "horizontal"), (cx-1, cy, "horizontal"),
                                      (cx, cy+1, "vertical"),   (cx, cy-1, "vertical")]:
                    stack.append((nx, ny, ndir))

        elif cell["type"] == "bridge":
            _push_bridge(stack, visited, cx, cy, direction)

        elif cell["type"].endswith("one_way"):
            _propagate_one_way_forward(stack, cell, cx, cy, direction)

        elif cell["type"] == "gate":
            gate_def = GATE_DEFINITIONS.get(cell["gate_type"], {})
            local_pos = cell.get("local_pos")
            if local_pos in gate_def.get("inputs", []):
                cell["powered"] = True
            elif local_pos == gate_def.get("output") and cell["powered"]:
                for nx, ny, ndir in [(cx+1, cy, "horizontal"), (cx-1, cy, "horizontal"),
                                      (cx, cy+1, "vertical"),   (cx, cy-1, "vertical")]:
                    stack.append((nx, ny, ndir))


def propagate_no_power(x, y, real_list=None, direction=None):
    stack = [(x, y, direction)]
    visited = set()

    while stack:
        cx, cy, direction = stack.pop()
        if (cx, cy, direction) in visited:
            continue
        visited.add((cx, cy, direction))

        if not (0 <= cx < state.grid_width and 0 <= cy < state.grid_height):
            continue

        cell = state.grid[cy][cx]
        cell["powered"] = False

        if cell["type"] in ["redstone", "power", "or", "clock"]:
            for nx, ny, ndir in [(cx+1, cy, "horizontal"), (cx-1, cy, "horizontal"),
                                  (cx, cy+1, "vertical"),   (cx, cy-1, "vertical")]:
                stack.append((nx, ny, ndir))
        elif cell["type"] == "bridge":
            _push_bridge(stack, visited, cx, cy, direction)
        elif cell["type"].endswith("one_way"):
            _propagate_one_way_backward(stack, cell, cx, cy, direction)
        elif cell["type"] == "gate":
            gate_def = GATE_DEFINITIONS.get(cell.get("gate_type"), {})
            local_pos = cell.get("local_pos")
            if local_pos in gate_def.get("inputs", []) or local_pos == gate_def.get("output"):
                for nx, ny, ndir in [(cx+1, cy, "horizontal"), (cx-1, cy, "horizontal"),
                                      (cx, cy+1, "vertical"),   (cx, cy-1, "vertical")]:
                    stack.append((nx, ny, ndir))


# ---------------------------------------------------------------------------
# Bridge / one-way helpers
# ---------------------------------------------------------------------------

def _push_bridge(stack, visited, cx, cy, direction):
    if direction == "horizontal":
        for nx, ny in [(cx+1, cy), (cx-1, cy)]:
            if (nx, ny, "horizontal") not in visited:
                stack.append((nx, ny, "horizontal"))
    elif direction == "vertical":
        for nx, ny in [(cx, cy+1), (cx, cy-1)]:
            if (nx, ny, "vertical") not in visited:
                stack.append((nx, ny, "vertical"))
    else:
        for nx, ny, ndir in [(cx+1, cy, "horizontal"), (cx-1, cy, "horizontal"),
                              (cx, cy+1, "vertical"),   (cx, cy-1, "vertical")]:
            if (nx, ny, ndir) not in visited:
                stack.append((nx, ny, ndir))


_OUTPUT_DIRS = [(1, 0), (0, 1), (-1, 0), (0, -1)]
_INPUT_DIRS  = [(-1, 0), (0, -1), (1, 0), (0, 1)]


def _propagate_one_way_forward(stack, cell, cx, cy, direction):
    try:
        rot = int(cell["type"][0])
    except (ValueError, IndexError):
        rot = 0

    input_dir = _INPUT_DIRS[rot]
    coming_from_input = False

    if direction is None:
        coming_from_input = True
    elif direction == "horizontal" and input_dir[0] != 0:
        coming_from_input = True
    elif direction == "vertical" and input_dir[1] != 0:
        coming_from_input = True

    if coming_from_input:
        cell["powered"] = True
        dx, dy = _OUTPUT_DIRS[rot]
        ndir = "horizontal" if dx != 0 else "vertical"
        stack.append((cx + dx, cy + dy, ndir))


def _propagate_one_way_backward(stack, cell, cx, cy, direction):
    try:
        rot = int(cell["type"][0])
    except (ValueError, IndexError):
        rot = 0

    output_dir = _OUTPUT_DIRS[rot]
    should_remove = False

    if direction is None:
        should_remove = True
    elif direction == "horizontal" and output_dir[0] != 0:
        should_remove = True
    elif direction == "vertical" and output_dir[1] != 0:
        should_remove = True

    if should_remove:
        cell["powered"] = False
        dx, dy = _INPUT_DIRS[rot]
        ndir = "horizontal" if dx != 0 else "vertical"
        stack.append((cx + dx, cy + dy, ndir))
