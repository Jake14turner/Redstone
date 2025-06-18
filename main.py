import pygame
import math  
import json
import os

COMPONENTS_FILE = "components.json"
VIEW_COMPONENTS = "view_components"
NAMING_COMPONENT = "naming_component"
component_name_input = ""
editing_component_index = None

def save_component(selected_cells, grid, name=None):
    global grid_width, grid_height
    width, height = grid_width, grid_height
    component_grid = []
    for y in range(height):
        row = []
        for x in range(width):
            cell = grid[y][x]
            row.append(cell)
        component_grid.append(row)
    if not name:
        name = "Component"
    component = {"name": name, "width": width, "height": height, "grid": component_grid}
    components = load_components()
    components.append(component)
    with open(COMPONENTS_FILE, "w") as f:
        json.dump(components, f)
    print(f"Component '{name}' saved!")

def load_components():
    if not os.path.exists(COMPONENTS_FILE):
        return []
    with open(COMPONENTS_FILE, "r") as f:
        return json.load(f)


pygame.init()
WIDTH, HEIGHT = 800, 600
GRID_SIZE = 20
GRID_COLOR = (100, 100, 100, 150)
REDSTONE_BASE = (255, 50, 50)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()
font = pygame.font.Font(None, 36) 


MENU, BUILD_MODE = "menu", "build"
state = MENU  
menu_open = False


camera_x, camera_y = 0, 0
target_camera_x, target_camera_y = camera_x, camera_y
move_speed = 0.15  
zoom = 1.0
target_zoom = zoom
zoom_speed = 0.1

panning = False
last_mouse_x, last_mouse_y = 0, 0


grid_width = 100  
grid_height = 100

grid = [[{"type": "empty", "powered": False, "frequency": None, "timer": 0} for _ in range(grid_width)] for _ in range(grid_height)]
placement_mode = "redstone" 
lasso_start = None
lasso_end = None
selected_cells = set()
item_menu_anim = 0.0  



menu_button_rect = pygame.Rect(10, 10, 40, 40) 
side_menu_rect = pygame.Rect(0, 0, 200, HEIGHT)  
exit_button_rect = pygame.Rect(20, 60, 160, 40) 
item_menu_rect = pygame.Rect(WIDTH - 120, 0, 120, HEIGHT) 
redstone_button_rect = pygame.Rect(WIDTH - 110, 20, 90, 30)
power_button_rect = pygame.Rect(WIDTH - 110, 60, 90, 30)
or_button_rect = pygame.Rect(WIDTH - 110, 100, 90, 30)
and_button_rect = pygame.Rect(WIDTH - 110, 140, 90, 30)
not_button_rect = pygame.Rect(WIDTH - 110, 180, 90, 30)
delete_button_rect = pygame.Rect(WIDTH - 110, 220, 90, 30)
xor_button_rect = pygame.Rect(WIDTH - 110, 260, 90, 30)
nor_button_rect = pygame.Rect(WIDTH - 110, 300, 90, 30)
nand_button_rect = pygame.Rect(WIDTH - 110, 340, 90, 30)
lasso_button_rect = pygame.Rect(WIDTH - 110, 380, 90, 30)
save_component_button_rect = pygame.Rect(20, 110, 160, 40)
clock_button_rect = pygame.Rect(WIDTH - 110, 420, 90, 30)
bridge_button_rect = pygame.Rect(WIDTH - 110, 460, 90, 30) 



clipboard = []


menu_icon_hover = False
menu_icon_animation = 0.0  

def lerp(a, b, t):
    return a + (b - a) * t 
item_menu_anim = 0.0  

button_scales = {mode: 1.0 for mode, _, _ in [
    ("redstone", redstone_button_rect, "Redstone"),
    ("bridge", bridge_button_rect, "Bridge"),
    ("power", power_button_rect, "Power"),
    ("or", or_button_rect, "OR"),
    ("and", and_button_rect, "AND"),
    ("not", not_button_rect, "NOT"),
    ("xor", xor_button_rect, "XOR"),
    ("nor", nor_button_rect, "NOR"),
    ("nand", nand_button_rect, "NAND"),
    ("select", lasso_button_rect, "Lasso"),
    ("delete", delete_button_rect, "Delete"),
    ("clock", clock_button_rect, "Clock"),
]}


rotation = 0
hover_states = {0: False, 1: False, 2: False}
text_scales = [1.0, 1.0, 1.0]
TARGET_SCALE = 1.15 
SCALE_SPEED = 0.2  
GATE_DEFINITIONS = {
    "0-or": {
        "size": (3, 2),
        "inputs": [(0, 0), (2, 0)],
        "output": (1, 1),
        "logic": "or"
    },
    "1-or": {
        "size": (2, 3),
        "inputs": [(0, 0), (0, 2)],
        "output": (1, 1),
        "logic": "or"
    },
    "2-or": {
        "size": (3, 2),
        "inputs": [(0, 1), (2, 1)],
        "output": (1, 0),
        "logic": "or"
    },
    "3-or": {
        "size": (2, 3),
        "inputs": [(1, 0), (1, 2)],
        "output": (0, 1),
        "logic": "or"
    },
    "0-and": {
        "size": (3, 2),
        "inputs": [(0, 0), (2, 0)],
        "output": (1, 1),
        "logic": "and"
    },
    "1-and": {
        "size": (2, 3),
        "inputs": [(0, 0), (0, 2)],
        "output": (1, 1),
        "logic": "and"
    },
    "2-and": {
        "size": (3, 2),
        "inputs": [(0, 1), (2, 1)],
        "output": (1, 0),
        "logic": "and"
    },
    "3-and": {
        "size": (2, 3),
        "inputs": [(1, 0), (1, 2)],
        "output": (0, 1),
        "logic": "and"
    },
    "0-not": {
        "size": (1, 2),
        "inputs": [(0, 0)],
        "output": (0, 1),
        "logic": "not"
    },
    "1-not": {
        "size": (2, 1),
        "inputs": [(1, 0)],
        "output": (0, 0),
        "logic": "not"
    },
    "2-not": {
        "size": (1, 2),
        "inputs": [(0, 1)],
        "output": (0, 0),
        "logic": "not"
    },
    "3-not": {
        "size": (2, 1),
        "inputs": [(0, 0)],
        "output": (1, 0),
        "logic": "not"
    },
    "0-xor": {
        "size": (3, 2),
        "inputs": [(0, 0), (2, 0)],
        "output": (1, 1),
        "logic": "xor"
    },
    "1-xor": {
        "size": (2, 3),
        "inputs": [(0, 0), (0, 2)],
        "output": (1, 1),
        "logic": "xor"
    },
    "2-xor": {
        "size": (3, 2),
        "inputs": [(0, 1), (2, 1)],
        "output": (1, 0),
        "logic": "xor"
    },
    "3-xor": {
        "size": (2, 3),
        "inputs": [(1, 0), (1, 2)],
        "output": (0, 1),
        "logic": "xor"
    },
    "0-nor": {
        "size": (3, 2),
        "inputs": [(0, 0), (2, 0)],
        "output": (1, 1),
        "logic": "nor"
    },
    "1-nor": {
        "size": (2, 3),
        "inputs": [(0, 0), (0, 2)],
        "output": (1, 1),
        "logic": "nor"
    },
    "2-nor": {
        "size": (3, 2),
        "inputs": [(0, 1), (2, 1)],
        "output": (1, 0),
        "logic": "nor"
    },
    "3-nor": {
        "size": (2, 3),
        "inputs": [(1, 0), (1, 2)],
        "output": (0, 1),
        "logic": "nor"
    },
    "0-nand": {
        "size": (3, 2),
        "inputs": [(0, 0), (2, 0)],
        "output": (1, 1),
        "logic": "nand"
    },
    "1-nand": {
        "size": (2, 3),
        "inputs": [(0, 0), (0, 2)],
        "output": (1, 1),
        "logic": "nand"
    },
    "2-nand": {
        "size": (3, 2),
        "inputs": [(0, 1), (2, 1)],
        "output": (1, 0),
        "logic": "nand"
    },
    "3-nand": {
        "size": (2, 3),
        "inputs": [(1, 0), (1, 2)],
        "output": (0, 1),
        "logic": "nand"
    },
}


