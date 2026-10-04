from dataclasses import dataclass


@dataclass
class Player:

    player_id: int

    color: str

    alive: bool = True

    # Золото теперь хранится в регионах (на клетке-столице),
    # а не у игрока: у каждой связной области своя казна.
