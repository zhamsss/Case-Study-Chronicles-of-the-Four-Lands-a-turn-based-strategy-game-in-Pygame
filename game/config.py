SCREEN_WIDTH = 1600
SCREEN_HEIGHT = 900

FPS = 60

GAME_TITLE = "Gexatron"

BACKGROUND_COLOR = (28, 35, 45)

# --- Карта (pointy-top гексы, схема "odd-r": нечётные строки сдвинуты вправо) ---
MAP_WIDTH = 20   # гексов в строке
MAP_HEIGHT = 18  # строк

GRID_OFFSET_X = 70
GRID_OFFSET_Y = 70

# --- Интерфейс ---
SIDE_PANEL_WIDTH = 320
PANEL_X = SCREEN_WIDTH - SIDE_PANEL_WIDTH

HEX_SIZE = 56

CAMERA_SPEED = 15

MIN_ZOOM = 0.6
MAX_ZOOM = 2.0
ZOOM_STEP = 0.1

PLAYER_COLORS = {
    1: (255, 60, 60),
    2: (0, 180, 255),
    3: (0, 255, 0),
    4: (180, 0, 255),
}

# --- Правила / экономика ---
START_GOLD = 20

UNIT_COST = {1: 10, 2: 20, 3: 30, 4: 40}
UNIT_MOVE_RANGE = 4          # на сколько клеток ходит юнит за ход

FARM_BASE_COST = 12          # цена первой фермы в регионе
FARM_COST_STEP = 2           # каждая следующая ферма дороже на столько
FARM_INCOME = 4              # доход фермы (сверх 1 за клетку)

TOWER_COST = {1: 15, 2: 35}
TOWER_UPKEEP = {1: 1, 2: 6}

TREE_DENSITY = 0.10          # доля клеток с деревьями на старте
TREE_SPREAD_CHANCE = 0.12    # шанс дерева дать росток за раунд
TREE_CHOP_REWARD = 3         # золото за срубленное дерево
