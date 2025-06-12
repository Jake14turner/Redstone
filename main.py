import pygame
import math  # Needed for the X animation

# Setup Pygame
pygame.init()
WIDTH, HEIGHT = 800, 600
GRID_SIZE = 20
GRID_COLOR = (100, 100, 100, 150)
REDSTONE_BASE = (255, 50, 50)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()
font = pygame.font.Font(None, 36)  # Font for text rendering

# Menu state
MENU, BUILD_MODE = "menu", "build"
state = MENU  # Start in the main menu
menu_open = False  # Tracks whether the side menu is visible

# Camera controls
camera_x, camera_y = 0, 0
target_camera_x, target_camera_y = camera_x, camera_y
move_speed = 0.15  
zoom = 1.0
target_zoom = zoom
zoom_speed = 0.1

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
item_menu_anim = 0.0  # 0.0 = hidden, 1.0 = fully visible


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



clipboard = []

# Hamburger icon animation variables
menu_icon_hover = False
menu_icon_animation = 0.0  # For smooth transitions

def lerp(a, b, t):
    return a + (b - a) * t  # Linear interpolation
item_menu_anim = 0.0  # 0.0 = hidden, 1.0 = fully visible


# Add these at the top with other initializations
rotation = 0
hover_states = {0: False, 1: False, 2: False}
text_scales = [1.0, 1.0, 1.0]
TARGET_SCALE = 1.15  # Slightly more subtle
SCALE_SPEED = 0.2    # Faster but still smooth
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


def place_gate(x, y, gate_type, rotation):
    typeOfGate = f"{rotation}-{gate_type}"
    definition = GATE_DEFINITIONS[typeOfGate]
    w, h = definition["size"]

    # Check if space is available
    for dy in range(h):
        for dx in range(w):
            gx = x + dx
            gy = y + dy
            if not (0 <= gx < grid_width and 0 <= gy < grid_height):
                return  # Out of bounds
            if grid[gy][gx]["type"] != "empty":
                return  # Already occupied

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
# Define colors using RGB values
GREEN = (0, 255, 0)   # RGB for green
GRAY = (169, 169, 169)  # RGB for gray
BLUE = (0, 0, 255)    # RGB for blue
# Define colors using RGB values
YELLOW = (255, 255, 0)  # RGB for yellow
WHITE = (255, 255, 255)  # RGB for white

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

    # Step 3: Evaluate gates
    for y in range(grid_height):
        for x in range(grid_width):
            cell = grid[y][x]
            if cell["type"] == "gate" and cell["local_pos"] == (0, 0):  # Top-left of gate
                gate_def = GATE_DEFINITIONS[cell["gate_type"]]
                evaluate_gate(x, y, gate_def)


