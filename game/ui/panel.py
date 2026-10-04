import pygame

from game.config import (
    SCREEN_HEIGHT,
    SIDE_PANEL_WIDTH,
    PLAYER_COLORS,
)
from game.ui.button import Button


class Panel:

    ITEMS = [
        ("unit_1", "Крестьянин"),
        ("unit_2", "Копейщик"),
        ("unit_3", "Барон"),
        ("unit_4", "Рыцарь"),
        ("farm", "Ферма"),
        ("tower_1", "Башня"),
        ("tower_2", "Сильная башня"),
    ]

    def __init__(self, x):

        self.x = x

        self.title_font = pygame.font.Font(None, 36)
        self.font = pygame.font.Font(None, 28)
        self.hint_font = pygame.font.Font(None, 22)

        width = SIDE_PANEL_WIDTH - 40

        self.end_turn_button = Button(
            x + 20, 20, width, 56, "Конец хода"
        )

        self.labels = dict(self.ITEMS)

        self.item_buttons = {}

        y = 270

        for item, label in self.ITEMS:

            self.item_buttons[item] = Button(
                x + 20, y, width, 38, label, font_size=26
            )

            y += 42

    # ------------------------------------------------------------------

    def handle_click(self, pos):
        """Возвращает 'end_turn', id предмета ('unit_1', 'farm'...) или None."""

        if self.end_turn_button.is_clicked(pos):
            return "end_turn"

        for item, button in self.item_buttons.items():
            if button.is_clicked(pos):
                return item

        return None

    def _text(self, screen, font, text, color, y):

        screen.blit(
            font.render(text, True, color),
            (self.x + 20, y)
        )

    def _object_name(self, tile):

        if tile.capital:
            return "Столица"

        if tile.house:
            return "Ферма"

        if tile.tower_level == 1:
            return "Башня"

        if tile.tower_level == 2:
            return "Сильная башня"

        if tile.tree:
            return "Дерево"

        if tile.tombstone:
            return "Надгробие"

        return "—"

    # ------------------------------------------------------------------

    def draw(
        self,
        screen,
        game_state,
        board,
        region,
        selected_tile,
        place_item
    ):

        pygame.draw.rect(
            screen,
            (18, 23, 33),
            (self.x, 0, SIDE_PANEL_WIDTH, SCREEN_HEIGHT)
        )

        self.end_turn_button.draw(screen)

        player = game_state.current_player

        self._text(
            screen, self.title_font,
            f"Игрок {player.player_id}",
            PLAYER_COLORS[player.player_id], 92
        )

        self._text(
            screen, self.font,
            f"Ход: {game_state.turn_number}",
            (255, 255, 255), 124
        )

        if region is not None:

            self._text(
                screen, self.font,
                f"Золото: {region.gold}",
                (255, 220, 0), 152
            )

            self._text(
                screen, self.font,
                f"Доход: {region.net_income:+d}",
                (120, 255, 120) if region.net_income >= 0
                else (255, 110, 110), 178
            )

            self._text(
                screen, self.font,
                f"Армия: {region.unit_count}",
                (255, 255, 255), 204
            )

            self._text(
                screen, self.font,
                f"Земли: {len(region.tiles)}",
                (255, 255, 255), 230
            )

        # Кнопки покупки

        for item, button in self.item_buttons.items():

            if region is not None and region.capital is not None:

                cost = board.item_cost(region, item)

                button.text = f"{self.labels[item]} — {cost}"
                button.enabled = region.gold >= cost

            else:
                button.text = self.labels[item]
                button.enabled = False

            button.active = item == place_item

            button.draw(screen)

        # Информация о клетке

        self._text(
            screen, self.title_font,
            "Информация", (255, 255, 255), 580
        )

        if selected_tile:

            owner = (
                f"Игрок {selected_tile.owner}"
                if selected_tile.owner else "Нет"
            )

            color = (220, 220, 220)

            self._text(
                screen, self.font,
                f"Клетка: {selected_tile.q}:{selected_tile.r}",
                color, 616
            )

            self._text(
                screen, self.font,
                f"Владелец: {owner}", color, 642
            )

            self._text(
                screen, self.font,
                f"Защита: {board.tile_defense(selected_tile)}",
                color, 668
            )

            self._text(
                screen, self.font,
                f"Объект: {self._object_name(selected_tile)}",
                color, 694
            )

            unit = selected_tile.unit

            if unit:

                white = (255, 255, 255)

                self._text(
                    screen, self.font, unit.name,
                    (255, 210, 110), 732
                )

                self._text(
                    screen, self.font,
                    f"Атака: {unit.attack}", white, 758
                )

                self._text(
                    screen, self.font,
                    f"Защита: {unit.defense}", white, 784
                )

                self._text(
                    screen, self.font,
                    f"Содержание: {unit.salary}", white, 810
                )

        self._text(
            screen, self.hint_font,
            "ПКМ/Esc — отмена, колесо — зум, WASD — камера",
            (130, 135, 145), 868
        )
