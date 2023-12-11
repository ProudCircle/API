from dataclasses import dataclass

@dataclass
class Bedwars:
    stars: int

    kills: int
    final_kills: int
    
    deaths: int
    final_deaths: int

    wins: int
    deaths: int
    games_played: int
    

@dataclass
class Player:
    uuid: str
    displayname: str
    