from datetime import datetime, timedelta
from enum import StrEnum
from typing import TYPE_CHECKING, Annotated, Literal

# ruff: noqa: TC001, TC002
import pydantic

from pygeoguessr.api import call_api, call_api_async
from pygeoguessr.models import MapBounds, ProgressChange, UserPin
from pygeoguessr.settings import BaseModel
from pygeoguessr.types import (
	CountryCode,
	GameToken,
	MapSlug,
	Metres,
	PanoIDAsHexBytes,
	StreakType,
	UserID,
	USStateCode,
)
from pygeoguessr.utils import x_or_none

if TYPE_CHECKING:
	import aiohttp


class GameType(StrEnum):
	Standard = 'standard'
	Challenge = 'challenge'
	Infinity = 'infinity'
	Quickplay = 'quickplay'
	Tutorial = 'tutorial'
	AdventCalendar = 'adventcalendar'


class GameRound(BaseModel):
	lat: float
	lng: float
	panoId: PanoIDAsHexBytes | None
	heading: float
	pitch: float
	zoom: float
	streakLocationCode: CountryCode | USStateCode | None
	"""Usually present in non-streak games"""
	startTime: datetime


class FormattedScore(BaseModel):
	amount: str  # For formatting, so while it is generally numeric, it theoretically might not be
	unit: Literal['point', 'points']
	percentage: float  # Out of 100, not 1


class FormattedDistanceUnit(BaseModel):
	amount: str
	unit: Literal['km', 'miles', 'm', 'yd']


class FormattedDistance(BaseModel):
	meters: FormattedDistanceUnit
	miles: FormattedDistanceUnit


class StandardGameGuess(BaseModel):
	lat: float
	lng: float
	timedOut: bool
	timedOutWithGuess: bool
	"""Not sure when this is ever true"""
	skippedRound: bool
	"""Not for when it says could not load the panorama at this round, there seems to be some kind of "skipped round" feature which maybe isn't a thing anymore or is some secret thing not for normal users or who knows"""
	roundScore: FormattedScore
	roundScoreInPercentage: float
	"""Out of 100, not 1"""
	roundScoreInPoints: int
	"""Might not be a point score out of 5000, if it is a streak game"""
	distance: FormattedDistance
	distanceInMeters: Metres
	streakLocationCode: CountryCode | USStateCode | None
	"""Only present for streak games, sadly. Note that this can be None if the user guessed a dependent territory (e.g. Isle of Man, Puerto Rico) in country streaks, which presumably isn't supposed to happen"""
	time: timedelta
	stepsCount: int | None


class GamePlayer(BaseModel):
	totalScore: FormattedScore
	totalDistance: FormattedDistance
	totalDistanceInMeters: Metres
	totalTime: timedelta
	totalStreak: int
	"""0 if not streak game"""
	guesses: list[StandardGameGuess]
	isLeader: bool
	currentPosition: int  # 0 if not on the leaderboard
	pin: UserPin
	newBadges: list[None]  # TODO: This is something
	explorer: None  # TODO: What does this ever do
	id: UserID
	nick: str
	isVerified: bool
	flair: int
	"""0 if no flair"""
	countryCode: CountryCode
	totalStepsCount: int | None


class QuickPlayStreak(BaseModel):
	currentStreak: int
	maxStreak: int
	maxStreakDate: datetime
	"""Has timezone, can be 0001-01-01T00:00:00.0000000+00:00"""


class QuickPlayStreaks(BaseModel):
	fiveKStreak: QuickPlayStreak
	countryStreak: QuickPlayStreak
	continentStreak: QuickPlayStreak


class QuickPlayProgress(BaseModel):
	"""Back when quick play was a mode…"""

	previousStreaks: Annotated[
		QuickPlayStreaks | None, pydantic.BeforeValidator(x_or_none)
	]  # raw value can be empty object
	currentStreaks: QuickPlayStreaks


class Game(BaseModel):
	token: GameToken
	type: GameType
	mode: Literal['standard', 'streak']
	state: Literal['started', 'finished']
	roundCount: 'pydantic.PositiveInt'  # Usually 5, or 3 for tutorial, 1 for quickplay, n + 1 for streaks of n length (as it includes the last round where you lost) #TODO: What would it be for ongoing streak games?
	timeLimit: timedelta
	'0 means no time limit'
	forbidMoving: bool
	forbidZooming: bool
	forbidRotating: bool
	streakType: StreakType
	map: MapSlug
	mapName: str
	panoramaProvider: Literal[0]
	"""Maybe this is a different number for Mapillary when that was a thing"""
	bounds: MapBounds
	round: int  # Current round you are up to, or roundCount if finished
	rounds: list[GameRound]
	player: GamePlayer
	progressChange: ProgressChange | None
	quickPlayProgress: QuickPlayProgress | None = None
	"""Maybe not present anymore"""


def get_game_details(game: GameToken) -> Game:
	return Game.model_validate_json(call_api(f'api/v3/games/{game}'))


async def get_game_details_async(
	game: GameToken, session: 'aiohttp.ClientSession | None' = None
) -> Game:
	return Game.model_validate_json(await call_api_async(f'api/v3/games/{game}', session))
