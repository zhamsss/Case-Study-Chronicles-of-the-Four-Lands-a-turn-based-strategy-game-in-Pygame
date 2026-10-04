import math
from pathlib import Path

import pygame

from game.config import (
    HEX_SIZE,
    MIN_ZOOM,
    MAX_ZOOM,
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
)

SPRITE_DIR = (
    Path(__file__).resolve().parent.parent / "assets" / "sprites"
)

GREEN = (0, 255, 120)
RED = (255, 80, 80)
YELLOW = (255, 255, 0)


def load_sprite(name):
    """Загружает спрайт; если файла нет — рисует розовую заглушку."""

    try:
        return pygame.image.load(
            str(SPRITE_DIR / name)
        ).convert_alpha()

    except (pygame.error, FileNotFoundError):

        surface = pygame.Surface((64, 64), pygame.SRCALPHA)

        pygame.draw.circle(
            surface, (255, 0, 255), (32, 32), 28
        )

        return surface


class GridRenderer:

    def __init__(self):

        self.zoom = 1.0

        names = {
            "gray": "hex_gray.png",
            "red": "hex_red.png",
            "blue": "hex_blue.png",
            "green": "hex_green.png",
            "purple": "hex_purple.png",
            "capital": "capital.png",
            "tree": "tree.png",
            "tombstone": "tombstone.png",
            "house": "house.png",
            "tower1": "castle_level1.png",
            "tower2": "castle_level2.png",
            "unit1": "1level_unit.png",
            "unit2": "2level_unit.png",
            "unit3": "3level_unit.png",
            "unit4": "4level_unit.png",
        }

        self.originals = {
            key: load_sprite(file)
            for key, file in names.items()
        }

        self.rescale()

    # ------------------------------------------------------------------
    # Масштаб
    # ------------------------------------------------------------------

    def _scaled(self, key, factor):

        size = max(4, int(self.hex_px * factor))

        return pygame.transform.smoothscale(
            self.originals[key],
            (size, size)
        )

    def rescale(self):

        self.hex_px = max(12, round(HEX_SIZE * self.zoom))

        self.hex_sprites = {
            None: self._scaled("gray", 1),
            1: self._scaled("red", 1),
            2: self._scaled("blue", 1),
            3: self._scaled("green", 1),
            4: self._scaled("purple", 1),
        }

        self.capital_sprite = self._scaled("capital", 0.79)
        self.tree_sprite = self._scaled("tree", 0.8)
        self.tombstone_sprite = self._scaled("tombstone", 0.7)
        self.house_sprite = self._scaled("house", 0.75)
        self.tower_sprites = {
            1: self._scaled("tower1", 0.8),
            2: self._scaled("tower2", 0.8),
        }

        self.unit_sprites = {}
        self.unit_sprites_dim = {}

        for level in (1, 2, 3, 4):

            sprite = self._scaled(f"unit{level}", 0.86)

            dim = sprite.copy()
            dim.fill(
                (255, 255, 255, 110),
                special_flags=pygame.BLEND_RGBA_MULT
            )

            self.unit_sprites[level] = sprite
            self.unit_sprites_dim[level] = dim

    def reset_zoom(self):

        self.zoom = 1.0
        self.rescale()

    def set_zoom(self, new_zoom, mouse_pos, camera_x, camera_y):
        """Меняет зум вокруг курсора. Возвращает новую позицию камеры."""

        new_zoom = max(MIN_ZOOM, min(MAX_ZOOM, new_zoom))

        old_px = self.hex_px

        self.zoom = new_zoom
        self.rescale()

        k = self.hex_px / old_px

        mx, my = mouse_pos

        return (
            mx - (mx - camera_x) * k,
            my - (my - camera_y) * k
        )

    # ------------------------------------------------------------------
    # Координаты
    # ------------------------------------------------------------------

    def hex_to_pixel(self, q, r, camera_x, camera_y):

        x = q * self.hex_px

        if r % 2:
            x += self.hex_px / 2

        y = r * self.hex_px * 0.75

        return x + camera_x, y + camera_y

    def get_tile_at_mouse(self, mouse_pos, board, camera_x, camera_y):

        mx, my = mouse_pos

        nearest_tile = None
        nearest_distance = 999999

        for tile in board.tiles.values():

            x, y = self.hex_to_pixel(
                tile.q, tile.r, camera_x, camera_y
            )

            distance = math.hypot(mx - x, my - y)

            if distance < nearest_distance:
                nearest_distance = distance
                nearest_tile = tile

        if nearest_distance <= self.hex_px * 0.58:
            return nearest_tile

        return None

    # ------------------------------------------------------------------
    # Отрисовка
    # ------------------------------------------------------------------

    def draw_board(
        self,
        screen,
        board,
        camera_x,
        camera_y,
        selected_unit_tile,
        highlight,
        current_player_id
    ):

        margin = self.hex_px

        for tile in board.tiles.values():

            x, y = self.hex_to_pixel(
                tile.q, tile.r, camera_x, camera_y
            )

            if (
                x < -margin or x > SCREEN_WIDTH + margin
                or y < -margin or y > SCREEN_HEIGHT + margin
            ):
                continue

            tile.screen_x = x
            tile.screen_y = y

            self._draw_tile(
                screen,
                tile,
                x,
                y,
                selected_unit_tile,
                highlight,
                current_player_id
            )

    def _blit_center(self, screen, sprite, x, y):

        screen.blit(sprite, sprite.get_rect(center=(x, y)))

    def _draw_tile(
        self,
        screen,
        tile,
        x,
        y,
        selected_unit_tile,
        highlight,
        current_player_id
    ):

        px = self.hex_px

        self._blit_center(
            screen, self.hex_sprites[tile.owner], x, y
        )

        if tile.tree:
            self._blit_center(screen, self.tree_sprite, x, y)

        if tile.tombstone:
            self._blit_center(screen, self.tombstone_sprite, x, y)

        if tile.house:
            self._blit_center(screen, self.house_sprite, x, y)

        if tile.tower_level:
            self._blit_center(
                screen, self.tower_sprites[tile.tower_level], x, y
            )

        if tile.capital:
            self._blit_center(screen, self.capital_sprite, x, y)

        if tile.unit:

            level = tile.unit.level

            if (
                tile.unit.moved
                and tile.owner == current_player_id
            ):
                sprite = self.unit_sprites_dim[level]
            else:
                sprite = self.unit_sprites[level]

            self._blit_center(screen, sprite, x, y)

        ix, iy = int(x), int(y)

        if tile in highlight:

            enemy = (
                tile.owner is not None
                and tile.owner != current_player_id
            )

            if tile.unit or enemy:

                pygame.draw.circle(
                    screen,
                    RED if enemy else GREEN,
                    (ix, iy),
                    int(px * 0.42),
                    3
                )

            else:

                pygame.draw.circle(
                    screen, GREEN, (ix, iy), max(3, int(px * 0.2))
                )

        if tile.selected:

            pygame.draw.circle(
                screen, YELLOW, (ix, iy), int(px * 0.5), 3
            )

        if tile is selected_unit_tile:

            pygame.draw.circle(
                screen, YELLOW, (ix, iy), int(px * 0.6), 4
            )
