from datetime import datetime, timedelta
from enum import StrEnum
from typing import TYPE_CHECKING, Annotated, Literal

#ruff: noqa: TCH001, TCH002
import pydantic

from pygeoguessr.api import call_api, call_api_async
from pygeoguessr.models import LatLng, MapBounds, ProgressChange
from pygeoguessr.settings import BaseModel
from pygeoguessr.types import (
	CompetitiveGameMode,
	CountryCode,
	LobbyToken,
	MapSlug,
	Metres,
	PanoIDAsHexBytes,
	UserID,
)
from pygeoguessr.utils import x_or_none

from .common import MovementOptions

if TYPE_CHECKING:
	import aiohttp


class DuelGuess(BaseModel):
	roundNumber: pydantic.PositiveInt
	lat: float
	lng: float
	distance: Metres
	created: datetime
	isTeamsBestGuessOnRound: bool
	score: int | None


class DuelPlayer(BaseModel):
	playerId: UserID
	guesses: list[DuelGuess]
	rank: int
	rating: int
	countryCode: CountryCode
	progressChange: ProgressChange | None
	pin: LatLng | None
	helpRequested: bool


class DuelRoundResult(BaseModel):
	"""An individual team's result for a specific round"""

	roundNumber: pydantic.PositiveInt
	score: int
	healthBefore: int
	healthAfter: int
	bestGuess: DuelGuess | None


class DuelTeam(BaseModel):
	"""A team in a duel, which may be only one player"""

	id: str
	name: str
	health: int
	players: list[DuelPlayer]
	roundResults: list[DuelRoundResult]


class WinStyle(StrEnum):
	"""Defined in module 2651 somewhere"""

	ComebackVictory = 'ComebackVictory'
	ExpresssComebackVictory = 'ExpressComebackVictory'
	ExpressKnockoutVictory = 'ExpressKnockoutVictory'
	ExpressVictory = 'ExpressVictory'
	FlawlessExpressVictory = 'FlawlessExpressVictory'
	FlawlessKnockoutVictory = 'FlawlessKnockoutVictory'
	FlawlessVictory = 'FlawlessVictory'
	KnockoutVictory = 'KnockoutVictory'
	Victory = 'Victory'


class DuelResult(BaseModel):
	isDraw: bool
	winningTeamId: str
	winnerStyle: WinStyle


class DuelLocation(BaseModel):
	panoId: PanoIDAsHexBytes
	lat: float
	lng: float
	countryCode: Annotated[
		CountryCode | None, pydantic.BeforeValidator(x_or_none)
	]  # Raw value can be empty string
	heading: float | None
	pitch: float | None
	zoom: float | None


class DuelRound(BaseModel):
	roundNumber: pydantic.PositiveInt
	"""Starts at 1"""
	panorama: DuelLocation
	hasProcessedRoundTimeout: bool
	isHealingRound: bool
	multiplier: float
	damageMultiplier: float
	'This seems to always be the same as multiplier?'
	startTime: datetime | None
	endTime: datetime | None
	timerStartTime: datetime | None


class DuelMap(BaseModel):
	name: str
	slug: MapSlug
	bounds: MapBounds
	maxErrorDistance: Metres


class DuelOptions(BaseModel):
	"""Mostly frickin duplicated from movementOptions and lobby gameOptions?"""

	initialHealth: int
	roundTime: timedelta
	maxRoundTime: timedelta
	maxNumberOfRounds: int
	healingRounds: list[int]
	"""Round numbers that are healing rounds, if disableHealing is true then this might still be present but it won't do anything"""
	movementOptions: MovementOptions
	mapSlug: MapSlug
	isRated: bool
	map: DuelMap
	duelRoundOptions: list[None]  # TODO: Empty list?
	roundsWithoutDamageMultiplier: int
	disableMultipliers: bool
	multiplierIncrement: int
	disableHealing: bool
	isTeamDuels: bool
	gameContext: (
		dict[Literal['type', 'id'], str] | None
	)  # TODO: What does this do, and should we make a proper model for it
	# manuallyStartRounds: bool
	# nope that one's not a thing anymore
	flashbackRounds: list[None]
	competitiveGameMode: CompetitiveGameMode
	"""Game mode for duels, e.g. moving/no move/NMPZ"""
	gracePeriodTime: timedelta
	roundStartingBehavior: Literal['Default']
	countAllGuesses: bool
	masterControlAutoStartRounds: bool
	gameTimeOut: timedelta
	"""e.g. 7200 seconds?"""


class Duel(BaseModel):
	gameId: LobbyToken
	teams: list[DuelTeam]
	rounds: list[DuelRound]
	currentRoundNumber: int
	status: Literal[
		'Finished'
	]  # TODO: What does this look like for unfinished duels… but I would need someone who's willing to sit there while I mess with the API, lol
	version: int
	options: DuelOptions
	movementOptions: MovementOptions
	mapBounds: MapBounds
	initialHealth: int
	maxNumberOfRounds: int
	result: DuelResult


def get_duel_details(lobby: LobbyToken) -> Duel:
	return Duel.model_validate_json(
		call_api(f'https://game-server.geoguessr.com/api/duels/{lobby}')
	)


async def get_duel_details_async(
	lobby: LobbyToken, session: 'aiohttp.ClientSession | None' = None
) -> Duel:
	return Duel.model_validate_json(
		await call_api_async(f'https://game-server.geoguessr.com/api/duels/{lobby}', session)
	)
