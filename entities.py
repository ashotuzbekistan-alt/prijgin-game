"""Классы игровых объектов."""
import pygame
import math
from settings import *


class Block(pygame.sprite.Sprite):
    def __init__(self, x, y, kind="ground"):
        super().__init__()
        self.kind = kind
        self.image = pygame.Surface((TILE_SIZE, TILE_SIZE))
        self.has_coin = kind == "question"
        self.hit_flash = 0
        self._draw()
        self.rect = self.image.get_rect(topleft=(x, y))

    def _draw(self):
        img = self.image
        if self.kind == "ground":
            img.fill(BROWN)
            pygame.draw.rect(img, DARK_BROWN, img.get_rect(), 3)
            for i in range(0, TILE_SIZE, 10):
                pygame.draw.line(img, DARK_BROWN, (i, 0), (i, TILE_SIZE), 1)
        elif self.kind == "brick":
            img.fill(RED)
            pygame.draw.rect(img, DARK_RED, img.get_rect(), 2)
            for row in range(0, TILE_SIZE, 13):
                pygame.draw.line(img, DARK_RED, (0, row), (TILE_SIZE, row), 2)
        elif self.kind == "question":
            color = GOLD if not self.has_coin else GRAY
            img.fill(color)
            pygame.draw.rect(img, DARK_BROWN, img.get_rect(), 3)
            if self.has_coin:
                font = pygame.font.SysFont("arial", 22, bold=True)
                q = font.render("?", True, WHITE)
                img.blit(q, q.get_rect(center=(TILE_SIZE // 2, TILE_SIZE // 2)))
        elif self.kind == "spike":
            img.fill((0, 0, 0))
            img.set_colorkey((0, 0, 0))
            pygame.draw.polygon(img, GRAY, [(2, TILE_SIZE), (TILE_SIZE // 2, 6), (TILE_SIZE - 2, TILE_SIZE)])
            pygame.draw.polygon(img, (60, 60, 60), [(2, TILE_SIZE), (TILE_SIZE // 2, 6), (TILE_SIZE - 2, TILE_SIZE)], 2)

    def hit(self):
        if self.has_coin:
            self.has_coin = False
            self._draw()
            return True
        return False


class Coin(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.base_y = y
        self.timer = 0
        self.image = pygame.Surface((24, 24), pygame.SRCALPHA)
        pygame.draw.circle(self.image, GOLD, (12, 12), 11)
        pygame.draw.circle(self.image, YELLOW, (12, 12), 7)
        self.rect = self.image.get_rect(topleft=(x + 8, y + 8))
        self.collected = False

    def update(self):
        self.timer += 1
        self.rect.y = self.base_y + 8 + int(math.sin(self.timer * 0.1) * 4)


class Flag(pygame.sprite.Sprite):
    def __init__(self, x, y_top, height):
        super().__init__()
        self.image = pygame.Surface((TILE_SIZE, height), pygame.SRCALPHA)
        pygame.draw.line(self.image, GRAY, (6, 0), (6, height), 4)
        pygame.draw.polygon(self.image, GREEN, [(10, 4), (36, 14), (10, 24)])
        self.rect = self.image.get_rect(topleft=(x, y_top))


class Projectile(pygame.sprite.Sprite):
    def __init__(self, x, y, direction):
        super().__init__()
        self.image = pygame.Surface((16, 16), pygame.SRCALPHA)
        pygame.draw.circle(self.image, PURPLE, (8, 8), 8)
        self.rect = self.image.get_rect(center=(x, y))
        self.vx = direction * 6
        self.vy = -4
        self.gravity = 0.35

    def update(self):
        self.vy += self.gravity
        self.rect.x += self.vx
        self.rect.y += self.vy


class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.width, self.height = 30, 40
        self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.facing_right = True
        self._draw(running_frame=0)
        self.rect = self.image.get_rect(topleft=(x, y))
        self.vx = 0
        self.vy = 0
        self.on_ground = False
        self.lives = PLAYER_START_LIVES
        self.score = 0
        self.invincible = 0
        self.anim_timer = 0
        self.dead = False
        self.win_pose = False

    def _draw(self, running_frame=0):
        img = self.image
        img.fill((0, 0, 0, 0))
        # ноги (немного смещаются для анимации бега)
        leg_off = 4 if running_frame == 1 else 0
        pygame.draw.rect(img, DARK_BROWN, (4, 28 - 0, 8, 12 - leg_off))
        pygame.draw.rect(img, DARK_BROWN, (18, 28, 8, 12 - (4 - leg_off)))
        # тело (комбинезон)
        pygame.draw.rect(img, RED, (4, 14, 22, 16), border_radius=3)
        # голова
        pygame.draw.rect(img, SKIN, (6, 2, 18, 14), border_radius=4)
        # кепка
        pygame.draw.rect(img, DARK_RED, (4, 0, 22, 6), border_radius=2)
        pygame.draw.rect(img, DARK_RED, (2, 4, 10, 4))
        if not self.facing_right:
            img_flipped = pygame.transform.flip(img, True, False)
            img.blit(img_flipped, (0, 0))

    def handle_input(self, input_state):
        """input_state — словарь {'left': bool, 'right': bool, 'jump': bool}.
        Так игрок одинаково реагирует и на клавиатуру, и на сенсорное
        управление (виртуальный джойстик на Android) — game.py сам решает,
        откуда брать эти значения."""
        self.vx = 0
        if input_state.get("left"):
            self.vx = -PLAYER_SPEED
            self.facing_right = False
        if input_state.get("right"):
            self.vx = PLAYER_SPEED
            self.facing_right = True
        if input_state.get("jump") and self.on_ground:
            self.vy = PLAYER_JUMP
            self.on_ground = False

    def apply_physics(self, blocks):
        # Гравитация
        self.vy += GRAVITY
        if self.vy > MAX_FALL_SPEED:
            self.vy = MAX_FALL_SPEED

        # Движение по X с коллизией
        self.rect.x += self.vx
        for block in blocks:
            if self.rect.colliderect(block.rect):
                if block.kind == "spike":
                    continue
                if self.vx > 0:
                    self.rect.right = block.rect.left
                elif self.vx < 0:
                    self.rect.left = block.rect.right

        # Движение по Y с коллизией
        self.rect.y += self.vy
        self.on_ground = False
        for block in blocks:
            if self.rect.colliderect(block.rect):
                if block.kind == "spike":
                    continue
                if self.vy > 0:
                    self.rect.bottom = block.rect.top
                    self.vy = 0
                    self.on_ground = True
                elif self.vy < 0:
                    self.rect.top = block.rect.bottom
                    self.vy = 0
                    if block.kind == "question":
                        block.hit()

        if self.invincible > 0:
            self.invincible -= 1

        # Анимация
        if self.vx != 0 and self.on_ground:
            self.anim_timer += 1
            frame = (self.anim_timer // 6) % 2
        else:
            frame = 0
        self._draw(running_frame=frame)

    def take_hit(self):
        if self.invincible <= 0:
            self.lives -= 1
            self.invincible = INVINCIBLE_TIME
            self.vy = PLAYER_JUMP * 0.6
            return True
        return False


class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, patrol_range=120):
        super().__init__()
        self.image = pygame.Surface((32, 28), pygame.SRCALPHA)
        self._draw()
        self.rect = self.image.get_rect(topleft=(x, y))
        self.start_x = x
        self.patrol_range = patrol_range
        self.vx = -ENEMY_SPEED
        self.vy = 0
        self.alive = True
        self.squash_timer = 0

    def _draw(self):
        img = self.image
        pygame.draw.ellipse(img, DARK_BROWN, (0, 8, 32, 20))
        pygame.draw.ellipse(img, BROWN, (2, 10, 28, 16))
        pygame.draw.circle(img, BLACK, (8, 18), 3)
        pygame.draw.circle(img, BLACK, (24, 18), 3)
        pygame.draw.polygon(img, DARK_BROWN, [(0, 8), (6, 0), (10, 8)])
        pygame.draw.polygon(img, DARK_BROWN, [(32, 8), (26, 0), (22, 8)])

    def update(self, blocks):
        if not self.alive:
            return
        self.vy += GRAVITY
        if self.vy > MAX_FALL_SPEED:
            self.vy = MAX_FALL_SPEED

        self.rect.x += self.vx
        for block in blocks:
            if block.kind == "spike":
                continue
            if self.rect.colliderect(block.rect):
                if self.vx > 0:
                    self.rect.right = block.rect.left
                else:
                    self.rect.left = block.rect.right
                self.vx *= -1

        # Разворот на краю патруля
        if abs(self.rect.x - self.start_x) > self.patrol_range:
            self.vx *= -1

        self.rect.y += self.vy
        for block in blocks:
            if block.kind == "spike":
                continue
            if self.rect.colliderect(block.rect):
                if self.vy > 0:
                    self.rect.bottom = block.rect.top
                    self.vy = 0

    def stomp(self):
        self.alive = False


class Boss(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.width, self.height = 80, 90
        self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self._draw()
        self.rect = self.image.get_rect(topleft=(x, y))
        self.start_x = x
        self.hp = 3
        self.max_hp = 3
        self.vx = -3
        self.vy = 0
        self.alive = True
        self.attack_timer = 0
        self.hit_flash = 0
        self.defeated_timer = 0

    def _draw(self):
        img = self.image
        img.fill((0, 0, 0, 0))
        color = (255, 255, 255) if self.hit_flash > 0 else PURPLE
        pygame.draw.ellipse(img, color, (0, 20, 80, 70))
        pygame.draw.circle(img, color, (40, 22), 26)
        pygame.draw.circle(img, WHITE, (28, 16), 7)
        pygame.draw.circle(img, WHITE, (52, 16), 7)
        pygame.draw.circle(img, BLACK, (28, 16), 3)
        pygame.draw.circle(img, BLACK, (52, 16), 3)
        pygame.draw.polygon(img, DARK_RED if self.hit_flash <= 0 else RED, [(15, 30), (65, 30), (40, 45)])

    def update(self, blocks, floor_y):
        if not self.alive:
            return
        if self.hit_flash > 0:
            self.hit_flash -= 1
            self._draw()
        self.rect.x += self.vx
        if abs(self.rect.x - self.start_x) > 200:
            self.vx *= -1
            self.start_x = self.rect.x if abs(self.rect.x - self.start_x) > 200 else self.start_x
        if self.rect.left < 0 or self.rect.right > SCREEN_WIDTH * 3:
            self.vx *= -1
        self.attack_timer += 1

    def take_damage(self):
        self.hp -= 1
        self.hit_flash = 15
        self._draw()
        if self.hp <= 0:
            self.alive = False
            return True
        return False
