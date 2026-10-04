from game.config import PLAYER_COLORS
from game.models.player import Player


class GameState:

    def __init__(self):

        self.players = [

            Player(1, "red"),
            Player(2, "blue"),
            Player(3, "green"),
            Player(4, "purple")

        ]

        self.current_player_index = 0

        self.turn_number = 1

        self.winner = None

    @property
    def current_player(self):

        return self.players[
            self.current_player_index
        ]

    @property
    def current_player_color(self):

        return PLAYER_COLORS[
            self.current_player.player_id
        ]

    def get_player(self, player_id):

        for player in self.players:

            if player.player_id == player_id:
                return player

        return None

    def next_player(self):
        """Переходит к следующему живому игроку.
        Возвращает True, если начался новый раунд."""

        new_round = False

        for _ in range(len(self.players)):

            self.current_player_index += 1

            if self.current_player_index >= len(self.players):
                self.current_player_index = 0
                self.turn_number += 1
                new_round = True

            if self.current_player.alive:
                break

        return new_round

    def end_turn(self):

        return self.next_player()

    def update_alive(self, tiles):
        """Игрок жив, пока у него есть хотя бы одна клетка."""

        owners = {
            tile.owner
            for tile in tiles
            if tile.owner is not None
        }

        for player in self.players:
            player.alive = player.player_id in owners

    def check_winner(self, tiles):

        alive_players = {
            tile.owner
            for tile in tiles
            if tile.owner is not None
        }

        if len(alive_players) == 1:

            self.winner = next(iter(alive_players))

            return self.winner

        return None