font_cache = {}
def get_font(size):
    if size not in font_cache:
        font_cache[size] = pygame.font.Font(None, size)
    return font_cache[size]


gold_base = (253, 255, 150)
gold_light = (253, 255, 117)
glow_colors = [(*gold_light, alpha) for alpha in range(50, 0, -10)]


gate_counter = 0

def assign_gate_id_to_group(x, y, w, h):
    global gate_counter
    gate_id = gate_counter
    for dy in range(h):
        for dx in range(w):
            gx = x + dx
            gy = y + dy
            grid[gy][gx]["gate_id"] = gate_id
    gate_counter += 1

def place_gate(x, y, gate_type, rotation):
    typeOfGate = f"{rotation}-{gate_type}"
    definition = GATE_DEFINITIONS[typeOfGate]
    w, h = definition["size"]


    for dy in range(h):
        for dx in range(w):
            gx = x + dx
            gy = y + dy
            if not (0 <= gx < grid_width and 0 <= gy < grid_height):
                return
            if grid[gy][gx]["type"] != "empty":
                return  


    for dy in range(h):
        for dx in range(w):
            gx = x + dx
            gy = y + dy
            grid[gy][gx] = {
                "type": "gate",
                "gate_type": typeOfGate,
                "local_pos": (dx, dy),
                "powered": False
            }


    assign_gate_id_to_group(x, y, w, h)





