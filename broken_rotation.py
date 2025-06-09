import pygame
import math  # Needed for the X animation
import os
import json
import tkinter as tk
from tkinter import simpledialog

# Setup Pygame
pygame.init()
WIDTH, HEIGHT = 800, 600
GRID_SIZE = 20
GRID_COLOR = (100, 100, 100, 150)
REDSTONE_BASE = (255, 50, 50)


MENU, BUILD_MODE, COMPONENT_LIST, COMPONENT_EDIT = "menu", "build", "component_list", "component_edit"
current_edit_component_name = None

screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()
font = pygame.font.Font(None, 36)  # Font for text rendering

# Menu state
MENU, BUILD_MODE = "menu", "build"
state = MENU  # Start in the main menu
menu_open = False  # Tracks whether the side menu is visible


components_dir = "components"
if not os.path.exists(components_dir):
    os.makedirs(components_dir)
loaded_components = []  # List of loaded component dicts
show_component_menu = False
component_menu_rects = []



# Camera controls
camera_x, camera_y = 0, 0
target_camera_x, target_camera_y = camera_x, camera_y
move_speed = 0.15  
zoom = 1.0
target_zoom = zoom
zoom_speed = 0.3 
current_gate_rotation = 0  # 0=up, 1=right, 2=down, 3=left

panning = False
last_mouse_x, last_mouse_y = 0, 0

# Grid system (big space)
grid_width = 100  
grid_height = 100
grid = [[{"type": "empty", "powered": False,} for _ in range(grid_width)] for _ in range(grid_height)]
placement_mode = "redstone"  # or "power"
lasso_start = None
lasso_end = None
selected_cells = set()


# Button positions
menu_button_rect = pygame.Rect(10, 10, 40, 40)  # Three-line menu button
side_menu_rect = pygame.Rect(0, 0, 200, HEIGHT)  # Side menu (hidden until clicked)
exit_button_rect = pygame.Rect(20, 60, 160, 40)  # Exit button inside side menu
item_menu_rect = pygame.Rect(WIDTH - 120, 10, 110, 100)
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
load_component_button_rect = pygame.Rect(WIDTH - 110, 420, 90, 30)




clipboard = []

# Hamburger icon animation variables
menu_icon_hover = False
menu_icon_animation = 0.0  # For smooth transitions

def lerp(a, b, t):
    return a + (b - a) * t  # Linear interpolation


