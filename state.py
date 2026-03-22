"""
Global mutable game state, imported by all modules that need it.
Avoids passing giant argument lists or circular imports.
"""

# Grid
grid_width = 2000
grid_height = 500
grid = []  # Populated at startup

# Camera / zoom
camera_x = 0.0
camera_y = 0.0
target_camera_x = 0.0
target_camera_y = 0.0
zoom = 1.0
target_zoom = 1.0

# Placement
placement_mode = "redstone"
rotation = 0
gate_counter = 0
propagation_mode = False

# Selection / lasso
lasso_start = None
lasso_end = None
selected_cells = set()
clipboard = []

# UI
state = "menu"
menu_open = False
item_menu_anim = 0.0

# Paste / component
paste_mode = False
selected_paste_component = None
components_list = []
selected_component_index = 0
editing_component_index = None
component_name_input = ""

# Error timers
placement_error_timer = 0
no_components_error = 0

# Zoom bar
zoom_bar_anim = 0.0
zoom_bar_height = 60
zoom_slider_dragging = False

# Panning
panning = False
last_mouse_x = 0
last_mouse_y = 0
dragging_placement = False

# FPS
frame_count = 0
fps_timer = 0
current_fps = 0

# Menu animation
menu_icon_hover = False
menu_icon_animation = 0.0

# Button hover scales (populated in drawing.py)
button_scales = {}
