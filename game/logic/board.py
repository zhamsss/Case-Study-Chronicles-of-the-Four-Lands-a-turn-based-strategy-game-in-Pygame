"""Вся игровая логика (без pygame): карта, регионы, ходы, бой, покупки, экономика."""

import random
from collections import deque

from game.config import (
    MAP_WIDTH,
    MAP_HEIGHT,
    START_GOLD,
    UNIT_COST,
    UNIT_MOVE_RANGE,
    FARM_BASE_COST,
    FARM_COST_STEP,
    FARM_INCOME,
    TOWER_COST,
    TOWER_UPKEEP,
    TREE_DENSITY,
    TREE_SPREAD_CHANCE,
    TREE_CHOP_REWARD,
)
from game.models.tile import Tile
from game.models.unit import Unit


# Соседи для pointy-top гексов, схема "odd-r"
EVEN_ROW_DIRS = [(1, 0), (-1, 0), (-1, -1), (0, -1), (-1, 1), (0, 1)]
ODD_ROW_DIRS = [(1, 0), (-1, 0), (0, -1), (1, -1), (0, 1), (1, 1)]

ITEMS = (
    "unit_1", "unit_2", "unit_3", "unit_4",
    "farm", "tower_1", "tower_2",
)


class Region:
    """Связная область одного игрока. Казна лежит на клетке-столице."""

    def __init__(self, owner, tiles, capital):
        self.owner = owner
        self.tiles = tiles
        self.capital = capital

    @property
    def gold(self):
        return self.capital.gold if self.capital else 0

    @gold.setter
    def gold(self, value):
        if self.capital:
            self.capital.gold = value

    @property
    def income(self):
        total = 0
        for tile in self.tiles:
            if not tile.tree:
                total += 1
            if tile.house:
                total += FARM_INCOME
        return total

    @property
    def upkeep(self):
        total = 0
        for tile in self.tiles:
            if tile.unit:
                total += tile.unit.salary
            if tile.tower_level:
                total += TOWER_UPKEEP[tile.tower_level]
        return total

    @property
    def net_income(self):
        return self.income - self.upkeep

    @property
    def unit_count(self):
        return sum(1 for t in self.tiles if t.unit)

    @property
    def farm_count(self):
        return sum(1 for t in self.tiles if t.house)