def draw_component_list():
    screen.fill((30, 30, 30))
    load_all_components()
    title = font.render("Saved Components", True, (255, 255, 0))
    screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 40))
    global component_menu_rects
    component_menu_rects = []
    for i, comp in enumerate(loaded_components):
        rect = pygame.Rect(WIDTH // 2 - 150, 100 + i * 50, 300, 40)
        component_menu_rects.append((rect, comp))
        pygame.draw.rect(screen, (200, 200, 100), rect)
        name_surf = font.render(comp["name"], True, (0, 0, 0))
        screen.blit(name_surf, (rect.x + 10, rect.y + 5))
    # Back button
    back_rect = pygame.Rect(20, HEIGHT - 60, 120, 40)
    pygame.draw.rect(screen, (180, 50, 50), back_rect)
    screen.blit(font.render("Back", True, (255, 255, 255)), (back_rect.x + 20, back_rect.y + 5))
    return back_rect

def load_component_to_grid(component):
    """
    Loads a component (dict loaded from JSON) onto the grid at (0, 0).
    Ensures gate local_pos is always a tuple for logic compatibility.
    """
    # Clear grid
    for y in range(grid_height):
        for x in range(grid_width):
            grid[y][x] = {"type": "empty", "powered": False}
    # Place component at (0,0)
    for cell_info in component["cells"]:
        gx = cell_info["dx"]
        gy = cell_info["dy"]
        if 0 <= gx < grid_width and 0 <= gy < grid_height:
            cell = cell_info["cell"].copy()
            # Convert local_pos to tuple for gates
            if cell.get("type") == "gate" and isinstance(cell.get("local_pos"), list):
                cell["local_pos"] = tuple(cell["local_pos"])
            grid[gy][gx] = cell

# Add these at the top with other initializations
hover_states = {0: False, 1: False, 2: False}
text_scales = [1.0, 1.0, 1.0]
TARGET_SCALE = 1.15  # Slightly more subtle
SCALE_SPEED = 0.2    # Faster but still smooth
GATE_DEFINITIONS = {
    "or": {
        "size": (3, 2),
        "inputs": [(0, 0), (2, 0)],
        "output": (1, 1),
        "logic": "or"
    },
    "and": {
        "size": (3, 2),
        "inputs": [(0, 0), (2, 0)],
        "output": (1, 1),
        "logic": "and"
    },
    "not": {
        "size": (1, 2),
        "inputs": [(0, 0)],
        "output": (0, 1),
        "logic": "not"
    },
    "xor": {
        "size": (3, 2),
        "inputs": [(0, 0), (2, 0)],
        "output": (1, 1),
        "logic": "xor"
    },
    "nor": {
        "size": (3, 2),
        "inputs": [(0, 0), (2, 0)],
        "output": (1, 1),
        "logic": "nor"
    },
    "nand": {
        "size": (3, 2),
        "inputs": [(0, 0), (2, 0)],
        "output": (1, 1),
        "logic": "nand"
    },
}

# Pre-render font surfaces at different sizes to avoid creating new ones each frame
font_cache = {}
def get_font(size):
    if size not in font_cache:
        font_cache[size] = pygame.font.Font(None, size)
    return font_cache[size]

# Pre-calculate glow colors
gold_base = (253, 255, 150)
gold_light = (253, 255, 117)
glow_colors = [(*gold_light, alpha) for alpha in range(50, 0, -10)]


def place_gate(x, y, gate_type, rotation=0):
    definition = GATE_DEFINITIONS[gate_type]
    w, h = definition["size"]

    # Check if space is available
    for dy in range(h):
        for dx in range(w):
            rx, ry = rotate_offset(dx, dy, rotation, w, h)
            gx = x + rx
            gy = y + ry
            if not (0 <= gx < grid_width and 0 <= gy < grid_height):
                return  # Out of bounds
            if grid[gy][gx]["type"] != "empty":
                return  # Already occupied

    for dy in range(h):
        for dx in range(w):
            rx, ry = rotate_offset(dx, dy, rotation, w, h)
            gx = x + rx
            gy = y + ry
            grid[gy][gx] = {
            "type": "gate",
            "gate_type": gate_type,
            "local_pos": (dx, dy),  # unrotated local position (CORRECT)
            "powered": False,
            "rotation": rotation
        }

def save_selected_as_component(name):
    print("Selected cells:", selected_cells)
    for (x, y) in selected_cells:
        print(f"({x},{y}):", grid[y][x])
    path = os.path.join(components_dir, f"{name}.json")
    if os.path.exists(path):
        print(f"Component '{name}' already exists!")
        return
    xs = [x for x, y in selected_cells]
    ys = [y for x, y in selected_cells]
    min_x, min_y = min(xs), min(ys)
    width = max(xs) - min_x + 1
    height = max(ys) - min_y + 1
    cells = []
    seen = set()

    # Save all selected cells, including all gate tiles
    for (x, y) in selected_cells:
        cell = grid[y][x]
        if (x, y) not in seen and cell["type"] != "empty":
            cells.append({"dx": x - min_x, "dy": y - min_y, "cell": cell.copy()})
            seen.add((x, y))

    component = {
        "name": name,
        "width": width,
        "height": height,
        "cells": cells
    }
    with open(path, "w") as f:
        json.dump(component, f)


def draw_menu():
    screen.fill((30, 30, 30))
    mouse_pos = pygame.mouse.get_pos()
    menu_items = [
        ("Make New Component", 250),
        ("View Components", 320),
        ("Exit", 390)
    ]
    
    # Pre-calculate time-based factor for consistent animation speed
    dt = clock.get_time() / 16.67  # Normalized to 60 FPS
    
    for i, (text, y) in enumerate(menu_items):
        # Update hover state
        btn_rect = pygame.Rect(250, y - 10, 300, 60)
        hover_states[i] = btn_rect.collidepoint(mouse_pos)
        
        # Animate scale with time-adjusted speed
        target_scale = TARGET_SCALE if hover_states[i] else 1.0
        text_scales[i] += (target_scale - text_scales[i]) * SCALE_SPEED * dt
        
        # Calculate current font size (rounded to nearest even number)
        current_size = max(24, min(48, int(36 * text_scales[i])))
        current_size = current_size + (current_size % 2)  # Keep sizes even for cleaner rendering
        
        # Get cached font
        current_font = get_font(current_size)
        
        # Main text surface (cached if possible)
        text_surf = current_font.render(text, True, gold_base)
        text_rect = text_surf.get_rect(center=(400, y + 25))
        
        # Optimized glow effect - only 3 layers instead of 5
        for alpha_color in glow_colors[:3]:
            # Create once and reuse
            glow_surf = current_font.render(text, True, alpha_color)
            screen.blit(glow_surf, glow_surf.get_rect(center=(400, y + 25)))
        
        # Draw main text
        screen.blit(text_surf, text_rect)
        
        # Dynamic underline (only when nearly hovered)
        if text_scales[i] > 1.05:
            underline_length = int(text_rect.width * min(1.0, (text_scales[i] - 1.0) / (TARGET_SCALE - 1.0)))
            pygame.draw.line(
                screen, gold_light,
                (400 - underline_length//2, text_rect.bottom + 2),
                (400 + underline_length//2, text_rect.bottom + 2),
                2
            )

GATE_COLORS = {
    "or": (255, 140, 0),      # Orange
    "and": (0, 200, 0),       # Green
    "not": (200, 0, 200),     # Purple
    "xor": (0, 200, 200),     # Cyan
    "nor": (120, 0, 255),     # Violet
    "nand": (255, 0, 120),    # Pink
}
# Define colors using RGB values
GREEN = (0, 255, 0)   # RGB for green
GRAY = (169, 169, 169)  # RGB for gray
BLUE = (0, 0, 255)    # RGB for blue
# Define colors using RGB values
YELLOW = (255, 255, 0)  # RGB for yellow
WHITE = (255, 255, 255)  # RGB for white

def load_all_components():
    global loaded_components
    loaded_components = []
    for fname in os.listdir(components_dir):
        if fname.endswith(".json"):
            with open(os.path.join(components_dir, fname)) as f:
                loaded_components.append(json.load(f))

def place_component(component, base_x, base_y):
    """
    Places a component (dict loaded from JSON) onto the grid at the specified base_x, base_y.
    Ensures gate local_pos is always a tuple for logic compatibility.
    The gate's origin (local_pos == (0, 0) or [0, 0]) will be placed at (base_x, base_y).
    """
    # Find the offset needed to place the origin tile at (base_x, base_y)
    origin_dx, origin_dy = 0, 0
    for cell_info in component["cells"]:
        cell = cell_info["cell"]
        # Accept both tuple and list for local_pos
        lp = cell.get("local_pos")
        if cell.get("type") == "gate" and (lp == (0, 0) or lp == [0, 0]):
            origin_dx = cell_info["dx"]
            origin_dy = cell_info["dy"]
            break
    # Offset all cells so the gate origin lands at (base_x, base_y)
    for cell_info in component["cells"]:
        gx = base_x + (cell_info["dx"] - origin_dx)
        gy = base_y + (cell_info["dy"] - origin_dy)
        if 0 <= gx < grid_width and 0 <= gy < grid_height:
            cell = cell_info["cell"].copy()
            # Convert local_pos to tuple for gates
            if cell.get("type") == "gate" and isinstance(cell.get("local_pos"), list):
                cell["local_pos"] = tuple(cell["local_pos"])
            grid[gy][gx] = cell


def prompt_for_name():
    root = tk.Tk()
    root.withdraw()
    name = simpledialog.askstring("Component Name", "Enter a name for your component:")
    root.destroy()
    return name

def draw_hamburger_icon():
    """Draws animated hamburger menu icon that transforms to X when open"""
    global menu_icon_hover, menu_icon_animation
    
    # Update animation state
    mouse_pos = pygame.mouse.get_pos()
    menu_icon_hover = menu_button_rect.collidepoint(mouse_pos)
    
    # Animate the transition
    target_animation = 1.0 if menu_icon_hover or menu_open else 0.0
    menu_icon_animation = lerp(menu_icon_animation, target_animation, 0.2)
    
    # Position and size parameters
    x, y = 20, 15
    width = 24
    thickness = 3
    spacing = 5
    
    # Color animation
    base_color = (200, 200, 200)
    hover_color = (240, 240, 240)
    current_color = (
        int(lerp(base_color[0], hover_color[0], menu_icon_animation)),
        int(lerp(base_color[1], hover_color[1], menu_icon_animation)),
        int(lerp(base_color[2], hover_color[2], menu_icon_animation))
    )
    
    # Draw either hamburger or X based on menu state
    if not menu_open:
        # Animated hamburger icon
        current_spacing = spacing + (3 * menu_icon_animation)  # Lines spread on hover
        for i in range(3):
            line_y = y + i * (thickness + current_spacing)
            pygame.draw.rect(screen, current_color, (x, line_y, width, thickness))
    else:
        # Animated X icon
        center_x = x + width // 2
        center_y = y + (thickness * 2 + spacing * 2) // 2
        line_length = width * min(1.0, menu_icon_animation * 1.5)
        
        # Draw two rotating lines
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

def rotate_offset(dx, dy, rotation, w, h):
    if rotation == 0:   # Up
        return dx, dy
    elif rotation == 1: # Right
        return dy, w - 1 - dx
    elif rotation == 2: # Down
        return w - 1 - dx, h - 1 - dy
    elif rotation == 3: # Left
        return h - 1 - dy, dx

def propagate_power():
    # Step 1: Reset
    for row in grid:
        for cell in row:
            cell["powered"] = False

    # Step 2: Power propagation from power sources
    for y in range(grid_height):
        for x in range(grid_width):
            if grid[y][x]["type"] == "power":
                propagate_from(x, y)

    # Step 3: Evaluate gates (only from origin tiles)
    for y in range(grid_height):
        for x in range(grid_width):
            cell = grid[y][x]
            if cell["type"] == "gate" and cell["local_pos"] == (0, 0):
                gate_def = GATE_DEFINITIONS[cell["gate_type"]]
                evaluate_gate(x, y, gate_def)


def evaluate_gate(x, y, definition):
    """
    Evaluate a gate's logic starting from its origin tile (local_pos == (0,0))
    x, y should be the coordinates of the gate's origin tile
    """
    rotation = grid[y][x].get("rotation", 0)
    w, h = definition["size"]
    
    # Collect input values
    inputs_powered = []
    for input_dx, input_dy in definition["inputs"]:
        # Rotate the input offset
        rotated_dx, rotated_dy = rotate_offset(input_dx, input_dy, rotation, w, h)
        input_x = x + rotated_dx
        input_y = y + rotated_dy
        
        if 0 <= input_x < grid_width and 0 <= input_y < grid_height:
            inputs_powered.append(grid[input_y][input_x]["powered"])
    
    # Evaluate logic
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
        output_logic = not (all(inputs_powered) and len(inputs_powered) == len(definition["inputs"]))
    
    # Apply power to output
    output_dx, output_dy = definition["output"]
    rotated_output_dx, rotated_output_dy = rotate_offset(output_dx, output_dy, rotation, w, h)
    output_x = x + rotated_output_dx
    output_y = y + rotated_output_dy
    
    if 0 <= output_x < grid_width and 0 <= output_y < grid_height:
        output_cell = grid[output_y][output_x]
        if output_logic and output_cell.get("type") == "gate" and output_cell.get("gate_type") == grid[y][x].get("gate_type"):
            output_cell["powered"] = True
            propagate_from(output_x, output_y)


def inverse_rotate_offset(dx, dy, rotation, w, h):
    """Given a rotated (dx, dy), get the original (unrotated) local_pos."""
    if rotation == 0:   # Up
        return dx, dy
    elif rotation == 1: # Right
        return w - 1 - dy, dx
    elif rotation == 2: # Down
        return w - 1 - dx, h - 1 - dy
    elif rotation == 3: # Left
        return dy, h - 1 - dx
    
def has_powered_input(x, y):
    neighbors = [(x+1, y), (x-1, y), (x, y+1), (x, y-1)]
    for nx, ny in neighbors:
        if 0 <= nx < grid_width and 0 <= ny < grid_height:
            neighbor = grid[ny][nx]
            if neighbor["type"] in ["redstone", "power", "or"] and neighbor["powered"]:
                return True
    return False

def propagate_from(x, y):
    stack = [(x, y)]
    visited = set()

    while stack:
        cx, cy = stack.pop()
        if (cx, cy) in visited:
            continue
        visited.add((cx, cy))

        if 0 <= cx < grid_width and 0 <= cy < grid_height:
            cell = grid[cy][cx]
            if cell["type"] in ["redstone", "power", "or"]:
                if not cell["powered"]:
                    cell["powered"] = True
                    neighbors = [(cx+1, cy), (cx-1, cy), (cx, cy+1), (cx, cy-1)]
                    stack.extend(neighbors)
            elif cell["type"] == "gate":
                gate_type = cell.get("gate_type")
                local_pos = cell.get("local_pos")
                gate_def = GATE_DEFINITIONS.get(gate_type, {})
                rotation = cell.get("rotation", 0)
                w, h = gate_def["size"]
                rotated_inputs = [rotate_offset(dx, dy, rotation, w, h) for dx, dy in gate_def.get("inputs", [])]
                rotated_output = rotate_offset(*gate_def.get("output", (-1, -1)), rotation, w, h)
                rotated_local_pos = inverse_rotate_offset(*local_pos, rotation, w, h)

                if rotated_local_pos in rotated_inputs:
                    if not cell["powered"]:
                        cell["powered"] = True
                if rotated_local_pos == rotated_output:
                    if not cell["powered"]:
                        cell["powered"] = True
                    neighbors = [(cx+1, cy), (cx-1, cy), (cx, cy+1), (cx, cy-1)]
                    stack.extend(neighbors)
def draw_grid():
    propagate_power()  # Recalculate power state

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
                elif cell["type"] == "power":
                    pygame.draw.rect(screen, (255, 255, 0), rect)
                if cell["type"] == "gate":
                    gate_type = cell["gate_type"]
                    gate_def = GATE_DEFINITIONS.get(gate_type, {})
                    local_pos = cell.get("local_pos", (0, 0))
                    rotation = cell.get("rotation", 0)
                    w, h = gate_def["size"]

                    # Calculate U-shape positions for this gate
                    input_offsets = [rotate_offset(dx, dy, rotation, w, h) for dx, dy in gate_def.get("inputs", [])]
                    output_offset = rotate_offset(*gate_def.get("output", (-1, -1)), rotation, w, h)
                    u_shape = set(input_offsets + [output_offset])
                    

                    # Only draw if this tile is part of the U-shape
                    rotated_local_pos = rotate_offset(*local_pos, rotation, w, h)
                    print("Rotated local pos:", rotated_local_pos, "local_pos:", local_pos, "rotation:", rotation)
                    if rotated_local_pos in u_shape:
                        gate_color = GATE_COLORS.get(gate_type, (180, 180, 180))
                        powered_color = tuple(min(255, c + 60) for c in gate_color)
                        color = powered_color if cell["powered"] else gate_color
                        pygame.draw.rect(screen, color, rect)
                        # Optionally, draw a label on the output tile
                        if rotated_local_pos == output_offset:
                            small_font = pygame.font.Font(None, 16)
                            label = small_font.render(gate_type.upper(), True, (0, 0, 0))
                            label_rect = label.get_rect(center=rect.center)
                            screen.blit(label, label_rect)
        

    # --- LASSO RECTANGLE ---
    if placement_mode == "lasso" and lasso_start and lasso_end:
        x1, y1 = lasso_start
        x2, y2 = lasso_end
        grid_x1 = round((x1 * GRID_SIZE - camera_x) * zoom)
        grid_y1 = round((y1 * GRID_SIZE - camera_y) * zoom)
        grid_x2 = round((x2 * GRID_SIZE - camera_x) * zoom)
        grid_y2 = round((y2 * GRID_SIZE - camera_y) * zoom)
        rect = pygame.Rect(min(grid_x1, grid_x2), min(grid_y1, grid_y2),
                           abs(grid_x2 - grid_x1) + GRID_SIZE, abs(grid_y2 - grid_y1) + GRID_SIZE)
        pygame.draw.rect(screen, (100, 200, 255), rect, 2)

    # --- POPUP MENU FOR LASSO SELECTION ---
    global copy_button_rect, delete_button_rect_popup, paste_button_rect, save_component_button_rect, save_changes_rect
    copy_button_rect = None
    delete_button_rect_popup = None
    paste_button_rect = None
    save_component_button_rect = None
    save_changes_rect = None

    if selected_cells:
        xs = [x for x, y in selected_cells]
        ys = [y for x, y in selected_cells]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        popup_x = round((max_x * GRID_SIZE - camera_x) * zoom) + 10
        popup_y = round((min_y * GRID_SIZE - camera_y) * zoom) - 40
        button_w, button_h = 60, 30

        # Copy button
        copy_button_rect = pygame.Rect(popup_x, popup_y, button_w, button_h)
        pygame.draw.rect(screen, (100, 200, 100), copy_button_rect)
        screen.blit(font.render("Copy", True, (255, 255, 255)), (popup_x + 8, popup_y + 5))

        # Delete button
        delete_button_rect_popup = pygame.Rect(popup_x + button_w + 10, popup_y, button_w, button_h)
        pygame.draw.rect(screen, (200, 80, 80), delete_button_rect_popup)
        screen.blit(font.render("Delete", True, (255, 255, 255)), (popup_x + button_w + 18, popup_y + 5))

        # Paste button
        paste_button_rect = pygame.Rect(popup_x + 2 * (button_w + 10), popup_y, button_w, button_h)
        paste_color = (80, 180, 255) if clipboard else (120, 120, 120)
        pygame.draw.rect(screen, paste_color, paste_button_rect)
        screen.blit(font.render("Paste", True, (255, 255, 255)), (popup_x + 2 * (button_w + 10) + 8, popup_y + 5))

        # Save as Component button
        save_component_button_rect = pygame.Rect(popup_x + 3 * (button_w + 10), popup_y, button_w + 20, button_h)
        pygame.draw.rect(screen, (255, 215, 0), save_component_button_rect)
        screen.blit(font.render("Save", True, (0, 0, 0)), (popup_x + 3 * (button_w + 10) + 10, popup_y + 5))

    # --- SAVE CHANGES BUTTON IN EDIT MODE ---
    if state == COMPONENT_EDIT:
        save_changes_rect = pygame.Rect(WIDTH - 250, HEIGHT - 60, 180, 40)
        pygame.draw.rect(screen, (0, 200, 0), save_changes_rect)
        screen.blit(font.render("Save Changes", True, (255, 255, 255)), (save_changes_rect.x + 15, save_changes_rect.y + 5))
        # Show component name
        if current_edit_component_name:
            name_surf = font.render(f"Editing: {current_edit_component_name}", True, (255, 255, 0))
            screen.blit(name_surf, (20, 10))

    # --- HIGHLIGHT SELECTED CELLS ---
    for (x, y) in selected_cells:
        grid_x = round((x * GRID_SIZE - camera_x) * zoom)
        grid_y = round((y * GRID_SIZE - camera_y) * zoom)
        size = round(GRID_SIZE * zoom)
        pygame.draw.rect(screen, (255, 255, 0), (grid_x, grid_y, size, size), 3)

    draw_hamburger_icon()

    global component_menu_rects
    component_menu_rects = []
    if show_component_menu:
        load_all_components()
        menu_x, menu_y = WIDTH - 250, 100
        menu_w, menu_h = 200, 30 * len(loaded_components) + 10
        pygame.draw.rect(screen, (40, 40, 40), (menu_x, menu_y, menu_w, menu_h))
        for i, comp in enumerate(loaded_components):
            rect = pygame.Rect(menu_x + 10, menu_y + 5 + i * 30, menu_w - 20, 25)
            component_menu_rects.append((rect, comp))
            pygame.draw.rect(screen, (200, 200, 100), rect)
            screen.blit(font.render(comp["name"], True, (0, 0, 0)), (rect.x + 5, rect.y + 2))

    # Item menu background
    pygame.draw.rect(screen, (60, 60, 60), item_menu_rect)

    # Buttons for redstone, power, OR gate, etc.
    pygame.draw.rect(screen, (200, 50, 50) if placement_mode == "redstone" else (100, 100, 100), redstone_button_rect)
    pygame.draw.rect(screen, (50, 200, 50) if placement_mode == "power" else (100, 100, 100), power_button_rect)
    pygame.draw.rect(screen, (50, 50, 200) if placement_mode == "or" else (100, 100, 100), or_button_rect)
    pygame.draw.rect(screen, (200, 200, 50) if placement_mode == "and" else (100, 100, 100), and_button_rect)
    pygame.draw.rect(screen, (200, 50, 200) if placement_mode == "not" else (100, 100, 100), not_button_rect)
    pygame.draw.rect(screen, (200, 50, 50) if placement_mode == "delete" else (100, 100, 100), delete_button_rect)
    pygame.draw.rect(screen, (50, 200, 200) if placement_mode == "xor" else (100, 100, 100), xor_button_rect)
    screen.blit(font.render("Redstone", True, (255, 255, 255)), (redstone_button_rect.x + 5, redstone_button_rect.y + 5))
    screen.blit(font.render("Power", True, (255, 255, 255)), (power_button_rect.x + 5, power_button_rect.y + 5))
    screen.blit(font.render("OR Gate", True, (255, 255, 255)), (or_button_rect.x + 5, or_button_rect.y + 5))
    screen.blit(font.render("AND Gate", True, (255, 255, 255)), (and_button_rect.x + 5, and_button_rect.y + 5))
    screen.blit(font.render("NOT Gate", True, (255, 255, 255)), (not_button_rect.x + 5, not_button_rect.y + 5))
    screen.blit(font.render("Delete", True, (255, 255, 255)), (delete_button_rect.x + 5, delete_button_rect.y + 5))
    screen.blit(font.render("XOR Gate", True, (255, 255, 255)), (xor_button_rect.x + 5, xor_button_rect.y + 5))
    pygame.draw.rect(screen, (150, 100, 255) if placement_mode == "nor" else (100, 100, 100), nor_button_rect)
    pygame.draw.rect(screen, (255, 100, 150) if placement_mode == "nand" else (100, 100, 100), nand_button_rect)
    screen.blit(font.render("NOR Gate", True, (255, 255, 255)), (nor_button_rect.x + 5, nor_button_rect.y + 5))
    screen.blit(font.render("NAND Gate", True, (255, 255, 255)), (nand_button_rect.x + 5, nand_button_rect.y + 5))
    pygame.draw.rect(screen, (100, 200, 255) if placement_mode == "lasso" else (100, 100, 100), lasso_button_rect)
    screen.blit(font.render("Lasso", True, (255, 255, 255)), (lasso_button_rect.x + 5, lasso_button_rect.y + 5))        
    pygame.draw.rect(screen, (255, 215, 0) if show_component_menu else (100, 100, 100), load_component_button_rect)
    screen.blit(font.render("Load", True, (0, 0, 0)), (load_component_button_rect.x + 18, load_component_button_rect.y + 5))

    # Side menu
    if menu_open:
        pygame.draw.rect(screen, (50, 50, 50), side_menu_rect)
        pygame.draw.rect(screen, (180, 50, 50), exit_button_rect)
        screen.blit(font.render("Exit", True, (255, 255, 255)), (exit_button_rect.x + 10, exit_button_rect.y + 5))


running = True
while running:
    if state == MENU:
        draw_menu()
    elif state == COMPONENT_LIST:
        back_rect = draw_component_list()
    else:
        draw_grid()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos

            # --- COMPONENT LIST MENU HANDLING ---
            if state == COMPONENT_LIST:
                if back_rect.collidepoint(mx, my):
                    state = MENU
                    continue
                for rect, comp in component_menu_rects:
                    if rect.collidepoint(mx, my):
                        load_component_to_grid(comp)
                        current_edit_component_name = comp["name"]
                        state = COMPONENT_EDIT
                        break
                continue

            # --- SAVE CHANGES BUTTON IN EDIT MODE ---
            if state == COMPONENT_EDIT and save_changes_rect and save_changes_rect.collidepoint(mx, my):
                # Gather all non-empty cells in the grid
                cells = []
                min_x, min_y, max_x, max_y = grid_width, grid_height, 0, 0
                for y in range(grid_height):
                    for x in range(grid_width):
                        cell = grid[y][x]
                        if cell["type"] != "empty":
                            min_x = min(min_x, x)
                            min_y = min(min_y, y)
                            max_x = max(max_x, x)
                            max_y = max(max_y, y)

                else:
                    for y in range(min_y, max_y + 1):
                        for x in range(min_x, max_x + 1):
                            cell = grid[y][x]
                            if cell["type"] != "empty":
                                cells.append({"dx": x - min_x, "dy": y - min_y, "cell": cell.copy()})
                    component = {
                        "name": current_edit_component_name,
                        "width": max_x - min_x + 1,
                        "height": max_y - min_y + 1,
                        "cells": cells
                    }
                    with open(os.path.join(components_dir, f"{current_edit_component_name}.json"), "w") as f:
                        json.dump(component, f)
                
                continue

            # --- BACK BUTTON IN COMPONENT_EDIT ---
            if state == COMPONENT_EDIT:
                if menu_button_rect.collidepoint(mx, my):
                    state = MENU
                    menu_open = False
                    continue

            # --- POPUP MENU BUTTON HANDLING ---
            if selected_cells:
                if copy_button_rect and copy_button_rect.collidepoint(mx, my):
                    clipboard.clear()
                    xs = [x for x, y in selected_cells]
                    ys = [y for x, y in selected_cells]
                    min_x, min_y = min(xs), min(ys)
                    for (x, y) in selected_cells:
                        cell = grid[y][x].copy()
                        clipboard.append((x - min_x, y - min_y, cell))
                
                
                    continue
                elif delete_button_rect_popup and delete_button_rect_popup.collidepoint(mx, my):
                    for (x, y) in selected_cells:
                        grid[y][x] = {"type": "empty", "powered": False}
                    selected_cells.clear()
                  
                
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
                elif save_component_button_rect and save_component_button_rect.collidepoint(mx, my):
                    name = prompt_for_name()
                    if name:
                        save_selected_as_component(name)
                    continue

            # --- LOAD COMPONENT BUTTON HANDLING ---
            if load_component_button_rect.collidepoint(mx, my):
                show_component_menu = not show_component_menu
                continue

            # --- COMPONENT MENU PLACEMENT ---
            if show_component_menu:
                for rect, comp in component_menu_rects:
                    if rect.collidepoint(mx, my):
                        gx = int((mx / zoom + camera_x) // GRID_SIZE)
                        gy = int((my / zoom + camera_y) // GRID_SIZE)
                        place_component(comp, gx, gy)
                        show_component_menu = False
                        break
                continue

            # --- MAIN MENU BUTTONS ---
            if state == MENU:
                if 250 <= my <= 300:  # "Make New Component"
                    for y in range(grid_height):
                        for x in range(grid_width):
                            grid[y][x] = {"type": "empty", "powered": False}
                    state = BUILD_MODE
                elif 320 <= my <= 370:  # "View Components"
                    state = COMPONENT_LIST
                elif 390 <= my <= 440:  # "Exit"
                    running = False

            # --- BUILD/EDIT MODE BUTTONS ---
            elif state == BUILD_MODE or state == COMPONENT_EDIT:
                if menu_button_rect.collidepoint(mx, my):
                    menu_open = not menu_open
                if redstone_button_rect.collidepoint(mx, my):
                    placement_mode = "redstone"
                    clear_lasso_selection()
                elif power_button_rect.collidepoint(mx, my):
                    placement_mode = "power"
                    clear_lasso_selection()
                if or_button_rect.collidepoint(mx, my):
                    placement_mode = "or"
                    clear_lasso_selection()
                elif and_button_rect.collidepoint(mx, my):
                    placement_mode = "and"
                    clear_lasso_selection()
                elif not_button_rect.collidepoint(mx, my):
                    placement_mode = "not"
                    clear_lasso_selection()
                elif delete_button_rect.collidepoint(mx, my):
                    placement_mode = "delete"
                    clear_lasso_selection()
                elif xor_button_rect.collidepoint(mx, my):
                    placement_mode = "xor"
                    clear_lasso_selection()
                elif nor_button_rect.collidepoint(mx, my):
                    placement_mode = "nor"
                    clear_lasso_selection()
                elif nand_button_rect.collidepoint(mx, my):
                    placement_mode = "nand"
                    clear_lasso_selection()
                elif lasso_button_rect.collidepoint(mx, my):
                    placement_mode = "lasso"
                    # Do NOT clear selection here, so user can use popup!

                elif menu_open and exit_button_rect.collidepoint(mx, my):
                    state = MENU
                    menu_open = False
                    continue

                # --- LASSO TOOL START ---
                if placement_mode == "lasso" and event.button == 1:
                    lasso_start = (int((mx / zoom + camera_x) // GRID_SIZE),
                                   int((my / zoom + camera_y) // GRID_SIZE))
                    lasso_end = lasso_start

                # --- NORMAL PLACEMENT/DELETE ---
                elif event.button == 1:
                    x = int((mx / zoom + camera_x) // GRID_SIZE)
                    y = int((my / zoom + camera_y) // GRID_SIZE)
                    if 0 <= x < grid_width and 0 <= y < grid_height:
                        if placement_mode == "redstone":
                            grid[y][x] = {"type": "redstone", "powered": False}
                        elif placement_mode == "power":
                            grid[y][x] = {"type": "power", "powered": True}
                        elif placement_mode == "or":
                            place_gate(x, y, "or", current_gate_rotation)
                        elif placement_mode == "and":
                            place_gate(x, y, "and", current_gate_rotation)
                        elif placement_mode == "not":
                            place_gate(x, y, "not", current_gate_rotation)
                        elif placement_mode == "xor":
                            place_gate(x, y, "xor", current_gate_rotation)
                        elif placement_mode == "nor":
                            place_gate(x, y, "nor", current_gate_rotation)
                        elif placement_mode == "nand":
                            place_gate(x, y, "nand", current_gate_rotation)
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

                elif event.button == 3:  # Right-click to start panning
                    panning = True
                    last_mouse_x, last_mouse_y = event.pos
                elif event.button == 4:  # Scroll up (smooth zoom in)
                    target_zoom *= 1.1
                elif event.button == 5:  # Scroll down (smooth zoom out)
                    target_zoom /= 1.1
        elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:  # Press 'R' to rotate
                        current_gate_rotation = (current_gate_rotation + 1) % 4

        # --- LASSO TOOL DRAG ---
        elif event.type == pygame.MOUSEMOTION:
            if placement_mode == "lasso" and lasso_start:
                lasso_end = (int((event.pos[0] / zoom + camera_x) // GRID_SIZE),
                             int((event.pos[1] / zoom + camera_y) // GRID_SIZE))
            elif panning:
                dx = event.pos[0] - last_mouse_x
                dy = event.pos[1] - last_mouse_y
                target_camera_x -= dx / zoom
                target_camera_y -= dy / zoom
                last_mouse_x, last_mouse_y = event.pos

        # --- LASSO TOOL END ---
        elif event.type == pygame.MOUSEBUTTONUP:
            if placement_mode == "lasso" and event.button == 1 and lasso_start:
                x1, y1 = lasso_start
                x2, y2 = lasso_end
                x_min, x_max = sorted([x1, x2])
                y_min, y_max = sorted([y1, y2])
                initial_selection = set()
                for y in range(y_min, y_max + 1):
                    for x in range(x_min, x_max + 1):
                        if 0 <= x < grid_width and 0 <= y < grid_height:
                            initial_selection.add((x, y))
                # Expand selection to include all tiles of any gate touched
                expanded_selection = set(initial_selection)
                for (x, y) in initial_selection:
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
                                    expanded_selection.add((gx, gy))
                selected_cells.clear()
                selected_cells.update(expanded_selection)
                lasso_start = lasso_end = None
            elif event.button == 3:
                panning = False

    pygame.display.flip()
    clock.tick(60)

pygame.quit()