def evaluate_gate(x, y, definition):
    inputs_powered = []
    for dx, dy in definition["inputs"]:
        gx, gy = x + dx, y + dy
        if 0 <= gx < grid_width and 0 <= gy < grid_height:
            inputs_powered.append(grid[gy][gx]["powered"])
    print(f"{definition['logic'].upper()} gate at ({x},{y}) inputs: {inputs_powered}")  # Debug

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
                # Allow input cells to be powered
                if local_pos in gate_def.get("inputs", []):
                    if not cell["powered"]:
                        cell["powered"] = True
                # Allow output cell to emit power
                if local_pos == gate_def.get("output"):
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
                    gate_def = GATE_DEFINITIONS.get(cell["gate_type"], {})
                    local_pos = cell.get("local_pos", (0, 0))
                    input_offsets = gate_def.get("inputs", [])
                    output_offset = gate_def.get("output", (-1, -1))

                    # Only draw the "U" shape: inputs, output, and vertical sides
                    u_shape = input_offsets + [output_offset]
                    if cell["gate_type"] == "0-not" or cell["gate_type"] == "1-not" or cell["gate_type"] == "2-not" or cell["gate_type"] == "3-not":
                        not_shape = input_offsets + [output_offset]
                        if local_pos in not_shape:
                            color = (30, 30, 180) if not cell["powered"] else (90, 140, 255)  # Dark blue → Soft electric blue
                            pygame.draw.rect(screen, color, rect)
                            label_text = ""
                            if local_pos in input_offsets:
                                label_text = "IN"
                            elif local_pos == output_offset:
                                label_text = "OUT"
                            if label_text:
                                label = font.render(label_text, True, WHITE)
                                screen.blit(label, (rect.x + 2, rect.y + 2))

                    elif cell["gate_type"] == "0-xor" or cell["gate_type"] == "1-xor" or cell["gate_type"] == "2-xor" or cell["gate_type"] == "3-xor":
                        if local_pos in u_shape:
                            color = (255, 255, 0) if not cell["powered"] else (0, 200, 200)  # Yellow → Bright cyan
                            pygame.draw.rect(screen, color, rect)
                            label_text = ""
                            if local_pos in input_offsets:
                                label_text = "IN"
                            elif local_pos == output_offset:
                                label_text = "OUT"
                            if label_text:
                                label = font.render(label_text, True, WHITE)
                                screen.blit(label, (rect.x + 2, rect.y + 2))

                    elif cell["gate_type"] == "0-nor" or cell["gate_type"] == "1-nor" or cell["gate_type"] == "2-nor" or cell["gate_type"] == "3-nor":
                        if local_pos in u_shape:
                            color = (130, 0, 0) if not cell["powered"] else (255, 80, 120)  # Deep red → Bright pink
                            pygame.draw.rect(screen, color, rect)
                            label_text = ""
                            if local_pos in input_offsets:
                                label_text = "IN"
                            elif local_pos == output_offset:
                                label_text = "OUT"
                            if label_text:
                                label = font.render(label_text, True, WHITE)
                                screen.blit(label, (rect.x + 2, rect.y + 2))

                    elif cell["gate_type"] == "0-nand" or cell["gate_type"] == "1-nand" or cell["gate_type"] == "2-nand" or cell["gate_type"] == "3-nand":
                        if local_pos in u_shape:
                            color = (90, 0, 140) if not cell["powered"] else (200, 0, 255)  # Deep purple → Neon violet
                            pygame.draw.rect(screen, color, rect)
                            label_text = ""
                            if local_pos in input_offsets:
                                label_text = "IN"
                            elif local_pos == output_offset:
                                label_text = "OUT"
                            if label_text:
                                label = font.render(label_text, True, WHITE)
                                screen.blit(label, (rect.x + 2, rect.y + 2))

                    elif cell["gate_type"] == "0-or" or cell["gate_type"] == "1-or" or cell["gate_type"] == "2-or" or cell["gate_type"] == "3-or":
                        if local_pos in u_shape:
                            color = (255, 130, 0) if not cell["powered"] else (255, 200, 0)  # Reddish orange → Golden yellow
                            pygame.draw.rect(screen, color, rect)
                            label_text = ""
                            if local_pos in input_offsets:
                                label_text = "IN"
                            elif local_pos == output_offset:
                                label_text = "OUT"
                            if label_text:
                                label = font.render(label_text, True, WHITE)
                                screen.blit(label, (rect.x + 2, rect.y + 2)) 

                    elif cell["gate_type"] == "0-and" or cell["gate_type"] == "1-and" or cell["gate_type"] == "2-and" or cell["gate_type"] == "3-and":
                        if local_pos in u_shape:
                            color = (0, 120, 0) if not cell["powered"] else (0, 255, 0)  # Forest green → Bright green
                            pygame.draw.rect(screen, color, rect)
                            label_text = ""
                            if local_pos in input_offsets:
                                label_text = "IN"
                            elif local_pos == output_offset:
                                label_text = "OUT"
                            if label_text:
                                label = font.render(label_text, True, WHITE)
                                screen.blit(label, (rect.x + 2, rect.y + 2))


    # --- SELECT RECTANGLE ---
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
    
        # --- POPUP MENU FOR LASSO SELECTION ---
    global copy_button_rect, delete_button_rect_popup, paste_button_rect
    copy_button_rect = None
    delete_button_rect_popup = None
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

         # Paste button (only enabled if clipboard is not empty)
        paste_button_rect = pygame.Rect(popup_x + 2 * (button_w + 10), popup_y, button_w, button_h)
        paste_color = (80, 180, 255) if clipboard else (120, 120, 120)
        pygame.draw.rect(screen, paste_color, paste_button_rect)
        screen.blit(font.render("Paste", True, (255, 255, 255)), (popup_x + 2 * (button_w + 10) + 8, popup_y + 5))
    # --- HIGHLIGHT SELECTED CELLS ---
    for (x, y) in selected_cells:
        grid_x = round((x * GRID_SIZE - camera_x) * zoom)
        grid_y = round((y * GRID_SIZE - camera_y) * zoom)
        size = round(GRID_SIZE * zoom)
        pygame.draw.rect(screen, (255, 255, 0), (grid_x, grid_y, size, size), 3)

    draw_hamburger_icon()

    # Item menu background
    pygame.draw.rect(screen, (60, 60, 60), item_menu_rect)

    # --- ITEM MENU BUTTONS ---

    GATE_COLORS = {
        "redstone": (255, 0, 0),
        "power": (255, 255, 0),
        "or": (255, 130, 0),
        "and": (0, 255, 0),
        "not": (30, 30, 180),
        "xor": (0, 255, 255),
        "nor": (255, 80, 120),
        "nand": (200, 0, 255),
        "delete": (255, 80, 80),
        "select": (100, 200, 255),
    }

    button_defs = [
        ("redstone", redstone_button_rect, "Redstone"),
        ("power", power_button_rect, "Power"),
        ("or", or_button_rect, "OR"),
        ("and", and_button_rect, "AND"),
        ("not", not_button_rect, "NOT"),
        ("xor", xor_button_rect, "XOR"),
        ("nor", nor_button_rect, "NOR"),
        ("nand", nand_button_rect, "NAND"),
        ("select", lasso_button_rect, "Lasso"),
        ("delete", delete_button_rect, "Delete"),
    ]

    mouse_pos = pygame.mouse.get_pos()
    for mode, rect, label in button_defs:
        is_hover = rect.collidepoint(mouse_pos)
        is_active = (
            (mode == "redstone" and placement_mode == "redstone") or
            (mode == "power" and placement_mode == "power") or
            (mode == "or" and placement_mode == "or") or
            (mode == "and" and placement_mode == "and") or
            (mode == "not" and placement_mode == "not") or
            (mode == "xor" and placement_mode == "xor") or
            (mode == "nor" and placement_mode == "nor") or
            (mode == "nand" and placement_mode == "nand") or
            (mode == "delete" and placement_mode == "delete") or
            (mode == "select" and placement_mode == "select")
        )
        base_color = GATE_COLORS.get(mode, (255, 255, 255))
        # Pastel/glow color for hover/active
        pastel = tuple(min(255, int(c * 0.6 + 255 * 0.4)) for c in base_color)
        draw_color = pastel if (is_hover or is_active) else (0, 0, 0)
        # Inflate softly if hovered/active
        draw_rect = rect.inflate(10, 8) if (is_hover or is_active) else rect
        pygame.draw.rect(screen, draw_color, draw_rect, border_radius=8)
        # Draw label (always white, auto-fit)
        # Use a slightly smaller font for long labels
        font_size = 24 if len(label) > 8 else 28
        btn_font = pygame.font.Font(None, font_size)
        text_surf = btn_font.render(label, True, (255, 255, 255))
        text_rect = text_surf.get_rect(center=draw_rect.center)
        screen.blit(text_surf, text_rect)
    
    # Side menu
    if menu_open:
        pygame.draw.rect(screen, (50, 50, 50), side_menu_rect)
        pygame.draw.rect(screen, (180, 50, 50), exit_button_rect)
        screen.blit(font.render("Exit", True, (255, 255, 255)), (exit_button_rect.x + 10, exit_button_rect.y + 5))


