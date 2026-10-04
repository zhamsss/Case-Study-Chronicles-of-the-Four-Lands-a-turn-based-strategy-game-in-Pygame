from dataclasses import dataclass


@dataclass
class Unit:

    level: int = 1

    moved: bool = False

    @property
    def attack(self):
        return self.level

    @property
    def defense(self):

        if self.level == 4:
            return 3

        return self.level

    @property
    def salary(self):

        salary_table = {
            1: 2,
            2: 6,
            3: 18,
            4: 36
        }

        return salary_table[self.level]

    @property
    def name(self):

        names = {
            1: "Крестьянин",
            2: "Копейщик",
            3: "Барон",
            4: "Рыцарь"
        }

        return names[self.level]
