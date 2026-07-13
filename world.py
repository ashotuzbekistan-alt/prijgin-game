"""Построение игрового мира из текстовой карты уровня."""
import pygame
from settings import TILE_SIZE
from entities import Block, Coin, Enemy, Flag, Player, Boss


class Level:
    def __init__(self, tile_map, is_boss_level=False):
        self.blocks = pygame.sprite.Group()
        self.coins = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.spikes = pygame.sprite.Group()
        self.flag = None
        self.boss = None
        self.player_start = (100, 100)
        self.is_boss_level = is_boss_level
        self.width = len(tile_map[0]) * TILE_SIZE
        self.height = len(tile_map) * TILE_SIZE

        for row_idx, row in enumerate(tile_map):
            for col_idx, ch in enumerate(row):
                x = col_idx * TILE_SIZE
                y = row_idx * TILE_SIZE
                if ch == "X":
                    self.blocks.add(Block(x, y, "ground"))
                elif ch == "B":
                    self.blocks.add(Block(x, y, "brick"))
                elif ch == "?":
                    self.blocks.add(Block(x, y, "question"))
                elif ch == "^":
                    b = Block(x, y, "spike")
                    self.blocks.add(b)
                    self.spikes.add(b)
                elif ch == "C":
                    self.coins.add(Coin(x, y))
                elif ch == "E":
                    self.enemies.add(Enemy(x, y))
                elif ch == "P":
                    self.player_start = (x, y - TILE_SIZE)
                elif ch == "F":
                    self.flag = Flag(x, y - TILE_SIZE * 3, TILE_SIZE * 4)
                elif ch == "W":
                    self.boss = Boss(x, y - TILE_SIZE * 2)

    def all_solid_blocks(self):
        return self.blocks
