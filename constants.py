import pygame

# --- Window / Grid ---
WIDTH, HEIGHT = 800, 600
GRID_SIZE = 20
GRID_COLOR = (100, 100, 100, 150)
REDSTONE_BASE = (255, 50, 50)

# --- Colors ---
GREEN = (0, 255, 0)
GRAY = (169, 169, 169)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
WHITE = (255, 255, 255)

gold_base = (253, 255, 150)
gold_light = (253, 255, 117)

# --- States ---
MENU = "menu"
BUILD_MODE = "build"
VIEW_COMPONENTS = "view_components"
NAMING_COMPONENT = "naming_component"
PASTE_COMPONENT = "paste_component"

COMPONENTS_FILE = "components.json"

# --- Gate Definitions ---
ONE_WAY_TYPES = {
    "0-one_way": {"size": (1, 1), "inputs": [(0, 0)], "output": (0, -1), "logic": "one_way"},
    "1-one_way": {"size": (1, 1), "inputs": [(0, 0)], "output": (1, 0),  "logic": "one_way"},
    "2-one_way": {"size": (1, 1), "inputs": [(0, 0)], "output": (0, 1),  "logic": "one_way"},
    "3-one_way": {"size": (1, 1), "inputs": [(0, 0)], "output": (-1, 0), "logic": "one_way"},
}

GATE_DEFINITIONS = {
    "0-or":   {"size": (3, 2), "inputs": [(0, 0), (2, 0)], "output": (1, 1), "logic": "or"},
    "1-or":   {"size": (2, 3), "inputs": [(0, 0), (0, 2)], "output": (1, 1), "logic": "or"},
    "2-or":   {"size": (3, 2), "inputs": [(0, 1), (2, 1)], "output": (1, 0), "logic": "or"},
    "3-or":   {"size": (2, 3), "inputs": [(1, 0), (1, 2)], "output": (0, 1), "logic": "or"},
    "0-and":  {"size": (3, 2), "inputs": [(0, 0), (2, 0)], "output": (1, 1), "logic": "and"},
    "1-and":  {"size": (2, 3), "inputs": [(0, 0), (0, 2)], "output": (1, 1), "logic": "and"},
    "2-and":  {"size": (3, 2), "inputs": [(0, 1), (2, 1)], "output": (1, 0), "logic": "and"},
    "3-and":  {"size": (2, 3), "inputs": [(1, 0), (1, 2)], "output": (0, 1), "logic": "and"},
    "0-not":  {"size": (1, 2), "inputs": [(0, 0)],         "output": (0, 1), "logic": "not"},
    "1-not":  {"size": (2, 1), "inputs": [(1, 0)],         "output": (0, 0), "logic": "not"},
    "2-not":  {"size": (1, 2), "inputs": [(0, 1)],         "output": (0, 0), "logic": "not"},
    "3-not":  {"size": (2, 1), "inputs": [(0, 0)],         "output": (1, 0), "logic": "not"},
    "0-xor":  {"size": (3, 2), "inputs": [(0, 0), (2, 0)], "output": (1, 1), "logic": "xor"},
    "1-xor":  {"size": (2, 3), "inputs": [(0, 0), (0, 2)], "output": (1, 1), "logic": "xor"},
    "2-xor":  {"size": (3, 2), "inputs": [(0, 1), (2, 1)], "output": (1, 0), "logic": "xor"},
    "3-xor":  {"size": (2, 3), "inputs": [(1, 0), (1, 2)], "output": (0, 1), "logic": "xor"},
    "0-nor":  {"size": (3, 2), "inputs": [(0, 0), (2, 0)], "output": (1, 1), "logic": "nor"},
    "1-nor":  {"size": (2, 3), "inputs": [(0, 0), (0, 2)], "output": (1, 1), "logic": "nor"},
    "2-nor":  {"size": (3, 2), "inputs": [(0, 1), (2, 1)], "output": (1, 0), "logic": "nor"},
    "3-nor":  {"size": (2, 3), "inputs": [(1, 0), (1, 2)], "output": (0, 1), "logic": "nor"},
    "0-nand": {"size": (3, 2), "inputs": [(0, 0), (2, 0)], "output": (1, 1), "logic": "nand"},
    "1-nand": {"size": (2, 3), "inputs": [(0, 0), (0, 2)], "output": (1, 1), "logic": "nand"},
    "2-nand": {"size": (3, 2), "inputs": [(0, 1), (2, 1)], "output": (1, 0), "logic": "nand"},
    "3-nand": {"size": (2, 3), "inputs": [(1, 0), (1, 2)], "output": (0, 1), "logic": "nand"},
}

GATE_COLORS = {
    "redstone": (255, 0, 0),
    "power":    (255, 255, 0),
    "bridge":   (120, 120, 255),
    "or":       (255, 130, 0),
    "and":      (0, 255, 0),
    "not":      (30, 30, 180),
    "xor":      (0, 255, 255),
    "nor":      (255, 80, 120),
    "nand":     (200, 0, 255),
    "delete":   (255, 80, 80),
    "select":   (100, 200, 255),
    "clock":    (0, 200, 200),
}
