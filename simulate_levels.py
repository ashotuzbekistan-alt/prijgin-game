"""
Headless-симулятор с честной AABB-коллизией (как в entities.Player), без
графики и без pygame — только математика прямоугольников. Проверяет, что
каждый уровень реально проходим для простого ИИ-игрока (идёт вправо,
прыгает на препятствиях).
"""
from levels_generated import ALL_LEVELS
from settings import TILE_SIZE, GRAVITY, PLAYER_SPEED, PLAYER_JUMP, MAX_FALL_SPEED


class Rect:
    __slots__ = ("x", "y", "w", "h")

    def __init__(self, x, y, w, h):
        self.x, self.y, self.w, self.h = x, y, w, h

    @property
    def left(self): return self.x
    @property
    def right(self): return self.x + self.w
    @property
    def top(self): return self.y
    @property
    def bottom(self): return self.y + self.h

    def colliderect(self, other):
        return (self.left < other.right and self.right > other.left and
                self.top < other.bottom and self.bottom > other.top)


def build_blocks(tile_map):
    blocks = []      # список (rect, kind)
    flag_x = None
    boss_x = None
    start_x, start_y = 1, len(tile_map) - 2

    for ry, row in enumerate(tile_map):
        for cx, ch in enumerate(row):
            if ch in ("X", "B", "?"):
                blocks.append((Rect(cx * TILE_SIZE, ry * TILE_SIZE, TILE_SIZE, TILE_SIZE), "solid"))
            elif ch == "^":
                blocks.append((Rect(cx * TILE_SIZE, ry * TILE_SIZE, TILE_SIZE, TILE_SIZE), "spike"))
            elif ch == "P":
                start_x, start_y = cx, ry
            elif ch == "F":
                flag_x = cx
            elif ch == "W":
                boss_x = cx

    target_x = (flag_x if flag_x is not None else boss_x) * TILE_SIZE
    return blocks, start_x * TILE_SIZE, start_y * TILE_SIZE, target_x


def simulate(tile_map, max_frames=8000):
    blocks, start_px, start_py, target_x = build_blocks(tile_map)
    level_height_px = len(tile_map) * TILE_SIZE

    # Тайловые множества — для надёжного "взгляда вперёд" ИИ (отдельно от
    # честной AABB-физики движения, которая работает точно как в игре)
    solid_tiles = set()
    spike_tiles = set()
    for ry, row in enumerate(tile_map):
        for cx, ch in enumerate(row):
            if ch in ("X", "B", "?"):
                solid_tiles.add((cx, ry))
            elif ch == "^":
                spike_tiles.add((cx, ry))
    floor_row = len(tile_map) - 1
    spike_row = floor_row - 1

    w_px, h_px = 30, 40
    player = Rect(start_px, start_py, w_px, h_px)
    vx = 0.0
    vy = 0.0
    on_ground = False

    for frame in range(max_frames):
        # ИИ смотрит на 3 тайла вперёд по тайловой сетке (независимо от
        # точного пиксельного смещения — надёжнее, чем rect-заглядывание)
        foot_tile_x = int((player.x + w_px / 2) // TILE_SIZE)
        need_jump = False
        for dx in range(0, 4):
            cx = foot_tile_x + dx
            if (cx, floor_row) not in solid_tiles:
                need_jump = True
                break
            if (cx, spike_row) in spike_tiles:
                need_jump = True
                break

        if need_jump and on_ground:
            vy = PLAYER_JUMP
            on_ground = False

        vx = PLAYER_SPEED
        vy += GRAVITY
        if vy > MAX_FALL_SPEED:
            vy = MAX_FALL_SPEED

        player.x += vx
        for rect, kind in blocks:
            if kind == "spike":
                continue
            if player.colliderect(rect):
                if vx > 0:
                    player.x = rect.left - player.w
                elif vx < 0:
                    player.x = rect.right

        player.y += vy
        on_ground = False
        for rect, kind in blocks:
            if kind == "spike":
                continue
            if player.colliderect(rect):
                if vy > 0:
                    player.y = rect.top - player.h
                    vy = 0
                    on_ground = True
                elif vy < 0:
                    player.y = rect.bottom
                    vy = 0

        for rect, kind in blocks:
            if kind == "spike" and player.colliderect(rect):
                return False, f"погиб на шипе, кадр {frame}, x={player.x:.0f}"

        if player.top > level_height_px + 200:
            return False, f"провалился в пропасть, кадр {frame}, x={player.x:.0f}"

        if player.x >= target_x:
            return True, f"дошёл до цели за {frame} кадров"

    return False, "не дошёл за отведённое время (застрял)"


if __name__ == "__main__":
    all_ok = True
    for i, level in enumerate(ALL_LEVELS, start=1):
        ok, msg = simulate(level)
        status = "OK" if ok else "FAIL"
        if not ok:
            all_ok = False
        print(f"Уровень {i:2d}: {status:4s} — {msg}")

    print()
    print("ВСЕ УРОВНИ ПРОХОДИМЫ" if all_ok else "ЕСТЬ НЕПРОХОДИМЫЕ УРОВНИ!")
