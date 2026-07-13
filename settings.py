"""Общие настройки и константы игры."""

# Экран
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60
TITLE = "Прыжкин: Приключение"

TILE_SIZE = 40

# Цвета (R, G, B)
SKY_BLUE = (92, 148, 252)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (216, 40, 0)
DARK_RED = (140, 20, 0)
BROWN = (150, 90, 40)
DARK_BROWN = (110, 60, 20)
GREEN = (0, 160, 60)
DARK_GREEN = (0, 110, 40)
YELLOW = (255, 216, 0)
GOLD = (255, 190, 0)
GRAY = (120, 120, 120)
PURPLE = (120, 40, 160)
ORANGE = (240, 130, 30)
SKIN = (250, 200, 160)

# Физика
GRAVITY = 0.8
PLAYER_SPEED = 5
PLAYER_JUMP = -16
MAX_FALL_SPEED = 18
ENEMY_SPEED = 2

# Игрок
PLAYER_START_LIVES = 3
INVINCIBLE_TIME = 90  # кадров неуязвимости после урона

# Состояния игры
STATE_MENU = "menu"
STATE_PLAYING = "playing"
STATE_PAUSED = "paused"
STATE_GAME_OVER = "game_over"
STATE_WIN = "win"
STATE_LEVEL_COMPLETE = "level_complete"
STATE_BOSS = "boss"
