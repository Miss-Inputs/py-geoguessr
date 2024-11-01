"""Multiplayer-specific APIs, which generally use the game-server.geoguessr.com endpoint instead of the usual geoguessr.com endpoint"""

from .common import (
	MultiplayerGameType,
	get_battle_royale_details,
	get_bullseye_details,
	get_live_challenge_details,
)
from .duels import Duel, get_duel_details, get_duel_details_async
from .lobby import Lobby, get_lobby_details, get_lobby_details_async

__all__ = [
	'Duel',
	'Lobby',
	'MultiplayerGameType',
	'get_battle_royale_details',
	'get_bullseye_details',
	'get_duel_details',
	'get_duel_details_async',
	'get_live_challenge_details',
	'get_lobby_details',
	'get_lobby_details_async',
]