class Board:

    def __init__(self):

        self.tiles = {}

        for r in range(MAP_HEIGHT):
            for q in range(MAP_WIDTH):
                self.tiles[(q, r)] = Tile(q, r)

        self._neighbours = {}

        for (q, r), tile in self.tiles.items():
            dirs = ODD_ROW_DIRS if r % 2 else EVEN_ROW_DIRS
            self._neighbours[tile] = [
                self.tiles[(q + dq, r + dr)]
                for dq, dr in dirs
                if (q + dq, r + dr) in self.tiles
            ]

        self.regions = []
        self.region_map = {}

        self._generate()
        self.update_regions()

    # ------------------------------------------------------------------
    # Генерация и вспомогательное
    # ------------------------------------------------------------------

    def _generate(self):

        for tile in self.tiles.values():
            if random.random() < TREE_DENSITY:
                tile.tree = True

        centers = {
            1: (2, 2),
            2: (MAP_WIDTH - 3, 2),
            3: (2, MAP_HEIGHT - 3),
            4: (MAP_WIDTH - 3, MAP_HEIGHT - 3),
        }

        for player_id, (q, r) in centers.items():

            center = self.tiles[(q, r)]

            for tile in [center] + self._neighbours[center]:
                tile.clear()
                tile.owner = player_id

            center.capital = True
            center.gold = START_GOLD

    def neighbours(self, tile):
        return self._neighbours[tile]

    def region_of(self, tile):
        return self.region_map.get(tile)

    def regions_of(self, player_id):
        return [r for r in self.regions if r.owner == player_id]

    # ------------------------------------------------------------------
    # Регионы
    # ------------------------------------------------------------------

    def update_regions(self):
        """Пересчитать связные области, столицы и казны."""

        visited = set()
        components = []

        for tile in self.tiles.values():

            if tile.owner is None or tile in visited:
                continue

            component = [tile]
            visited.add(tile)
            queue = deque([tile])

            while queue:
                current = queue.popleft()

                for n in self._neighbours[current]:
                    if n.owner == tile.owner and n not in visited:
                        visited.add(n)
                        component.append(n)
                        queue.append(n)

            components.append(component)

        self.regions = []
        self.region_map = {}

        for component in components:

            owner = component[0].owner

            # Область из одной клетки пропадает
            if len(component) == 1:
                component[0].clear()
                continue

            capitals = [t for t in component if t.capital]

            if not capitals:
                capital = self._pick_capital_tile(component)
                capital.capital = True
                capital.gold = 0
                capitals = [capital]

            elif len(capitals) > 1:
                # Области слились: казны складываются, остаётся одна столица
                keep = capitals[0]
                keep.gold = sum(c.gold for c in capitals)

                for extra in capitals[1:]:
                    extra.capital = False
                    extra.gold = 0

            region = Region(owner, component, capitals[0])
            self.regions.append(region)

            for tile in component:
                self.region_map[tile] = region

    def _pick_capital_tile(self, component):

        candidates = [
            t for t in component
            if t.unit is None and not t.has_building
        ]

        if not candidates:
            candidates = [t for t in component if t.unit is None]

        if not candidates:
            candidates = component

        tile = random.choice(candidates)

        tile.unit = None
        tile.tree = False
        tile.tombstone = False
        tile.house = False
        tile.tower_level = 0

        return tile

    # ------------------------------------------------------------------
    # Защита и бой
    # ------------------------------------------------------------------

    def tile_defense(self, tile):
        """Защита клетки = максимум по ней самой и соседним клеткам владельца."""

        if tile.owner is None:
            return 0

        defense = tile.get_defense()

        for n in self._neighbours[tile]:
            if n.owner == tile.owner:
                defense = max(defense, n.get_defense())

        return defense

    def can_capture(self, level, target, player_id):

        if target.owner == player_id:
            return False

        if target.owner is None:
            return True

        # Рыцарь (4) бьёт всё, т.к. максимальная защита = 3
        return level > self.tile_defense(target)

    def _can_stand(self, level, tile):
        """Можно ли юниту такого уровня встать на СВОЮ клетку."""

        if tile.has_building:
            return False

        if tile.unit:
            return tile.unit.level + level <= 4

        return True

    def _capture(self, tile, player_id):

        tile.owner = player_id
        tile.unit = None
        tile.capital = False
        tile.gold = 0
        tile.house = False
        tile.tower_level = 0

    # ------------------------------------------------------------------
    # Движение
    # ------------------------------------------------------------------

    def get_moves(self, src):

        unit = src.unit

        if unit is None or unit.moved:
            return set()

        player_id = src.owner
        level = unit.level

        moves = set()
        dist = {src: 0}
        queue = deque([src])

        while queue:

            current = queue.popleft()

            if dist[current] >= UNIT_MOVE_RANGE:
                continue

            for n in self._neighbours[current]:

                if n in dist:
                    continue

                dist[n] = dist[current] + 1

                if n.owner == player_id:
                    # По своей земле можно идти дальше
                    queue.append(n)

                    if self._can_stand(level, n):
                        moves.add(n)

                elif self.can_capture(level, n, player_id):
                    # Чужая/нейтральная клетка — конечная точка
                    moves.add(n)

        return moves

    def move_unit(self, src, dst):

        unit = src.unit
        player_id = src.owner

        src.unit = None

        chopped = dst.tree

        if dst.owner == player_id:

            if dst.unit:
                dst.unit = Unit(
                    level=min(4, dst.unit.level + unit.level)
                )
            else:
                dst.unit = unit

        else:
            self._capture(dst, player_id)
            dst.unit = unit

        dst.tree = False
        dst.tombstone = False
        dst.unit.moved = True

        self.update_regions()

        if chopped:
            self._reward_tree(dst)

    def _reward_tree(self, tile):

        region = self.region_map.get(tile)

        if region and region.capital:
            region.capital.gold += TREE_CHOP_REWARD

    # ------------------------------------------------------------------
    # Покупки
    # ------------------------------------------------------------------

    def item_cost(self, region, item):

        if item.startswith("unit_"):
            return UNIT_COST[int(item[5:])]

        if item == "farm":
            return FARM_BASE_COST + FARM_COST_STEP * region.farm_count

        if item.startswith("tower_"):
            return TOWER_COST[int(item[6:])]

        raise ValueError(item)

    def buy_targets(self, region, item):

        if region is None or region.capital is None:
            return set()

        if region.gold < self.item_cost(region, item):
            return set()

        targets = set()

        if item.startswith("unit_"):

            level = int(item[5:])

            for tile in region.tiles:

                if self._can_stand(level, tile):
                    targets.add(tile)

                for n in self._neighbours[tile]:
                    if (
                        n.owner != region.owner
                        and self.can_capture(level, n, region.owner)
                    ):
                        targets.add(n)

        elif item == "farm":

            for tile in region.tiles:

                if (
                    tile.unit
                    or tile.has_building
                    or tile.tree
                    or tile.tombstone
                ):
                    continue

                if any(
                    n.owner == region.owner and (n.capital or n.house)
                    for n in self._neighbours[tile]
                ):
                    targets.add(tile)

        else:

            level = int(item[6:])

            for tile in region.tiles:

                if (
                    tile.unit
                    or tile.capital
                    or tile.house
                    or tile.tree
                    or tile.tombstone
                ):
                    continue

                if tile.tower_level == 0:
                    targets.add(tile)

                elif level == 2 and tile.tower_level == 1:
                    targets.add(tile)

        return targets

    def buy(self, region, item, tile):

        if tile not in self.buy_targets(region, item):
            return False

        cost = self.item_cost(region, item)
        region.capital.gold -= cost

        chopped = False

        if item.startswith("unit_"):

            level = int(item[5:])
            chopped = tile.tree

            if tile.owner == region.owner:
                if tile.unit:
                    level = min(4, tile.unit.level + level)
            else:
                self._capture(tile, region.owner)

            tile.unit = Unit(level=level, moved=True)
            tile.tree = False
            tile.tombstone = False

        elif item == "farm":
            tile.house = True

        else:
            tile.tower_level = int(item[6:])

        self.update_regions()

        if chopped:
            self._reward_tree(tile)

        return True

    # ------------------------------------------------------------------
    # Смена хода
    # ------------------------------------------------------------------

    def start_turn(self, player_id):
        """Начало хода игрока: доход, голод, надгробия, сброс ходов."""

        for tile in self.tiles.values():

            if tile.owner != player_id:
                continue

            if tile.tombstone:
                tile.tombstone = False
                tile.tree = True

            if tile.unit:
                tile.unit.moved = False

        for region in self.regions:

            if region.owner != player_id or region.capital is None:
                continue

            new_gold = region.gold + region.net_income

            if new_gold < 0:
                # Нечем платить армии — все юниты региона умирают
                for tile in region.tiles:
                    if tile.unit:
                        tile.unit = None
                        tile.tombstone = True

                region.capital.gold = 0

            else:
                region.capital.gold = new_gold

    def grow_trees(self):
        """Раз в раунд: деревья распространяются на соседние свободные клетки."""

        new_trees = []

        for tile in self.tiles.values():

            if tile.tree and random.random() < TREE_SPREAD_CHANCE:

                free = [
                    n for n in self._neighbours[tile] if n.is_free
                ]

                if free:
                    new_trees.append(random.choice(free))

        for tile in new_trees:
            tile.tree = True
