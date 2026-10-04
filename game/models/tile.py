from dataclasses import dataclass

from game.models.unit import Unit


# eq=False: клетки сравниваются и хешируются по identity,
# поэтому их можно класть в set/dict и быстро делать `tile in tiles`.
@dataclass(eq=False)
class Tile:

    q: int          # столбец
    r: int          # строка

    owner: int | None = None

    unit: Unit | None = None

    capital: bool = False

    selected: bool = False

    screen_x: float = 0
    screen_y: float = 0

    tree: bool = False

    tombstone: bool = False

    house: bool = False         # ферма

    tower_level: int = 0

    gold: int = 0               # казна региона (хранится на клетке-столице)

    @property
    def has_building(self):
        return self.capital or self.house or self.tower_level > 0

    @property
    def is_free(self):
        return (
            self.unit is None
            and not self.has_building
            and not self.tree
            and not self.tombstone
        )

    def clear(self):
        """Полностью очистить клетку (становится нейтральной)."""

        self.owner = None
        self.unit = None
        self.capital = False
        self.tree = False
        self.tombstone = False
        self.house = False
        self.tower_level = 0
        self.gold = 0

    def get_defense(self):

        defense = 0

        if self.unit:
            defense = max(
                defense,
                self.unit.defense
            )

        if self.capital:
            defense = max(
                defense,
                1
            )

        if self.tower_level == 1:
            defense = max(
                defense,
                2
            )

        if self.tower_level == 2:
            defense = max(
                defense,
                3
            )

        return defense
