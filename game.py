"""Главный игровой класс: меню, уровни, бой с боссом, HUD."""
import os
import sys
import pygame
from settings import *
from world import Level
from entities import Player, Projectile
from levels import ALL_LEVELS, BOSS_LEVEL_INDICES

# python-for-android выставляет эту переменную окружения — по ней понимаем,
# что запущены на телефоне, и включаем полноэкранный режим под реальный
# размер экрана устройства вместо фиксированного окна для ПК.
ON_ANDROID = "ANDROID_ARGUMENT" in os.environ


class Game:
    def __init__(self):
        pygame.init()
        if ON_ANDROID:
            info = pygame.display.Info()
            global SCREEN_WIDTH, SCREEN_HEIGHT
            SCREEN_WIDTH, SCREEN_HEIGHT = info.current_w, info.current_h
            self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        self.big_font = pygame.font.SysFont("arial", 56, bold=True)
        self.mid_font = pygame.font.SysFont("arial", 32, bold=True)
        self.small_font = pygame.font.SysFont("arial", 22)

        self.state = STATE_MENU
        self.level_index = 0
        self.level = None
        self.player = None
        self.camera_x = 0
        self.projectiles = pygame.sprite.Group()
        self.message_timer = 0
        self.message_text = ""
        self.total_score = 0

        # ---- Сенсорное управление (виртуальный джойстик + кнопка прыжка) ----
        # Работает и от мыши (для проверки на компьютере), и от пальца на
        # телефоне — pygame.FINGERDOWN/MOTION/UP это отдельные события,
        # которые на Android приходят от настоящих касаний экрана.
        self.joystick_center = (90, SCREEN_HEIGHT - 100)
        self.joystick_radius = 55
        self.joystick_knob = [0, 0]  # текущее смещение ручки джойстика
        self.jump_button_center = (SCREEN_WIDTH - 90, SCREEN_HEIGHT - 100)
        self.jump_button_radius = 50
        self.active_pointers = {}  # id -> "joystick" | "jump"
        self.touch_left = False
        self.touch_right = False
        self.touch_jump = False

    # ---------- Загрузка уровня ----------
    def load_level(self, index):
        self.level_index = index
        is_boss = index in BOSS_LEVEL_INDICES
        self.level = Level(ALL_LEVELS[index], is_boss_level=is_boss)
        if is_boss:
            # Чем дальше по игре, тем крепче босс (+1 HP за каждый следующий)
            boss_number = BOSS_LEVEL_INDICES.index(index) + 1
            self.level.boss.hp = 2 + boss_number
            self.level.boss.max_hp = self.level.boss.hp
        px, py = self.level.player_start
        keep_score = self.player.score if self.player else 0
        keep_lives = self.player.lives if self.player else PLAYER_START_LIVES
        self.player = Player(px, py)
        self.player.score = keep_score
        self.player.lives = keep_lives
        self.camera_x = 0
        self.projectiles.empty()
        self.state = STATE_BOSS if is_boss else STATE_PLAYING

    def start_new_game(self):
        self.player = None
        self.load_level(0)

    # ---------- Основной цикл ----------
    def run(self):
        while True:
            dt = self.clock.tick(FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    self.handle_keydown(event.key)
                self.handle_touch_event(event)

            keys = pygame.key.get_pressed()
            input_state = {
                "left": keys[pygame.K_LEFT] or keys[pygame.K_a] or self.touch_left,
                "right": keys[pygame.K_RIGHT] or keys[pygame.K_d] or self.touch_right,
                "jump": keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_w] or self.touch_jump,
            }

            if self.state == STATE_MENU:
                self.draw_menu()
            elif self.state in (STATE_PLAYING, STATE_BOSS):
                self.update_playing(input_state)
                self.draw_playing()
                self.draw_touch_controls()
            elif self.state == STATE_LEVEL_COMPLETE:
                self.draw_center_message("Уровень пройден!", "Нажми ENTER для продолжения")
            elif self.state == STATE_GAME_OVER:
                self.draw_center_message("ИГРА ОКОНЧЕНА", "Нажми ENTER чтобы начать заново")
            elif self.state == STATE_WIN:
                self.draw_center_message("ПОБЕДА! Все боссы повержены!", "Нажми ENTER для меню")

            pygame.display.flip()

    # ---------- Сенсорное управление ----------
    def handle_touch_event(self, event):
        # Мышь — для проверки на компьютере. Палец (FINGER*) — на Android
        # координаты приходят нормализованными (0..1), переводим в пиксели.
        if event.type == pygame.MOUSEBUTTONDOWN:
            self._touch_down("mouse", event.pos)
        elif event.type == pygame.MOUSEBUTTONUP:
            self._touch_up("mouse")
        elif event.type == pygame.MOUSEMOTION:
            self._touch_move("mouse", event.pos)
        elif event.type == pygame.FINGERDOWN:
            pos = (event.x * SCREEN_WIDTH, event.y * SCREEN_HEIGHT)
            self._touch_down(event.finger_id, pos)
        elif event.type == pygame.FINGERUP:
            self._touch_up(event.finger_id)
        elif event.type == pygame.FINGERMOTION:
            pos = (event.x * SCREEN_WIDTH, event.y * SCREEN_HEIGHT)
            self._touch_move(event.finger_id, pos)

    def _dist(self, a, b):
        return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5

    def _touch_down(self, pointer_id, pos):
        if self._dist(pos, self.joystick_center) <= self.joystick_radius * 1.8:
            self.active_pointers[pointer_id] = "joystick"
            self._touch_move(pointer_id, pos)
        elif self._dist(pos, self.jump_button_center) <= self.jump_button_radius * 1.4:
            self.active_pointers[pointer_id] = "jump"
            self.touch_jump = True

    def _touch_move(self, pointer_id, pos):
        role = self.active_pointers.get(pointer_id)
        if role == "joystick":
            dx = pos[0] - self.joystick_center[0]
            dy = pos[1] - self.joystick_center[1]
            dist = max(1.0, (dx * dx + dy * dy) ** 0.5)
            clamped = min(dist, self.joystick_radius)
            self.joystick_knob = [dx / dist * clamped, dy / dist * clamped]
            self.touch_left = dx < -12
            self.touch_right = dx > 12

    def _touch_up(self, pointer_id):
        role = self.active_pointers.pop(pointer_id, None)
        if role == "joystick":
            self.joystick_knob = [0, 0]
            self.touch_left = False
            self.touch_right = False
        elif role == "jump":
            self.touch_jump = False

    def draw_touch_controls(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        # Джойстик
        jx, jy = self.joystick_center
        pygame.draw.circle(overlay, (255, 255, 255, 60), (jx, jy), self.joystick_radius)
        pygame.draw.circle(overlay, (255, 255, 255, 130),
                            (jx + self.joystick_knob[0], jy + self.joystick_knob[1]), 26)
        # Кнопка прыжка
        bx, by = self.jump_button_center
        color = (255, 255, 255, 160) if self.touch_jump else (255, 255, 255, 70)
        pygame.draw.circle(overlay, color, (bx, by), self.jump_button_radius)
        label = self.small_font.render("ПРЫЖОК", True, (255, 255, 255, 220))
        overlay.blit(label, label.get_rect(center=(bx, by)))
        self.screen.blit(overlay, (0, 0))

    def handle_keydown(self, key):
        if self.state == STATE_MENU and key in (pygame.K_RETURN, pygame.K_SPACE):
            self.start_new_game()
        elif self.state == STATE_LEVEL_COMPLETE and key == pygame.K_RETURN:
            self.load_level(self.level_index + 1)
        elif self.state == STATE_GAME_OVER and key == pygame.K_RETURN:
            self.state = STATE_MENU
        elif self.state == STATE_WIN and key == pygame.K_RETURN:
            self.state = STATE_MENU

    # ---------- Логика игрового кадра ----------
    def update_playing(self, input_state):
        self.player.handle_input(input_state)
        self.player.apply_physics(self.level.blocks)

        # Падение в пропасть
        if self.player.rect.top > self.level.height + 200:
            self.kill_player()
            return

        # Монеты
        for coin in list(self.level.coins):
            if self.player.rect.colliderect(coin.rect):
                coin.kill()
                self.player.score += 100
        self.level.coins.update()

        # Шипы
        for spike in self.level.spikes:
            if self.player.rect.colliderect(spike.rect):
                if self.player.take_hit():
                    if self.player.lives <= 0:
                        self.game_over()
                        return

        # Враги
        for enemy in list(self.level.enemies):
            enemy.update(self.level.blocks)
            if enemy.alive and self.player.rect.colliderect(enemy.rect):
                if self.player.vy > 0 and self.player.rect.bottom - enemy.rect.top < 20:
                    enemy.stomp()
                    self.player.vy = PLAYER_JUMP * 0.6
                    self.player.score += 200
                else:
                    if self.player.take_hit():
                        if self.player.lives <= 0:
                            self.game_over()
                            return
        for enemy in list(self.level.enemies):
            if not enemy.alive:
                enemy.kill()

        # Флаг (конец уровня)
        if self.level.flag and self.player.rect.colliderect(self.level.flag.rect):
            self.total_score = self.player.score
            self.state = STATE_LEVEL_COMPLETE

        # Босс
        if self.level.is_boss_level and self.level.boss and self.level.boss.alive:
            boss = self.level.boss
            boss.update(self.level.blocks, self.level.height)
            boss.attack_timer += 0
            if boss.attack_timer % 90 == 0 and boss.attack_timer > 0:
                direction = -1 if self.player.rect.centerx < boss.rect.centerx else 1
                self.projectiles.add(Projectile(boss.rect.centerx, boss.rect.centery, direction))

            if self.player.rect.colliderect(boss.rect):
                if self.player.vy > 0 and self.player.rect.bottom - boss.rect.top < 25:
                    boss.take_damage()
                    self.player.vy = PLAYER_JUMP * 0.7
                    self.player.score += 500
                    if not boss.alive:
                        if self.level_index == len(ALL_LEVELS) - 1:
                            self.state = STATE_WIN
                        else:
                            self.total_score = self.player.score
                            self.state = STATE_LEVEL_COMPLETE
                else:
                    if self.player.take_hit():
                        if self.player.lives <= 0:
                            self.game_over()
                            return

            self.projectiles.update()
            for proj in list(self.projectiles):
                if proj.rect.colliderect(self.player.rect):
                    proj.kill()
                    if self.player.take_hit():
                        if self.player.lives <= 0:
                            self.game_over()
                            return
                if proj.rect.x < -50 or proj.rect.x > self.level.width + 50:
                    proj.kill()

        # Камера
        target_cam = self.player.rect.centerx - SCREEN_WIDTH // 2
        target_cam = max(0, min(target_cam, max(0, self.level.width - SCREEN_WIDTH)))
        self.camera_x += (target_cam - self.camera_x) * 0.15

    def kill_player(self):
        self.player.lives -= 1
        if self.player.lives <= 0:
            self.game_over()
        else:
            px, py = self.level.player_start
            self.player.rect.topleft = (px, py)
            self.player.vy = 0
            self.player.invincible = INVINCIBLE_TIME

    def game_over(self):
        self.state = STATE_GAME_OVER

    # ---------- Отрисовка ----------
    def draw_menu(self):
        self.screen.fill(SKY_BLUE)
        title = self.big_font.render(TITLE, True, WHITE)
        shadow = self.big_font.render(TITLE, True, BLACK)
        self.screen.blit(shadow, shadow.get_rect(center=(SCREEN_WIDTH // 2 + 3, 163)))
        self.screen.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, 160)))

        hint = self.mid_font.render("Нажми ENTER чтобы начать", True, WHITE)
        self.screen.blit(hint, hint.get_rect(center=(SCREEN_WIDTH // 2, 320)))

        controls = [
            "Стрелки / A-D — движение",
            "ПРОБЕЛ / W / ВВЕРХ — прыжок",
            "Прыгни на врага, чтобы победить его",
            "Собирай монетки, дойди до флага",
        ]
        for i, line in enumerate(controls):
            t = self.small_font.render(line, True, WHITE)
            self.screen.blit(t, t.get_rect(center=(SCREEN_WIDTH // 2, 400 + i * 30)))

        pygame.draw.rect(self.screen, BROWN, (0, SCREEN_HEIGHT - 40, SCREEN_WIDTH, 40))

    def draw_playing(self):
        self.screen.fill(SKY_BLUE)
        cam = int(self.camera_x)

        for block in self.level.blocks:
            self.screen.blit(block.image, (block.rect.x - cam, block.rect.y))
        for coin in self.level.coins:
            self.screen.blit(coin.image, (coin.rect.x - cam, coin.rect.y))
        for enemy in self.level.enemies:
            self.screen.blit(enemy.image, (enemy.rect.x - cam, enemy.rect.y))
        if self.level.flag:
            f = self.level.flag
            self.screen.blit(f.image, (f.rect.x - cam, f.rect.y))
        if self.level.is_boss_level and self.level.boss and self.level.boss.alive:
            boss = self.level.boss
            self.screen.blit(boss.image, (boss.rect.x - cam, boss.rect.y))
            self.draw_boss_health(boss)
        for proj in self.projectiles:
            self.screen.blit(proj.image, (proj.rect.x - cam, proj.rect.y))

        if self.player.invincible == 0 or (self.player.invincible // 4) % 2 == 0:
            self.screen.blit(self.player.image, (self.player.rect.x - cam, self.player.rect.y))

        self.draw_hud()

    def draw_boss_health(self, boss):
        bar_w = 300
        x = SCREEN_WIDTH // 2 - bar_w // 2
        y = 20
        pygame.draw.rect(self.screen, BLACK, (x - 3, y - 3, bar_w + 6, 26), border_radius=6)
        pygame.draw.rect(self.screen, GRAY, (x, y, bar_w, 20), border_radius=4)
        ratio = max(0, boss.hp / boss.max_hp)
        pygame.draw.rect(self.screen, RED, (x, y, int(bar_w * ratio), 20), border_radius=4)
        label = self.small_font.render("БОСС", True, WHITE)
        self.screen.blit(label, label.get_rect(center=(SCREEN_WIDTH // 2, y - 14)))

    def draw_hud(self):
        pygame.draw.rect(self.screen, (0, 0, 0, 120), (0, 0, SCREEN_WIDTH, 36))
        score_text = self.small_font.render(f"Очки: {self.player.score}", True, WHITE)
        lives_text = self.small_font.render(f"Жизни: {self.player.lives}", True, WHITE)
        level_text = self.small_font.render(f"Уровень: {self.level_index + 1}/{len(ALL_LEVELS)}", True, WHITE)
        self.screen.blit(score_text, (10, 8))
        self.screen.blit(lives_text, (250, 8))
        self.screen.blit(level_text, (450, 8))

    def draw_center_message(self, big_text, small_text):
        self.screen.fill((20, 20, 30))
        t1 = self.big_font.render(big_text, True, WHITE)
        t2 = self.mid_font.render(small_text, True, YELLOW)
        self.screen.blit(t1, t1.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 40)))
        self.screen.blit(t2, t2.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 30)))
        if self.player:
            score_text = self.small_font.render(f"Итоговый счёт: {self.player.score}", True, WHITE)
            self.screen.blit(score_text, score_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 80)))
