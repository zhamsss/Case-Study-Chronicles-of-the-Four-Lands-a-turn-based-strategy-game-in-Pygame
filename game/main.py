import sys
from pathlib import Path

# Чтобы работало и `python game/main.py`, и `python -m game.main`
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pygame

from game.config import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    FPS,
    GAME_TITLE,
    BACKGROUND_COLOR,
    GRID_OFFSET_X,
    GRID_OFFSET_Y,
    PANEL_X,
    CAMERA_SPEED,
    ZOOM_STEP,
    PLAYER_COLORS,
)
from game.logic.board import Board
from game.logic.game_state import GameState
from game.ui.grid_renderer import GridRenderer
from game.ui.panel import Panel


class App:

    def __init__(self):

        pygame.init()

        self.screen = pygame.display.set_mode(
            (SCREEN_WIDTH, SCREEN_HEIGHT)
        )

        pygame.display.set_caption(GAME_TITLE)

        self.clock = pygame.time.Clock()

        self.big_font = pygame.font.Font(None, 80)
        self.font = pygame.font.Font(None, 36)

        self.renderer = GridRenderer()
        self.panel = Panel(PANEL_X)

        self.new_game()

    # ------------------------------------------------------------------
    # Состояние
    # ------------------------------------------------------------------

    def new_game(self):

        self.board = Board()
        self.game_state = GameState()

        self.renderer.reset_zoom()

        self.camera_x = GRID_OFFSET_X
        self.camera_y = GRID_OFFSET_Y

        self.selected_tile = None
        self.selected_unit_tile = None
        self.reachable = set()

        self.place_item = None
        self.place_region = None
        self.place_targets = set()

    @property
    def current_id(self):
        return self.game_state.current_player.player_id

    def set_selected(self, tile):

        if self.selected_tile:
            self.selected_tile.selected = False

        self.selected_tile = tile

        if tile:
            tile.selected = True

    def clear_unit(self):

        self.selected_unit_tile = None
        self.reachable = set()

    def cancel_place(self):

        self.place_item = None
        self.place_region = None
        self.place_targets = set()

    def active_region(self):
        """Регион, с которым работает панель (золото, покупки)."""

        if self.place_item:
            return self.place_region

        tile = self.selected_tile

        if tile and tile.owner == self.current_id:

            region = self.board.region_of(tile)

            if region:
                return region

        mine = self.board.regions_of(self.current_id)

        if mine:
            return max(mine, key=lambda r: len(r.tiles))

        return None

    def after_action(self):

        tiles = self.board.tiles.values()

        self.game_state.update_alive(tiles)
        self.game_state.check_winner(tiles)

    def end_turn(self):

        self.cancel_place()
        self.clear_unit()
        self.set_selected(None)

        self.game_state.update_alive(self.board.tiles.values())

        new_round = self.game_state.end_turn()

        if new_round:
            self.board.grow_trees()

        self.board.start_turn(self.current_id)

    # ------------------------------------------------------------------
    # Ввод
    # ------------------------------------------------------------------

    def on_key(self, key):

        if key == pygame.K_r and self.game_state.winner is not None:
            self.new_game()
            return

        if self.game_state.winner is not None:
            return

        if key == pygame.K_ESCAPE:
            self.cancel_place()
            self.clear_unit()

        elif key in (pygame.K_SPACE, pygame.K_RETURN):
            self.end_turn()

    def on_wheel(self, direction):

        pos = pygame.mouse.get_pos()

        if pos[0] >= PANEL_X:
            return

        self.camera_x, self.camera_y = self.renderer.set_zoom(
            self.renderer.zoom + direction * ZOOM_STEP,
            pos,
            self.camera_x,
            self.camera_y
        )

    def on_right_click(self):

        self.cancel_place()
        self.clear_unit()

    def on_left_click(self, pos):

        if self.game_state.winner is not None:
            return

        if pos[0] >= PANEL_X:
            self.on_panel_click(pos)
            return

        tile = self.renderer.get_tile_at_mouse(
            pos, self.board, self.camera_x, self.camera_y
        )

        if tile is None:
            self.cancel_place()
            self.clear_unit()
            return

        # Режим покупки: ждём клик по подсвеченной клетке
        if self.place_item:

            if tile in self.place_targets:

                self.board.buy(
                    self.place_region, self.place_item, tile
                )

                self.cancel_place()
                self.clear_unit()
                self.set_selected(tile)
                self.after_action()

            else:
                self.cancel_place()

            return

        # Ход выбранного юнита
        if self.selected_unit_tile and tile in self.reachable:

            self.board.move_unit(self.selected_unit_tile, tile)

            self.clear_unit()
            self.set_selected(tile)
            self.after_action()

            return

        self.set_selected(tile)

        if (
            tile.unit
            and tile.owner == self.current_id
            and not tile.unit.moved
        ):
            self.selected_unit_tile = tile
            self.reachable = self.board.get_moves(tile)

        else:
            self.clear_unit()

    def on_panel_click(self, pos):

        action = self.panel.handle_click(pos)

        if action is None:
            return

        if action == "end_turn":
            self.end_turn()
            return

        # Покупка
        if self.place_item == action:
            self.cancel_place()
            return

        region = self.active_region()

        targets = self.board.buy_targets(region, action)

        if not targets:
            return

        self.clear_unit()

        self.place_item = action
        self.place_region = region
        self.place_targets = targets

    # ------------------------------------------------------------------
    # Цикл
    # ------------------------------------------------------------------

    def update_camera(self):

        keys = pygame.key.get_pressed()

        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            self.camera_x += CAMERA_SPEED

        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            self.camera_x -= CAMERA_SPEED

        if keys[pygame.K_w] or keys[pygame.K_UP]:
            self.camera_y += CAMERA_SPEED

        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            self.camera_y -= CAMERA_SPEED

    def draw(self):

        self.screen.fill(BACKGROUND_COLOR)

        self.screen.set_clip(
            pygame.Rect(0, 0, PANEL_X, SCREEN_HEIGHT)
        )

        highlight = (
            self.place_targets if self.place_item
            else self.reachable
        )

        self.renderer.draw_board(
            self.screen,
            self.board,
            self.camera_x,
            self.camera_y,
            self.selected_unit_tile,
            highlight,
            self.current_id
        )

        self.screen.set_clip(None)

        self.panel.draw(
            self.screen,
            self.game_state,
            self.board,
            self.active_region(),
            self.selected_tile,
            self.place_item
        )

        if self.game_state.winner is not None:
            self.draw_winner()

        pygame.display.flip()

    def draw_winner(self):

        overlay = pygame.Surface(
            (PANEL_X, SCREEN_HEIGHT), pygame.SRCALPHA
        )

        overlay.fill((0, 0, 0, 160))

        self.screen.blit(overlay, (0, 0))

        winner = self.game_state.winner

        title = self.big_font.render(
            f"Победил игрок {winner}!",
            True,
            PLAYER_COLORS[winner]
        )

        hint = self.font.render(
            "R — новая игра",
            True,
            (255, 255, 255)
        )

        self.screen.blit(
            title,
            title.get_rect(center=(PANEL_X // 2, SCREEN_HEIGHT // 2 - 30))
        )

        self.screen.blit(
            hint,
            hint.get_rect(center=(PANEL_X // 2, SCREEN_HEIGHT // 2 + 40))
        )

    def run(self):

        running = True

        while running:

            self.clock.tick(FPS)

            for event in pygame.event.get():

                if event.type == pygame.QUIT:
                    running = False

                elif event.type == pygame.KEYDOWN:
                    self.on_key(event.key)

                elif event.type == pygame.MOUSEBUTTONDOWN:

                    if event.button == 1:
                        self.on_left_click(event.pos)

                    elif event.button == 3:
                        self.on_right_click()

                elif event.type == pygame.MOUSEWHEEL:
                    self.on_wheel(event.y)

            self.update_camera()

            self.draw()

        pygame.quit()


def main():

    App().run()


if __name__ == "__main__":
    main()
