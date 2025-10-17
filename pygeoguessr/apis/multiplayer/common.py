"""These methods use a different endpoint"""

from enum import StrEnum

# ruff: noqa: TC001
from pygeoguessr.api import call_api
from pygeoguessr.models import Club, DivisionInfo, ProgressRankDivision, UserAvatar
from pygeoguessr.settings import BaseModel
from pygeoguessr.types import CountryCode, LobbyToken, UserID

DuelTeamID = str
"""Opaque ID for a team in a duel"""


class MultiplayerGameType(StrEnum):
	Duels = 'Duels'
	LiveChallenge = 'LiveChallenge'
	TeamDuels = 'TeamDuels'
	Bullseye = 'Bullseye'
	CityStreak = 'CompetitiveCityStreak'
	Countries = 'Countries'
	Distance = 'Distance'


class MovementOptions(BaseModel):
	forbidMoving: bool
	forbidZooming: bool
	forbidRotating: bool


class PlayerRank(BaseModel):
	rank: int | None
	division: ProgressRankDivision


class PlayerCompetitiveInfo(BaseModel):
	rating: int
	division: DivisionInfo
	"""Always says gold?"""


class Player(BaseModel):
	playerId: UserID
	nick: str
	countryCode: CountryCode
	"""What the user has set their country to on their profile"""
	isVerified: bool
	flair: int
	avatarPath: str
	level: int
	titleTierId: int
	division: str
	"""This seems to always say bronze?"""
	performanceStreak: (
		str  # TODO: Enum (e.g. None, but surely there are other more interesting values)
	)
	rank: PlayerRank
	"""Always has every field set to 0?"""
	team: str
	competitive: PlayerCompetitiveInfo
	avatar: UserAvatar
	isGuest: bool
	club: Club | None


def get_battle_royale_details(lobby: LobbyToken):
	# TODO: Handle "You need to be logged in as a guest to do this."
	return call_api(
		f'https://game-server.geoguessr.com/api/battle-royale/{lobby}', needs_auth=False
	)


def get_bullseye_details(lobby: LobbyToken):
	# TODO: Handle "You need to be logged in as a guest to do this."
	return call_api(f'https://game-server.geoguessr.com/api/bullseye/{lobby}', needs_auth=False)


def get_live_challenge_details(lobby: LobbyToken):
	# TODO: Handle "You need to be logged in as a guest to do this."
	return call_api(
		f'https://game-server.geoguessr.com/api/live-challenge/{lobby}', needs_auth=False
	)


# TODO: https://game-server.geoguessr.com/api/replays/{player ID}/{duel ID}/{round number} - hell yeah mothafucka
# time is maybe an epoch (1697970517079, 1697970622350), type = one of these
# (n = s || (s = {})).PanoPosition = "PanoPosition", n.PanoPov = "PanoPov", n.PanoZoom = "PanoZoom", n.MapZoom = "MapZoom", n.MapPosition = "MapPosition", n.PinPosition = "PinPosition", n.Guess = "Guess", n.Focus = "Focus", n.Timer = "Timer", n.KeyPress = "KeyPress", n.MapDisplay = "MapDisplay";
# payload = lat/lng for MapPosition, lat/lng/panoId for PanoPosition, zoom for MapZoom/PanoZoom (likely different meanings, MapZoom is probably the slippy map level, PanoZoom seems to be between 0 and 1 and would be the Street View parameter), isActive/isSticky/size for MapDisplay, heading/pitch for PanoPov
# This does require authorization
