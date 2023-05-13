import pygame as py
py.font.init()


# =================== General constants =========================
DEBUG = False
FPS = 60
WIN_WIDTH = 700
WIN_HEIGHT = 860
STARTING_POS = (WIN_WIDTH/2, WIN_HEIGHT-100)

# ====== AI SCORE SETTINGS
SCORE_VEL_MULTIPLIER = 0.001    # bonus for faster cars
BAD_GENOME_THRESHOLD = 300       # if a car is too far behind it is removed
INPUT_NEURONS = 6  # 9
OUTPUT_NEURONS = 2

# ================== SEASON SETTINGS =============================
SEASON = 2023
# =================== Car Specs ==================================

CAR_DBG = True
FRICTION = -0.1
MAX_VEL = 40
MAX_VEL_REDUCTION = 1  # at the start reduce maximum speed
ACC_STRENGTH = 0.15
BRAKE_STRENGTH = 1.5
TURN_VEL = 3.5
SENSOR_DISTANCE = 300  # distance in px 1m = 10px
ACTIVATION_THRESHOLD = 0.0
MMTOMETERS = 1/1000
STEERING_THRESHOLD = 0.01
STEERING_SPEED = 20  # [°/s]
PPM = 10  # Pixels per meter (conversion scale)
MPP = 1/PPM  # Meters per pixel
# =================== TRACK Specs ==================================

ROAD_DBG = False
MAX_ANGLE = 1
MAX_DEVIATION = 300
SPACING = 250
NUM_POINTS = 30                # number of points for each segment
SAFE_SPACE = SPACING + 50      # buffer space above the screen
ROAD_WIDTH = 250

# =================== Display and Colors ==============
NODE_RADIUS = 20
NODE_SPACING = 5
LAYER_SPACING = 100
CONNECTION_WIDTH = 1

WHITE = (255, 255, 255)
GRAY = (200, 200, 200)
BLACK = (0, 0, 0)
RED = (200, 0, 0)
RED_PALE = (250, 200, 200)

GREEN = (0, 200, 0)
GREEN_PALE = (200, 250, 200)

BLUE = (0, 0, 255)
BLUE_PALE = (200, 200, 255)

DARK_RED = (100, 0, 0)
DARK_RED_PALE = (150, 100, 100)
DARK_GREEN = (0, 100, 0)
DARK_BLUE = (100, 100, 150)
DARK_GRAY = (150, 150, 150)
DARK_GREEN_PALE = (100, 150, 100)

TEXTCOLOR = (255, 255, 255)
BACKGROUNDCOLOR = (0, 0, 0)

# ======= FONTS ============================
NODE_FONT = py.font.SysFont("comicsans", 15)
STAT_FONT = py.font.SysFont("comicsans", 30)


# =================== Constants for internal use ==============
GEN = 0

# enumerations
ACC = 0
BRAKE = 1
TURN_LEFT = 2
TURN_RIGHT = 3
THROTTLE = 0
STEER = 1
INPUT = 0
MIDDLE = 1
OUTPUT = 2
