"""
Генератор 30 уровней (v2, сегментный подход).

Идея: уровень строится не случайной точечной расстановкой, а
последовательностью СЕГМЕНТОВ слева направо:
  - 'flat'  — ровный целый пол длиной 6-10 тайлов (безопасная зона,
              тут может быть платформа сверху, монетки, враг)
  - 'gap'   — провал в полу шириной 1-2 тайла
  - 'spike' — один тайл шипов, лежащих НАД целым полом

Между любыми двумя опасными сегментами (gap/spike) всегда идёт flat-сегмент
длиной минимум 6 тайлов — этого с большим запасом хватает, чтобв игрок
успел приземлиться после прыжка и разбежаться для следующего.

Прыжок игрока при текущей физике (PLAYER_SPEED=5, PLAYER_JUMP=-16,
GRAVITY=0.8) покрывает по горизонтали ~5 тайлов — с запасом хватает на
провалы шириной 1-2 тайла.

Результат проверяется симулятором simulate_levels.py (честная AABB-физика,
как в самой игре) перед тем, как использоваться.
"""
import random

HEIGHT = 9
FLOOR_ROW = HEIGHT - 1
SPIKE_ROW = FLOOR_ROW - 1

BOSS_LEVEL_NUMBERS = {5, 10, 15, 20, 25, 30}  # 1-indexed номера уровней с боссом


def make_boss_level(level_num):
    width = 28
    rows = [["." for _ in range(width)] for _ in range(HEIGHT)]
    for x in range(width):
        rows[FLOOR_ROW][x] = "X"
    rows[FLOOR_ROW - 1][2] = "P"
    rows[FLOOR_ROW - 1][width - 6] = "W"
    return ["".join(r) for r in rows]


def build_segments(level_num, rng):
    difficulty = level_num / 30.0
    n_hazards = 4 + int(difficulty * 8)  # от 4 до 12 препятствий

    segments = [("flat", 7)]  # безопасный старт
    for _ in range(n_hazards):
        kind = rng.choice(["gap", "gap", "spike"])
        width = rng.choice([1, 1, 2]) if kind == "gap" else 1
        segments.append((kind, width))
        segments.append(("flat", rng.randint(9, 13)))
    segments.append(("flat", 5))  # безопасный финиш
    return segments


def make_normal_level(level_num, rng):
    segments = build_segments(level_num, rng)
    width = sum(length for _, length in segments)
    rows = [["." for _ in range(width)] for _ in range(HEIGHT)]
    for x in range(width):
        rows[FLOOR_ROW][x] = "X"

    flat_zones = []  # (start, end) — целые участки пола, куда можно класть платформы/врагов
    cursor = 0
    for kind, length in segments:
        start, end = cursor, cursor + length
        if kind == "gap":
            for x in range(start, end):
                rows[FLOOR_ROW][x] = "."
        elif kind == "spike":
            for x in range(start, end):
                rows[SPIKE_ROW][x] = "^"
        else:
            flat_zones.append((start, end))
        cursor = end

    # --- Платформы с монетками/блоками — только в безопасных flat-зонах,
    # с отступом от краёв зоны, чтобы не пересекаться с траекторией прыжка
    # игрока сразу после соседнего препятствия ---
    difficulty = level_num / 30.0
    LANDING_MARGIN = 3  # тайлов запаса на приземление/разбег с каждой стороны
    for start, end in flat_zones:
        usable_start = start + LANDING_MARGIN
        usable_end = end - LANDING_MARGIN
        if usable_end - usable_start < 3:
            continue
        if rng.random() < 0.5 + difficulty * 0.3:
            plat_row = rng.choice([FLOOR_ROW - 3, FLOOR_ROW - 4])
            plat_w = min(usable_end - usable_start, rng.randint(3, 5))
            plat_start = rng.randint(usable_start, usable_end - plat_w)
            for x in range(plat_start, plat_start + plat_w):
                if 0 <= plat_row < HEIGHT and rows[plat_row][x] == ".":
                    rows[plat_row][x] = rng.choice(["X", "X", "B", "?"])
            if plat_row - 1 >= 0:
                for x in range(plat_start, plat_start + plat_w):
                    if rng.random() < 0.6:
                        rows[plat_row - 1][x] = "C"

    # --- Свободные монетки в воздухе (чисто декоративные, не мешают проходу) ---
    for _ in range(4 + int(difficulty * 4)):
        x = rng.randint(3, width - 4)
        y = rng.randint(2, FLOOR_ROW - 3)
        if rows[y][x] == ".":
            rows[y][x] = "C"

    # --- Враги — только в безопасных flat-зонах, не на первом/последнем тайле зоны ---
    n_enemies = 2 + int(difficulty * 6)
    placed = 0
    eligible_zones = [z for z in flat_zones if z[1] - z[0] >= 6]
    attempts = 0
    while placed < n_enemies and eligible_zones and attempts < 200:
        attempts += 1
        start, end = rng.choice(eligible_zones)
        x = rng.randint(start + 2, end - 2)
        if rows[FLOOR_ROW - 1][x] == ".":
            rows[FLOOR_ROW - 1][x] = "E"
            placed += 1

    # --- Старт и финиш (внутри первой и последней flat-зоны) ---
    first_start, _ = flat_zones[0]
    _, last_end = flat_zones[-1]
    rows[FLOOR_ROW - 1][first_start + 1] = "P"
    rows[FLOOR_ROW - 1][last_end - 2] = "F"

    return ["".join(r) for r in rows]


def generate_all_levels():
    levels = []
    rng = random.Random(2026)
    for level_num in range(1, 31):
        if level_num in BOSS_LEVEL_NUMBERS:
            levels.append(make_boss_level(level_num))
        else:
            levels.append(make_normal_level(level_num, rng))
    return levels


def validate_level(tile_map):
    joined = "".join(tile_map)
    assert "P" in joined, "нет старта игрока"
    assert ("F" in joined) or ("W" in joined), "нет финиша/босса"
    return True


if __name__ == "__main__":
    levels = generate_all_levels()
    for lvl in levels:
        validate_level(lvl)

    print('"""Автоматически сгенерированные 30 уровней (см. level_generator.py)."""\n')
    print("ALL_LEVELS = [")
    for lvl in levels:
        print("    [")
        for row in lvl:
            print(f"        {row!r},")
        print("    ],")
    print("]")
    print()
    print(f"BOSS_LEVEL_INDICES = {sorted(n - 1 for n in BOSS_LEVEL_NUMBERS)}  # 0-based")
