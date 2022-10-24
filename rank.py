class Rank:
    foundation = 1
    copper = 2
    iron = 3
    jade = 4
    low_gold = 5
    high_gold = 6
    true_gold = 7
    underlord = 8
    overlord = 9
    archlord = 10
    monarch = 11
    
    name = {
        foundation: 'foundation',
        copper: 'copper',
        iron: 'iron',
        jade: 'jade',
        low_gold: 'low-gold',
        high_gold: 'high-gold',
        true_gold: 'true-gold',
        underlord: 'underlord',
        overlord: 'overlord',
        archlord: 'archlord',
        monarch: 'monarch'}
    
    description = {
        foundation: 'New to the path',
        copper: 'A first taste of the arts',
        iron: 'Beginning to show strength',
        jade: 'Awareness begins, last entry stage',
        low_gold: 'The first true stage, embers burn',
        high_gold: 'Nearing dangerous power',
        true_gold: 'Highest rank before true mastery',
        underlord: 'Revelation and control of soulpower',
        overlord: 'Challenges are nothing',
        archlord: 'Kneel only for the Monarch',
        monarch: 'Maximum power'}

    def __init__(self, value: int):
        self.value = value

    @staticmethod
    def equal(left, right):
        return left.value == right.value

    def __str__(self):
        return self.name[self.value]

    @classmethod
    def of_string(cls, s: str):
        for (value, name) in cls.name.items():
            if s == name:
                return cls(value = value)