def draw_menu():
    screen.fill((30, 30, 30))
    mouse_pos = pygame.mouse.get_pos()
    menu_items = [
        ("Make New Component", 250),
        ("View Components", 320),
        ("Exit", 390)
    ]
    

    dt = clock.get_time() / 16.67 
    
    for i, (text, y) in enumerate(menu_items):

        btn_rect = pygame.Rect(250, y - 10, 300, 60)
        hover_states[i] = btn_rect.collidepoint(mouse_pos)
        

        target_scale = TARGET_SCALE if hover_states[i] else 1.0
        text_scales[i] += (target_scale - text_scales[i]) * SCALE_SPEED * dt
        

        current_size = max(24, min(48, int(36 * text_scales[i])))
        current_size = current_size + (current_size % 2) 
        

        current_font = get_font(current_size)
        

        text_surf = current_font.render(text, True, gold_base)
        text_rect = text_surf.get_rect(center=(400, y + 25))
        

        for alpha_color in glow_colors[:3]:
            glow_surf = current_font.render(text, True, alpha_color)
            screen.blit(glow_surf, glow_surf.get_rect(center=(400, y + 25)))
        

        screen.blit(text_surf, text_rect)
        

        if text_scales[i] > 1.05:
            underline_length = int(text_rect.width * min(1.0, (text_scales[i] - 1.0) / (TARGET_SCALE - 1.0)))
            pygame.draw.line(
                screen, gold_light,
                (400 - underline_length//2, text_rect.bottom + 2),
                (400 + underline_length//2, text_rect.bottom + 2),
                2
            )

GREEN = (0, 255, 0)  
GRAY = (169, 169, 169) 
BLUE = (0, 0, 255)  

YELLOW = (255, 255, 0)  
WHITE = (255, 255, 255)  

def draw_cell_inspector():
    mouse_x, mouse_y = pygame.mouse.get_pos()
    grid_x = int((mouse_x / zoom + camera_x) // GRID_SIZE)
    grid_y = int((mouse_y / zoom + camera_y) // GRID_SIZE)
    if 0 <= grid_x < grid_width and 0 <= grid_y < grid_height:
        cell = grid[grid_y][grid_x]
        lines = [
            f"Cell: ({grid_x}, {grid_y})",
            f"Type: {cell.get('type', 'empty')}",
            f"Powered: {cell.get('powered', False)}"
        ]
        if cell["type"] == "gate":
            gate_type = cell.get("gate_type", "?")
            local_pos = cell.get("local_pos", "?")
            gate_id = cell.get("gate_id", "N/A")  
            lines.append(f"Gate ID: {gate_id}") 
            lines.append(f"Gate type: {gate_type}")
            lines.append(f"Local pos: {local_pos}")
            gate_def = GATE_DEFINITIONS.get(gate_type)
            if gate_def:

                lines.append(f"Inputs: {gate_def['inputs']}")
                lines.append(f"Output: {gate_def['output']}")

                input_vals = []
                for dx, dy in gate_def["inputs"]:
                    gx, gy = grid_x - local_pos[0] + dx, grid_y - local_pos[1] + dy
                    if 0 <= gx < grid_width and 0 <= gy < grid_height:
                        input_cell = grid[gy][gx]
                        input_vals.append(input_cell.get("powered", False))
                    else:
                        input_vals.append(None)
                lines.append(f"Input values: {input_vals}")
  
                out_x = grid_x - local_pos[0] + gate_def["output"][0]
                out_y = grid_y - local_pos[1] + gate_def["output"][1]
                output_logic = None
                if 0 <= out_x < grid_width and 0 <= out_y < grid_height:
                    output_logic = grid[out_y][out_x].get("powered", False)
                lines.append(f"Output powered: {output_logic}")
        elif cell["type"] == "clock":
            lines.append(f"Frequency: {cell.get('frequency', '?')}")
            lines.append(f"Timer: {cell.get('timer', '?')}")



        font = pygame.font.Font(None, 24)
        box_w = 0
        box_h = 0
        rendered_lines = []
        for line in lines:
            surf = font.render(str(line), True, (255, 255, 255))
            rendered_lines.append(surf)
            box_w = max(box_w, surf.get_width())
            box_h += surf.get_height() + 2
        box_rect = pygame.Rect(10, 10, box_w + 16, box_h + 10)
        pygame.draw.rect(screen, (30, 30, 30), box_rect)
        pygame.draw.rect(screen, (80, 200, 255), box_rect, 2)
        y = box_rect.y + 5
        for surf in rendered_lines:
            screen.blit(surf, (box_rect.x + 8, y))
            y += surf.get_height() + 2

def draw_hamburger_icon():
    """Draws animated hamburger menu icon that transforms to X when open"""
    global menu_icon_hover, menu_icon_animation
    

    mouse_pos = pygame.mouse.get_pos()
    menu_icon_hover = menu_button_rect.collidepoint(mouse_pos)
    

    target_animation = 1.0 if menu_icon_hover or menu_open else 0.0
    menu_icon_animation = lerp(menu_icon_animation, target_animation, 0.2)
    

    x, y = 20, 15
    width = 24
    thickness = 3
    spacing = 5
    

    base_color = (200, 200, 200)
    hover_color = (240, 240, 240)
    current_color = (
        int(lerp(base_color[0], hover_color[0], menu_icon_animation)),
        int(lerp(base_color[1], hover_color[1], menu_icon_animation)),
        int(lerp(base_color[2], hover_color[2], menu_icon_animation))
    )
    

    if not menu_open:

        current_spacing = spacing + (3 * menu_icon_animation) 
        for i in range(3):
            line_y = y + i * (thickness + current_spacing)
            pygame.draw.rect(screen, current_color, (x, line_y, width, thickness))
    else:

        center_x = x + width // 2
        center_y = y + (thickness * 2 + spacing * 2) // 2
        line_length = width * min(1.0, menu_icon_animation * 1.5)
        

        for angle in [45, -45]:
            end_x = center_x + line_length * math.cos(math.radians(angle))
            end_y = center_y + line_length * math.sin(math.radians(angle))
            pygame.draw.line(
    screen, current_color,
    (center_x - line_length * math.cos(math.radians(angle)),
     center_y - line_length * math.sin(math.radians(angle))),
    (end_x, end_y),
    thickness
)

def clear_lasso_selection():
    global selected_cells, lasso_start, lasso_end
    selected_cells.clear()
    lasso_start = None
    lasso_end = None

def propagate_power():
    for row in grid:
        for cell in row:
            if cell["type"] != "clock":
                cell["powered"] = False


    gates_by_id = {}
    for y in range(grid_height):
        for x in range(grid_width):
            cell = grid[y][x]
            if cell["type"] == "gate" and "gate_id" in cell:
                gates_by_id.setdefault(cell["gate_id"], []).append((x, y, cell))


    for y in range(grid_height):
        for x in range(grid_width):
            cell = grid[y][x]
            if cell["type"] == "power":
                propagate_from(x, y)
            elif cell["type"] == "clock":
                cell["timer"] += 1
                if cell["timer"] >= cell["frequency"]:
                    cell["powered"] = not cell["powered"]
                    cell["timer"] = 0
                if cell["powered"]:
                    propagate_from(x, y)


    changed = True
    iterations = 0
    max_iterations = 20

    while changed and iterations < max_iterations:
        changed = False
        iterations += 1

        for gate_id, gate_cells in gates_by_id.items():
            for x, y, cell in gate_cells:
                gate_def = GATE_DEFINITIONS.get(cell["gate_type"])
                if not gate_def or cell["local_pos"] != (0, 0):
                    continue

                out_x, out_y, output_logic = evaluate_gate_output(x, y, gate_def)

                if not (0 <= out_x < grid_width and 0 <= out_y < grid_height):
                    continue

                out_cell = grid[out_y][out_x]
                if out_cell["powered"] != output_logic:
                    out_cell["powered"] = output_logic
                    propagate_from(out_x, out_y)
                    changed = True







def evaluate_gate_output(x, y, definition):
    inputs_powered = []
    for dx, dy in definition["inputs"]:
        gx, gy = x + dx, y + dy
        if 0 <= gx < grid_width and 0 <= gy < grid_height:
            inputs_powered.append(grid[gy][gx]["powered"])
            print(f"Input cell ({gx}, {gy}) powered: {grid[gy][gx]['powered']}")
    print(f"Evaluating NAND gate at ({x}, {y}) with inputs: {inputs_powered}")
   

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
    out_x, out_y = x + out_dx, y + out_dy

    print(f" -> output: {output_logic}")
    return out_x, out_y, output_logic


def evaluate_gate(x, y, definition):
    inputs_powered = []
    for dx, dy in definition["inputs"]:
        gx, gy = x + dx, y + dy
        if 0 <= gx < grid_width and 0 <= gy < grid_height:
            inputs_powered.append(grid[gy][gx]["powered"])
            
    

    output_logic = False
    if definition["logic"] == "or":
        output_logic = any(inputs_powered)
    elif definition["logic"] == "and":
        output_logic = all(inputs_powered) and len(inputs_powered) == len(definition["inputs"])
    elif definition["logic"] == "not":
        output_logic = (len(inputs_powered) == 1) and (not inputs_powered[0])
    elif definition["logic"] == "xor":
        output_logic = sum(inputs_powered) == 1
    elif definition["logic"] == "nor":
        output_logic = not any(inputs_powered)
    elif definition["logic"] == "nand":
        output_logic = not all(inputs_powered)

    print(f"NAND gate output: {output_logic}")
    out_dx, out_dy = definition["output"]
    out_x, out_y = x + out_dx, y + out_dy
    if output_logic:
        grid[out_y][out_x]["powered"] = True
        propagate_from(out_x, out_y)


def has_powered_input(x, y):
    neighbors = [(x+1, y), (x-1, y), (x, y+1), (x, y-1)]
    for nx, ny in neighbors:
        if 0 <= nx < grid_width and 0 <= ny < grid_height:
            neighbor = grid[ny][nx]
            if neighbor["type"] in ["redstone", "power", "or"] and neighbor["powered"]:
                return True
    return False

def propagate_from(x, y, direction=None):
    stack = [(x, y, direction)]
    visited = set()

    while stack:
        cx, cy, direction = stack.pop()
        if (cx, cy, direction) in visited:
            continue
        visited.add((cx, cy, direction))

        if not (0 <= cx < grid_width and 0 <= cy < grid_height):
            continue

        cell = grid[cy][cx]

        if cell["type"] in ["redstone", "power", "or", "clock"]:
            if not cell["powered"] or cell["type"] == "clock":
                cell["powered"] = True
                for nx, ny, ndir in [
                    (cx+1, cy, "horizontal"),
                    (cx-1, cy, "horizontal"),
                    (cx, cy+1, "vertical"),
                    (cx, cy-1, "vertical")
                ]:
                    stack.append((nx, ny, ndir))

        elif cell["type"] == "bridge":
            if direction == "horizontal":
                for nx, ny in [(cx+1, cy), (cx-1, cy)]:
                    stack.append((nx, ny, "horizontal"))
            elif direction == "vertical":
                for nx, ny in [(cx, cy+1), (cx, cy-1)]:
                    stack.append((nx, ny, "vertical"))
            else:
                for nx, ny, ndir in [
                    (cx+1, cy, "horizontal"),
                    (cx-1, cy, "horizontal"),
                    (cx, cy+1, "vertical"),
                    (cx, cy-1, "vertical")
                ]:
                    stack.append((nx, ny, ndir))

        elif cell["type"] == "gate":
            gate_type = cell.get("gate_type")
            local_pos = cell.get("local_pos")
            gate_def = GATE_DEFINITIONS.get(gate_type, {})

            if local_pos in gate_def.get("inputs", []):
                cell["powered"] = True
                continue

            if local_pos == gate_def.get("output"):
                if not cell["powered"]:
                    cell["powered"] = True
                for nx, ny, ndir in [
                    (cx+1, cy, "horizontal"),
                    (cx-1, cy, "horizontal"),
                    (cx, cy+1, "vertical"),
                    (cx, cy-1, "vertical")
                ]:
                    stack.append((nx, ny, ndir))


                    
def draw_grid():
    global copy_button_rect, delete_button_rect_popup, paste_button_rect
    propagate_power() 

    screen.fill((30, 30, 30))
    global zoom, camera_x, camera_y
    zoom = lerp(zoom, target_zoom, zoom_speed)
    camera_x = lerp(camera_x, target_camera_x, move_speed)
    camera_y = lerp(camera_y, target_camera_y, move_speed)

    grid_alpha = max(50, min(200, int(255 * (zoom / target_zoom))))
    grid_color_fade = (100, 100, 100, grid_alpha)

    for x in range(grid_width):
        for y in range(grid_height):
            grid_x = round((x * GRID_SIZE - camera_x) * zoom)
            grid_y = round((y * GRID_SIZE - camera_y) * zoom)
            size = round(GRID_SIZE * zoom)

            if -size < grid_x < WIDTH and -size < grid_y < HEIGHT:
                rect = pygame.Rect(grid_x, grid_y, size, size)
                pygame.draw.rect(screen, grid_color_fade, rect, 1)

                cell = grid[y][x]
                alpha = max(50, min(255, int(255 * (zoom / target_zoom))))

                if cell["type"] == "redstone":
                    color = (255, 0, 0, alpha) if cell["powered"] else (100, 0, 0, alpha)
                    pygame.draw.rect(screen, color[:3], rect)
                if cell["type"] == "bridge":

                    pygame.draw.rect(screen, (120, 120, 255), rect)
      
                    pygame.draw.line(screen, (200, 200, 255), rect.midleft, rect.midright, 3)
                    pygame.draw.line(screen, (200, 200, 255), rect.midtop, rect.midbottom, 3)
                elif cell["type"] == "power":
                    pygame.draw.rect(screen, (255, 255, 0), rect)
                elif cell["type"] == "clock":
                    color = (0, 200, 200) if cell["powered"] else (0, 100, 100)
                    pygame.draw.rect(screen, color, rect)
                if cell["type"] == "gate":
                    gate_def = GATE_DEFINITIONS.get(cell["gate_type"], {})
                    local_pos = cell.get("local_pos", (0, 0))
                    input_offsets = gate_def.get("inputs", [])
                    output_offset = gate_def.get("output", (-1, -1))


                    u_shape = input_offsets + [output_offset]
                    if cell["gate_type"] in ["0-not", "1-not", "2-not", "3-not"]:
                        not_shape = input_offsets + [output_offset]
                        if local_pos in not_shape:
                            color = (30, 30, 180) if not cell["powered"] else (90, 140, 255)
                            pygame.draw.rect(screen, color, rect)
                            arrow_color_in = (80, 180, 255)
                            arrow_color_out = (255, 220, 80)
                            arrow_w = max(4, rect.width // 3)
                            arrow_h = max(6, rect.height // 2)
                            cx, cy = rect.center
                            rot = int(cell["gate_type"].split('-')[0])

                            if rot == 0:  # Down
                                points = [(cx, rect.bottom - 3), (cx - arrow_w, rect.bottom - arrow_h), (cx + arrow_w, rect.bottom - arrow_h)]
                            elif rot == 1:  # Right
                                points = [(rect.right - 3, cy), (rect.right - arrow_h, cy - arrow_w), (rect.right - arrow_h, cy + arrow_w)]
                            elif rot == 2:  # Up
                                points = [(cx, rect.top + 3), (cx - arrow_w, rect.top + arrow_h), (cx + arrow_w, rect.top + arrow_h)]
                            elif rot == 3:  # Left
                                points = [(rect.left + 3, cy), (rect.left + arrow_h, cy - arrow_w), (rect.left + arrow_h, cy + arrow_w)]
                            if local_pos in input_offsets:
                                pygame.draw.polygon(screen, arrow_color_in, points)
                            if local_pos == output_offset:
                                pygame.draw.polygon(screen, arrow_color_out, points)

                    elif cell["gate_type"] in ["0-xor", "1-xor", "2-xor", "3-xor"]:
                        if local_pos in u_shape:
                            color = (255, 255, 0) if not cell["powered"] else (0, 200, 200)
                            pygame.draw.rect(screen, color, rect)
                            label_text = ""
                            if local_pos in input_offsets:
                                label_text = "IN"
                            elif local_pos == output_offset:
                                label_text = "OUT"
                        

                    elif cell["gate_type"] in ["0-nor", "1-nor", "2-nor", "3-nor"]:
                        if local_pos in u_shape:
                            color = (130, 0, 0) if not cell["powered"] else (255, 80, 120)
                            pygame.draw.rect(screen, color, rect)
                            label_text = ""
                            if local_pos in input_offsets:
                                label_text = "IN"
                            elif local_pos == output_offset:
                                label_text = "OUT"
                        

                    elif cell["gate_type"] in ["0-nand", "1-nand", "2-nand", "3-nand"]:
                        if local_pos in u_shape:
                            color = (90, 0, 140) if not cell["powered"] else (200, 0, 255)
                            pygame.draw.rect(screen, color, rect)
                            label_text = ""
                            if local_pos in input_offsets:
                                label_text = "IN"
                            elif local_pos == output_offset:
                                label_text = "OUT"
                        

                    elif cell["gate_type"] in ["0-or", "1-or", "2-or", "3-or"]:
                        if local_pos in u_shape:
                            color = (255, 130, 0) if not cell["powered"] else (255, 200, 0)
                            pygame.draw.rect(screen, color, rect)
                            label_text = ""
                            if local_pos in input_offsets:
                                label_text = "IN"
                            elif local_pos == output_offset:
                                label_text = "OUT"
                        

                    elif cell["gate_type"] in ["0-and", "1-and", "2-and", "3-and"]:
                        if local_pos in u_shape:
                            color = (0, 120, 0) if not cell["powered"] else (0, 255, 0)
                            pygame.draw.rect(screen, color, rect)
                            label_text = ""
                            if local_pos in input_offsets:
                                label_text = "IN"
                            elif local_pos == output_offset:
                                label_text = "OUT"
                        


    if placement_mode == "select" and lasso_start and lasso_end:
        x1, y1 = lasso_start
        x2, y2 = lasso_end
        grid_x1 = round((x1 * GRID_SIZE - camera_x) * zoom)
        grid_y1 = round((y1 * GRID_SIZE - camera_y) * zoom)
        grid_x2 = round((x2 * GRID_SIZE - camera_x) * zoom)
        grid_y2 = round((y2 * GRID_SIZE - camera_y) * zoom)
        rect = pygame.Rect(min(grid_x1, grid_x2), min(grid_y1, grid_y2),
                           abs(grid_x2 - grid_x1) + GRID_SIZE, abs(grid_y2 - grid_y1) + GRID_SIZE)
        pygame.draw.rect(screen, (100, 200, 255), rect, 2)
    


    if placement_mode in ["redstone", "power", "or", "and", "not", "xor", "nor", "nand"]:
        mouse_x, mouse_y = pygame.mouse.get_pos()
        grid_x = int((mouse_x / zoom + camera_x) // GRID_SIZE)
        grid_y = int((mouse_y / zoom + camera_y) // GRID_SIZE)
        if 0 <= grid_x < grid_width and 0 <= grid_y < grid_height:
            if placement_mode in ["redstone", "power"]:
                rect = pygame.Rect(
                    round((grid_x * GRID_SIZE - camera_x) * zoom),
                    round((grid_y * GRID_SIZE - camera_y) * zoom),
                    round(GRID_SIZE * zoom),
                    round(GRID_SIZE * zoom)
                )
                pygame.draw.rect(screen, (255, 248, 189), rect, 3) 
            else:

                typeOfGate = f"{rotation}-{placement_mode}"
                gate_def = GATE_DEFINITIONS.get(typeOfGate)
                if gate_def:
                    w, h = gate_def["size"]
                    input_offsets = gate_def["inputs"]
                    output_offset = gate_def["output"]

                    for dx, dy in input_offsets:
                        gx = grid_x + dx
                        gy = grid_y + dy
                        if 0 <= gx < grid_width and 0 <= gy < grid_height:
                            rect = pygame.Rect(
                                round((gx * GRID_SIZE - camera_x) * zoom),
                                round((gy * GRID_SIZE - camera_y) * zoom),
                                round(GRID_SIZE * zoom),
                                round(GRID_SIZE * zoom)
                            )
                            pygame.draw.rect(screen, (0, 255, 0), rect, 3) 

                    out_gx = grid_x + output_offset[0]
                    out_gy = grid_y + output_offset[1]
                    if 0 <= out_gx < grid_width and 0 <= out_gy < grid_height:
                        rect = pygame.Rect(
                            round((out_gx * GRID_SIZE - camera_x) * zoom),
                            round((out_gy * GRID_SIZE - camera_y) * zoom),
                            round(GRID_SIZE * zoom),
                            round(GRID_SIZE * zoom)
                        )
                        pygame.draw.rect(screen, (255, 200, 0), rect, 3)  


    popup_button_defs = []
    if selected_cells:
        xs = [x for x, y in selected_cells]
        ys = [y for x, y in selected_cells]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        popup_x = round((max_x * GRID_SIZE - camera_x) * zoom) + 10
        popup_y = round((min_y * GRID_SIZE - camera_y) * zoom) - 40
        button_w, button_h = 60, 30

        popup_button_defs = [
            ("copy", pygame.Rect(popup_x, popup_y, button_w, button_h), "Copy", (100, 200, 100)),
            ("delete", pygame.Rect(popup_x + button_w + 10, popup_y, button_w, button_h), "Delete", (200, 80, 80)),
            ("paste", pygame.Rect(popup_x + 2 * (button_w + 10), popup_y, button_w, button_h), "Paste", (80, 180, 255) if clipboard else (120, 120, 120)),
        ]

        # Track scale for popup buttons
        if not hasattr(draw_grid, "popup_button_scales"):
            draw_grid.popup_button_scales = {name: 1.0 for name, *_ in popup_button_defs}
        popup_scales = draw_grid.popup_button_scales

        mouse_pos = pygame.mouse.get_pos()
        popup_scale_speed = 0.18
        popup_target_scale = 1.13

        for name, rect, label, base_color in popup_button_defs:
            is_hover = rect.collidepoint(mouse_pos)
            target = popup_target_scale if is_hover else 1.0
            popup_scales[name] += (target - popup_scales[name]) * popup_scale_speed
            scale = popup_scales[name]
            center = rect.center
            scaled_w = int(rect.width * scale)
            scaled_h = int(rect.height * scale)
            draw_rect = pygame.Rect(0, 0, scaled_w, scaled_h)
            draw_rect.center = center

            pastel = tuple(min(255, int(c * 0.6 + 255 * 0.4)) for c in base_color)
            draw_color = pastel if is_hover else (0, 0, 0)

            if is_hover:
                glow_surface = pygame.Surface((draw_rect.width, draw_rect.height), pygame.SRCALPHA)
                glow_center = (draw_rect.width // 2, draw_rect.height // 2)
                max_radius = int(min(draw_rect.width, draw_rect.height) * 0.95)
                for i in range(10, 0, -1):
                    alpha = int(80 * (i / 10))
                    radius = int(max_radius * (i / 10))
                    pygame.draw.circle(
                        glow_surface,
                        (*base_color, alpha),
                        glow_center,
                        radius
                    )
                screen.blit(glow_surface, draw_rect.topleft)

            pygame.draw.rect(screen, draw_color, draw_rect, border_radius=8)
            font_size = 22 if len(label) > 5 else 26
            btn_font = pygame.font.Font(None, font_size)
            text_surf = btn_font.render(label, True, (255, 255, 255))
            text_rect = text_surf.get_rect(center=draw_rect.center)
            screen.blit(text_surf, text_rect)

        copy_button_rect = popup_button_defs[0][1]
        delete_button_rect_popup = popup_button_defs[1][1]
        paste_button_rect = popup_button_defs[2][1]
    else:
        if hasattr(draw_grid, "popup_button_scales"):
            draw_grid.popup_button_scales = {name: 1.0 for name, *_ in [
                ("copy", None, None, None),
                ("delete", None, None, None),
                ("paste", None, None, None),
            ]}

    for (x, y) in selected_cells:
        grid_x = round((x * GRID_SIZE - camera_x) * zoom)
        grid_y = round((y * GRID_SIZE - camera_y) * zoom)
        size = round(GRID_SIZE * zoom)
        pygame.draw.rect(screen, (255, 255, 0), (grid_x, grid_y, size, size), 3)

    draw_hamburger_icon()
    draw_cell_inspector()

    menu_width = 120
    slide_offset = int(menu_width * (1 - item_menu_anim))
    item_menu_rect_slid = item_menu_rect.move(slide_offset, 0)
    pygame.draw.rect(screen, (60, 60, 60), item_menu_rect_slid)

    GATE_COLORS = {
        "redstone": (255, 0, 0),
        "power": (255, 255, 0),
        "bridge": (120, 120, 255),
        "or": (255, 130, 0),
        "and": (0, 255, 0),
        "not": (30, 30, 180),
        "xor": (0, 255, 255),
        "nor": (255, 80, 120),
        "nand": (200, 0, 255),
        "delete": (255, 80, 80),
        "select": (100, 200, 255),
        "clock": (0, 200, 200),
    }

    button_defs = [
        ("redstone", redstone_button_rect, "Redstone"),
        ("bridge", bridge_button_rect, "Bridge"),
        ("power", power_button_rect, "Power"),
        ("or", or_button_rect, "OR"),
        ("and", and_button_rect, "AND"),
        ("not", not_button_rect, "NOT"),
        ("xor", xor_button_rect, "XOR"),
        ("nor", nor_button_rect, "NOR"),
        ("nand", nand_button_rect, "NAND"),
        ("select", lasso_button_rect, "Lasso"),
        ("delete", delete_button_rect, "Delete"),
        ("clock", clock_button_rect, "Clock"),
        
    ]

    mouse_pos = pygame.mouse.get_pos()
    scale_speed = 0.18 
    target_scale = 1.15

    for mode, rect, label in button_defs:
        is_hover = rect.move(slide_offset, 0).collidepoint(mouse_pos)
        is_active = (
            (mode == "redstone" and placement_mode == "redstone") or
            (mode == "bridge" and placement_mode == "bridge") or
            (mode == "power" and placement_mode == "power") or
            (mode == "or" and placement_mode == "or") or
            (mode == "and" and placement_mode == "and") or
            (mode == "not" and placement_mode == "not") or
            (mode == "xor" and placement_mode == "xor") or
            (mode == "nor" and placement_mode == "nor") or
            (mode == "nand" and placement_mode == "nand") or
            (mode == "delete" and placement_mode == "delete") or
            (mode == "select" and placement_mode == "select") or
            (mode == "clock" and placement_mode == "clock")
        )

        target = target_scale if (is_hover or is_active) else 1.0
        button_scales[mode] += (target - button_scales[mode]) * scale_speed

        scale = button_scales[mode]
        center = rect.move(slide_offset, 0).center
        scaled_w = int(rect.width * scale)
        scaled_h = int(rect.height * scale)
        draw_rect = pygame.Rect(0, 0, scaled_w, scaled_h)
        draw_rect.center = center

        base_color = GATE_COLORS.get(mode, (255, 255, 255))
        pastel = tuple(min(255, int(c * 0.6 + 255 * 0.4)) for c in base_color)
        draw_color = pastel if (is_hover or is_active) else (0, 0, 0)

        if is_hover or is_active:
            glow_surface = pygame.Surface((draw_rect.width, draw_rect.height), pygame.SRCALPHA)
            glow_center = (draw_rect.width // 2, draw_rect.height // 2)
            max_radius = int(min(draw_rect.width, draw_rect.height) * 0.95)  # Make glow larger
            for i in range(10, 0, -1):
                alpha = int(80 * (i / 10)) 
                radius = int(max_radius * (i / 10))
                pygame.draw.circle(
                    glow_surface,
                    (*base_color, alpha),
                    glow_center,
                    radius
                )
            screen.blit(glow_surface, draw_rect.topleft)

        pygame.draw.rect(screen, draw_color, draw_rect, border_radius=8)
        font_size = 24 if len(label) > 8 else 28
        btn_font = pygame.font.Font(None, font_size)
        text_surf = btn_font.render(label, True, (255, 255, 255))
        text_rect = text_surf.get_rect(center=draw_rect.center)
        screen.blit(text_surf, text_rect)


    if menu_open:
        pygame.draw.rect(screen, (50, 50, 50), side_menu_rect)

        mouse_pos = pygame.mouse.get_pos()
        if not hasattr(draw_grid, "exit_button_scale"):
            draw_grid.exit_button_scale = 1.0
        scale_speed = 0.18
        target_scale = 1.13
        is_hover = exit_button_rect.collidepoint(mouse_pos)
        target = target_scale if is_hover else 1.0
        draw_grid.exit_button_scale += (target - draw_grid.exit_button_scale) * scale_speed


        scale = draw_grid.exit_button_scale
        center = exit_button_rect.center
        scaled_w = int(exit_button_rect.width * scale)
        scaled_h = int(exit_button_rect.height * scale)
        draw_rect = pygame.Rect(0, 0, scaled_w, scaled_h)
        draw_rect.center = center


        base_color = (200, 80, 80)
        pastel = tuple(min(255, int(c * 0.6 + 255 * 0.4)) for c in base_color)
        draw_color = pastel if is_hover else (50, 50, 50)


        if is_hover:
            glow_surface = pygame.Surface((draw_rect.width, draw_rect.height), pygame.SRCALPHA)
            glow_center = (draw_rect.width // 2, draw_rect.height // 2)
            max_radius = int(min(draw_rect.width, draw_rect.height) * 0.95)
            for i in range(10, 0, -1):
                alpha = int(80 * (i / 10))
                radius = int(max_radius * (i / 10))
                pygame.draw.circle(
                    glow_surface,
                    (*base_color, alpha),
                    glow_center,
                    radius
                )
            screen.blit(glow_surface, draw_rect.topleft)

        pygame.draw.rect(screen, draw_color, draw_rect, border_radius=8)
        font_size = 28
        btn_font = pygame.font.Font(None, font_size)
        text_surf = btn_font.render("Exit", True, (255, 255, 255))
        text_rect = text_surf.get_rect(center=draw_rect.center)
        screen.blit(text_surf, text_rect)

        pygame.draw.rect(screen, draw_color, draw_rect, border_radius=8)
        font_size = 28
        btn_font = pygame.font.Font(None, font_size)
        text_surf = btn_font.render("Exit", True, (255, 255, 255))
        text_rect = text_surf.get_rect(center=draw_rect.center)
        screen.blit(text_surf, text_rect)

        if not hasattr(draw_grid, "save_button_scale"):
            draw_grid.save_button_scale = 1.0
        save_is_hover = save_component_button_rect.collidepoint(mouse_pos)
        save_target = target_scale if save_is_hover else 1.0
        draw_grid.save_button_scale += (save_target - draw_grid.save_button_scale) * scale_speed

        save_scale = draw_grid.save_button_scale
        save_center = save_component_button_rect.center
        save_scaled_w = int(save_component_button_rect.width * save_scale)
        save_scaled_h = int(save_component_button_rect.height * save_scale)
        save_draw_rect = pygame.Rect(0, 0, save_scaled_w, save_scaled_h)
        save_draw_rect.center = save_center

        save_base_color = (80, 180, 255)
        save_pastel = tuple(min(255, int(c * 0.6 + 255 * 0.4)) for c in save_base_color)
        save_draw_color = save_pastel if save_is_hover else (50, 50, 50)

        if save_is_hover:
            glow_surface = pygame.Surface((save_draw_rect.width, save_draw_rect.height), pygame.SRCALPHA)
            glow_center = (save_draw_rect.width // 2, save_draw_rect.height // 2)
            max_radius = int(min(save_draw_rect.width, save_draw_rect.height) * 0.95)
            for i in range(10, 0, -1):
                alpha = int(80 * (i / 10))
                radius = int(max_radius * (i / 10))
                pygame.draw.circle(
                    glow_surface,
                    (*save_base_color, alpha),
                    glow_center,
                    radius
                )
            screen.blit(glow_surface, save_draw_rect.topleft)

        pygame.draw.rect(screen, save_draw_color, save_draw_rect, border_radius=8)
        save_font = pygame.font.Font(None, 28)
        save_text = save_font.render("Save Component", True, (255, 255, 255))
        save_text_rect = save_text.get_rect(center=save_draw_rect.center)
        screen.blit(save_text, save_text_rect)

def draw_components_list(components, selected_index):
    global component_delete_rects
    screen.fill((30, 30, 30))
    y = 100
    back_font = pygame.font.Font(None, 32)
    back_text = back_font.render("Back", True, (255, 255, 255))
    back_rect = pygame.Rect(20, 20, 80, 40)
    pygame.draw.rect(screen, (80, 80, 80), back_rect, border_radius=8)
    screen.blit(back_text, back_rect.move(10, 5))
    component_delete_rects = []
    for i, comp in enumerate(components):
        color = (255, 255, 0) if i == selected_index else (200, 200, 200)
        surf = font.render(comp["name"], True, color)
        screen.blit(surf, (100, y))
        del_rect = pygame.Rect(350, y, 80, 32)
        pygame.draw.rect(screen, (200, 80, 80), del_rect, border_radius=8)
        del_font = pygame.font.Font(None, 28)
        del_text = del_font.render("Delete", True, (255, 255, 255))
        del_text_rect = del_text.get_rect(center=del_rect.center)
        screen.blit(del_text, del_text_rect)
        component_delete_rects.append(del_rect)
        y += 40
    if components:
        preview = font.render("Click to edit", True, (180, 180, 255))
        screen.blit(preview, (400, 80))

def load_component_to_grid(component, index=None):
    global grid, grid_width, grid_height, editing_component_index
    comp_w, comp_h = component["width"], component["height"]
    comp_grid = component["grid"]
    grid_width, grid_height = comp_w, comp_h
    grid = [[cell.copy() for cell in row] for row in comp_grid]
    editing_component_index = index



def draw_naming_prompt(input_text):
    screen.fill((30, 30, 30))
    prompt_font = pygame.font.Font(None, 40)
    prompt = prompt_font.render("Enter component name:", True, (255, 255, 255))
    screen.blit(prompt, (WIDTH//2 - prompt.get_width()//2, HEIGHT//2 - 80))
    box = pygame.Rect(WIDTH//2 - 150, HEIGHT//2 - 20, 300, 50)
    pygame.draw.rect(screen, (80, 80, 80), box, border_radius=8)
    input_font = pygame.font.Font(None, 36)
    input_surf = input_font.render(input_text, True, (0, 255, 0))
    screen.blit(input_surf, (box.x + 10, box.y + 10))
    save_rect = pygame.Rect(WIDTH//2 - 60, HEIGHT//2 + 50, 120, 40)
    pygame.draw.rect(screen, (0, 200, 0), save_rect, border_radius=8)
    save_text = input_font.render("Save", True, (255, 255, 255))
    screen.blit(save_text, save_rect.move(20, 5))
    return save_rect


running = True
while running:
    if state == MENU:
        draw_menu()
    elif state == VIEW_COMPONENTS:
        draw_components_list(components_list, selected_component_index)
    elif state == NAMING_COMPONENT:
        save_rect = draw_naming_prompt(component_name_input)
    else:
        draw_grid()
    mouse_x, _ = pygame.mouse.get_pos()
    show_menu = mouse_x > WIDTH - 180
    target_anim = 1.0 if show_menu else 0.0
    item_menu_anim += (target_anim - item_menu_anim) * 0.3

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.KEYDOWN:
            if state == NAMING_COMPONENT:
                if event.key == pygame.K_RETURN:
                    if component_name_input.strip():
                        save_component(selected_cells, grid, component_name_input.strip())
                        state = BUILD_MODE
                elif event.key == pygame.K_BACKSPACE:
                    component_name_input = component_name_input[:-1]
                else:
                    if len(component_name_input) < 20 and event.unicode.isprintable():
                        component_name_input += event.unicode
            elif placement_mode == "clock":
                if event.key == pygame.K_UP:
                    grid[y][x]["frequency"] = max(1, grid[y][x]["frequency"] - 1) 
                elif event.key == pygame.K_DOWN:
                    grid[y][x]["frequency"] += 1

            if event.key == pygame.K_r:
                rotation = rotation + 1 if rotation < 3 else 0

        elif event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos

            if state == NAMING_COMPONENT:
                save_rect = draw_naming_prompt(component_name_input)
                if save_rect.collidepoint(mx, my):
                    if component_name_input.strip():
                        save_component(selected_cells, grid, component_name_input.strip())
                        state = BUILD_MODE

            elif selected_cells:
                if copy_button_rect and copy_button_rect.collidepoint(mx, my):
                    clipboard.clear()
                    xs = [x for x, y in selected_cells]
                    ys = [y for x, y in selected_cells]
                    min_x, min_y = min(xs), min(ys)
                    for (x, y) in selected_cells:
                        cell = grid[y][x].copy()
                        clipboard.append((x - min_x, y - min_y, cell))
                    print("Copied selection!")
                    continue
                elif delete_button_rect_popup and delete_button_rect_popup.collidepoint(mx, my):
                    for (x, y) in selected_cells:
                        grid[y][x] = {"type": "empty", "powered": False}
                    selected_cells.clear()
                    print("Deleted selection!")
                    continue
                elif paste_button_rect and paste_button_rect.collidepoint(mx, my) and clipboard:
                    xs = [x for x, y in selected_cells]
                    ys = [y for x, y in selected_cells]
                    base_x, base_y = min(xs), min(ys)
                    for dx, dy, cell in clipboard:
                        gx, gy = base_x + dx, base_y + dy
                        if 0 <= gx < grid_width and 0 <= gy < grid_height:
                            grid[gy][gx] = cell.copy()
                    print("Pasted selection!")
                    continue

            if state == MENU:
                if 250 <= my <= 300:
                    grid_width = 100
                    grid_height = 100
                    grid = [[{"type": "empty", "powered": False} for _ in range(grid_width)] for _ in range(grid_height)]
                    selected_cells.clear()
                    lasso_start = None
                    lasso_end = None
                    state = BUILD_MODE
                elif 320 <= my <= 370:
                    state = VIEW_COMPONENTS
                    components_list = load_components()
                    selected_component_index = 0
                elif 390 <= my <= 440:
                    running = False
            elif state == BUILD_MODE:
                if menu_button_rect.collidepoint(mx, my):
                    menu_open = not menu_open
                if redstone_button_rect.collidepoint(mx, my):
                    placement_mode = "redstone"
                    clear_lasso_selection()
                    continue
                elif bridge_button_rect.collidepoint(mx, my):
                    placement_mode = "bridge"
                    clear_lasso_selection()
                    continue
                elif power_button_rect.collidepoint(mx, my):
                    placement_mode = "power"
                    clear_lasso_selection()
                    continue
                if or_button_rect.collidepoint(mx, my):
                    placement_mode = "or"
                    clear_lasso_selection()
                    continue
                elif and_button_rect.collidepoint(mx, my):
                    placement_mode = "and"
                    clear_lasso_selection()
                    continue
                elif not_button_rect.collidepoint(mx, my):
                    placement_mode = "not"
                    clear_lasso_selection()
                    continue
                elif xor_button_rect.collidepoint(mx, my):
                    placement_mode = "xor"
                    clear_lasso_selection()
                    continue
                elif nor_button_rect.collidepoint(mx, my):
                    placement_mode = "nor"
                    clear_lasso_selection()
                    continue
                elif nand_button_rect.collidepoint(mx, my):
                    placement_mode = "nand"
                    clear_lasso_selection()
                    continue
                elif lasso_button_rect.collidepoint(mx, my):
                    placement_mode = "select"
                elif delete_button_rect.collidepoint(mx, my):
                    placement_mode = "delete"
                    clear_lasso_selection()
                    continue
                elif clock_button_rect.collidepoint(mx, my):
                    placement_mode = "clock"
                    clear_lasso_selection()
                    continue 

                elif menu_open and exit_button_rect.collidepoint(mx, my):
                    state = MENU
                    menu_open = False

                elif menu_open and save_component_button_rect.collidepoint(mx, my):
                    state = NAMING_COMPONENT
                    component_name_input = ""


                if placement_mode == "select" and event.button == 1:
                    lasso_start = (int((mx / zoom + camera_x) // GRID_SIZE),
                                   int((my / zoom + camera_y) // GRID_SIZE))
                    lasso_end = lasso_start


                elif event.button == 1:
                    x = int((mx / zoom + camera_x) // GRID_SIZE)
                    y = int((my / zoom + camera_y) // GRID_SIZE)
                    if 0 <= x < grid_width and 0 <= y < grid_height:
                        if placement_mode == "redstone":
                            grid[y][x] = {"type": "redstone", "powered": False}
                        elif placement_mode == "bridge":
                            grid[y][x] = {"type": "bridge", "powered": False}
                        elif placement_mode == "power":
                            grid[y][x] = {"type": "power", "powered": True}
                        elif placement_mode == "or":
                            place_gate(x, y, "or", rotation)
                        elif placement_mode == "and":
                            place_gate(x, y, "and", rotation)
                        elif placement_mode == "not":
                            place_gate(x, y, "not", rotation)
                        elif placement_mode == "xor":
                            place_gate(x, y, "xor", rotation)
                        elif placement_mode == "nor":
                            place_gate(x, y, "nor", rotation)
                        elif placement_mode == "nand":
                            place_gate(x, y, "nand", rotation)
                        elif placement_mode == "clock":
                            frequency = 30
                            grid[y][x] = {"type": "clock", "powered": False, "frequency": frequency, "timer": 0}
                        elif placement_mode == "delete":
                            cell = grid[y][x]
                            if cell["type"] == "gate":
                                gate_type = cell["gate_type"]
                                local_pos = cell["local_pos"]
                                gate_def = GATE_DEFINITIONS[gate_type]
                                w, h = gate_def["size"]
                                origin_x = x - local_pos[0]
                                origin_y = y - local_pos[1]
                                for dy in range(h):
                                    for dx in range(w):
                                        gx = origin_x + dx
                                        gy = origin_y + dy
                                        if 0 <= gx < grid_width and 0 <= gy < grid_height:
                                            if grid[gy][gx].get("type") == "gate" and grid[gy][gx].get("gate_type") == gate_type:
                                                grid[gy][gx] = {"type": "empty", "powered": False}
                            else:
                                grid[y][x] = {"type": "empty", "powered": False}

                elif event.button == 3:
                    panning = True
                    last_mouse_x, last_mouse_y = event.pos
                elif event.button == 4:
                    target_zoom *= 1.1
                elif event.button == 5:
                    target_zoom /= 1.1

            elif state == VIEW_COMPONENTS:
                if 20 <= mx <= 100 and 20 <= my <= 60:
                    state = MENU
                else:

                    for idx, del_rect in enumerate(component_delete_rects):
                        if del_rect.collidepoint(mx, my):

                            components = load_components()
                            if 0 <= idx < len(components):
                                del components[idx]
                                with open(COMPONENTS_FILE, "w") as f:
                                    json.dump(components, f)
                                components_list = load_components()
                                selected_component_index = 0
                            break
                    else:
                        idx = (my - 100) // 40
                        if 0 <= idx < len(components_list):
                            load_component_to_grid(components_list[idx])
                            state = BUILD_MODE

        elif event.type == pygame.MOUSEMOTION:
            if placement_mode == "select" and lasso_start:
                lasso_end = (int((event.pos[0] / zoom + camera_x) // GRID_SIZE),
                             int((event.pos[1] / zoom + camera_y) // GRID_SIZE))
            elif panning:
                dx = event.pos[0] - last_mouse_x
                dy = event.pos[1] - last_mouse_y
                target_camera_x -= dx / zoom
                target_camera_y -= dy / zoom
                last_mouse_x, last_mouse_y = event.pos

        elif event.type == pygame.MOUSEBUTTONUP:
            if placement_mode == "select" and event.button == 1 and lasso_start:
                x1, y1 = lasso_start
                x2, y2 = lasso_end
                x_min, x_max = sorted([x1, x2])
                y_min, y_max = sorted([y1, y2])
                selected_cells.clear()
                for y in range(y_min, y_max + 1):
                    for x in range(x_min, x_max + 1):
                        if 0 <= x < grid_width and 0 <= y < grid_height:
                            selected_cells.add((x, y))
                lasso_start = lasso_end = None
            elif event.button == 3:
                panning = False
                

    

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