running = True
while running:
    if state == MENU:
        draw_menu()
    else:
        draw_grid()

    # Animate item menu slide-in
    mouse_x, _ = pygame.mouse.get_pos()
    show_menu = mouse_x > WIDTH - 60  # Show menu if mouse near right edge
    target_anim = 1.0 if show_menu else 0.0
    item_menu_anim += (target_anim - item_menu_anim) * 0.3  # Smooth lerp

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                rotation = rotation + 1 if rotation < 3 else 0

        elif event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos

            # --- POPUP MENU BUTTON HANDLING ---
            if selected_cells:
                if copy_button_rect and copy_button_rect.collidepoint(mx, my):
                    # Copy logic
                    clipboard.clear()
                    xs = [x for x, y in selected_cells]
                    ys = [y for x, y in selected_cells]
                    min_x, min_y = min(xs), min(ys)
                    for (x, y) in selected_cells:
                        cell = grid[y][x].copy()
                        clipboard.append((x - min_x, y - min_y, cell))
                    print("Copied selection!")
                    continue  # Prevent further placement logic this click
                elif delete_button_rect_popup and delete_button_rect_popup.collidepoint(mx, my):
                    # Delete logic
                    for (x, y) in selected_cells:
                        grid[y][x] = {"type": "empty", "powered": False}
                    selected_cells.clear()
                    print("Deleted selection!")
                    continue  # Prevent further placement logic this click
                elif paste_button_rect and paste_button_rect.collidepoint(mx, my) and clipboard:
                    # Paste logic: paste at top-left of current selection
                    xs = [x for x, y in selected_cells]
                    ys = [y for x, y in selected_cells]
                    base_x, base_y = min(xs), min(ys)
                    for dx, dy, cell in clipboard:
                        gx, gy = base_x + dx, base_y + dy
                        if 0 <= gx < grid_width and 0 <= gy < grid_height:
                            grid[gy][gx] = cell.copy()
                    print("Pasted selection!")
                    continue  # Prevent further placement logic this click

            if state == MENU:
                if 250 <= my <= 300:  # "Make New Component"
                    state = BUILD_MODE
                elif 320 <= my <= 370:  # "View Components"
                    print("View Components Clicked!")  # Placeholder action
                elif 390 <= my <= 440:  # "Exit"
                    running = False
            elif state == BUILD_MODE:
                if menu_button_rect.collidepoint(mx, my):  # Clicked menu button
                    menu_open = not menu_open
                if redstone_button_rect.collidepoint(mx, my):
                    placement_mode = "redstone"
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
                    # Do NOT clear selection here, so user can use popup!
                elif delete_button_rect.collidepoint(mx, my):
                    placement_mode = "delete"
                    clear_lasso_selection()
                    continue

                elif menu_open and exit_button_rect.collidepoint(mx, my):  # Clicked "Exit"
                    state = MENU
                    menu_open = False

                # --- LASSO TOOL START ---
                if placement_mode == "select" and event.button == 1:
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
                        elif placement_mode == "delete":
                            cell = grid[y][x]
                            if cell["type"] == "gate":
                                # Remove the entire gate
                                gate_type = cell["gate_type"]
                                local_pos = cell["local_pos"]
                                gate_def = GATE_DEFINITIONS[gate_type]
                                w, h = gate_def["size"]
                                # Find the origin of the gate
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

        # --- LASSO TOOL DRAG ---
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

        # --- LASSO TOOL END ---
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
