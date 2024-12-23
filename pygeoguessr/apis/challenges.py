from collections.abc import AsyncIterator, Sequence
from datetime import datetime, timedelta
from enum import IntEnum
from typing import TYPE_CHECKING, Annotated, Literal

import pydantic

# ruff: noqa: TC001
from pygeoguessr.api import NotFoundError, call_api, call_api_async, get_default_async_session
from pygeoguessr.models import User
from pygeoguessr.settings import BaseModel
from pygeoguessr.types import (
	ChallengeToken,
	CountryCode,
	GameMode,
	GameToken,
	MapSlug,
	Metres,
	StreakType,
	UserID,
)

from .games import Game
from .maps import Map

if TYPE_CHECKING:
	import aiohttp


class ChallengeType(IntEnum):
	"""pages/results/[token]-ddc80a3aeb1ff2f1.js function 56609"""

	Regular = 0
	Official = 1
	"""Daily challenge, etc"""
	Educational = 2
	AutoGenerated = 3
	Rematch = 4
	PostGame = 5


class Challenge(BaseModel):
	token: ChallengeToken
	mapSlug: MapSlug
	roundCount: int
	timeLimit: timedelta
	forbidMoving: bool
	forbidZooming: bool
	forbidRotating: bool
	numberOfParticipants: int
	gameMode: Annotated[GameMode, pydantic.BeforeValidator(str.title)]
	challengeType: ChallengeType
	streakType: StreakType
	accessLevel: Literal[0, 1]
	"""????"""


class ChallengeDetailsResponse(BaseModel):
	challenge: Challenge
	map: Map
	creator: User


class DailyChallengeLeaderboardItem(BaseModel):
	id: UserID
	nick: str
	pinUrl: str  # URL fragment
	totalScore: int
	totalTime: timedelta
	totalDistance: Metres
	isOnLeaderboard: bool
	isVerified: bool
	flair: int  # Probably for elite account havers
	countryCode: CountryCode
	currentStreak: int
	totalStepsCount: int


class DailyChallengeInfo(BaseModel):
	"""Return value of get_daily_challenge_for_today"""

	date: datetime
	"""UTC"""
	participants: int
	token: ChallengeToken
	pickedWinner: bool
	leaderboard: list[DailyChallengeLeaderboardItem]
	friends: list[DailyChallengeLeaderboardItem] | None
	"""Null if not logged in"""
	authorCreator: None  # Not sure what this does?
	country: list[DailyChallengeLeaderboardItem]
	description: str | None


class ChallengeHighscore(BaseModel):
	gameToken: GameToken
	playerName: str
	userId: UserID
	totalScore: int
	isLeader: Literal[False]
	pinUrl: str
	"""pin/blah.png"""
	game: Game


class ChallengeHighscoresPage(BaseModel):
	items: list[ChallengeHighscore]
	paginationToken: str | None


def get_challenge_details_and_creator(challenge: ChallengeToken) -> tuple[Challenge, User]:
	challenge_details = ChallengeDetailsResponse.model_validate_json(
		call_api(f'api/v3/challenges/{challenge}')
	)
	return challenge_details.challenge, challenge_details.creator


def get_challenge_details_map_creator(challenge: ChallengeToken) -> tuple[Challenge, Map, User]:
	challenge_details = ChallengeDetailsResponse.model_validate_json(
		call_api(f'api/v3/challenges/{challenge}')
	)
	return challenge_details.challenge, challenge_details.map, challenge_details.creator


async def get_challenge_details_map_creator_async(
	challenge: ChallengeToken, session: 'aiohttp.ClientSession | None' = None
) -> tuple[Challenge, Map, User]:
	url = f'api/v3/challenges/{challenge}'
	data = await call_api_async(url, session)
	challenge_details = ChallengeDetailsResponse.model_validate_json(data)
	return challenge_details.challenge, challenge_details.map, challenge_details.creator


async def get_challenge_details_and_creator_async(
	challenge: ChallengeToken, session: 'aiohttp.ClientSession | None' = None
) -> tuple[Challenge, User]:
	challenge_details = ChallengeDetailsResponse.model_validate_json(
		await call_api_async(f'api/v3/challenges/{challenge}', session)
	)
	return challenge_details.challenge, challenge_details.creator


def get_challenge_details(challenge: ChallengeToken) -> Challenge:
	return get_challenge_details_and_creator(challenge)[0]


def get_challenge_creator(challenge: ChallengeToken) -> User:
	return get_challenge_details_and_creator(challenge)[1]


def get_game_for_challenge(challenge: ChallengeToken) -> Game | None:
	"""Requires authentication. Gets the Game for the current user's attempt at the challenge.

	Returns:
		Game with all the rounds and guesses etc, or None if this user has not played that challenge yet
	"""
	try:
		return Game.model_validate_json(
			call_api(f'api/v3/challenges/{challenge}/game', needs_auth=True)
		)
	except NotFoundError:
		return None


async def get_game_for_challenge_async(
	challenge: ChallengeToken, session: 'aiohttp.ClientSession | None' = None
) -> Game | None:
	"""Requires authentication. Gets the Game for the current user's attempt at the challenge.

	Returns:
		Game with all the rounds and guesses etc, or None if this user has not played that challenge yet
	"""
	url = f'api/v3/challenges/{challenge}/game'
	try:
		data = await call_api_async(url, session, needs_auth=True)
	except NotFoundError:
		return None
	else:
		return Game.model_validate_json(data)


def get_daily_challenge_for_today() -> DailyChallengeInfo:
	"""Gets info about today's current daily challenge. If logged in, can show the leaderboard for the current user's friends.

	Returns:
		DailyChallengeInfo"""
	# TODO: Make get_challenge_details invalidate its cache if it gets the challenge for today (so that number of people played can be updated, etc)
	return DailyChallengeInfo.model_validate_json(
		call_api('api/v3/challenges/daily-challenges/today', expiry=timedelta(days=1))
	)


async def get_daily_challenge_for_today_async(
	session: 'aiohttp.ClientSession | None' = None,
) -> DailyChallengeInfo:
	"""Gets info about today's current daily challenge. If logged in, can show the leaderboard for the current user's friends.

	Returns:
		DailyChallengeInfo"""
	# TODO: Make get_challenge_details invalidate its cache if it gets the challenge for today (so that number of people played can be updated, etc)
	return DailyChallengeInfo.model_validate_json(
		await call_api_async(
			'api/v3/challenges/daily-challenges/today', session, expiry=timedelta(days=1)
		)
	)


daily_challenge_list_adapter = pydantic.TypeAdapter(list[DailyChallengeInfo])


def get_daily_challenges_for_this_week() -> Sequence[DailyChallengeInfo]:
	"""Does not necessarily need authentication, but friends will be empty otherwise, so we ensure it uses the ncfa cookie"""
	return daily_challenge_list_adapter.validate_json(
		call_api(
			'api/v3/challenges/daily-challenges/previous', expiry=timedelta(days=1), needs_auth=True
		)
	)


async def get_daily_challenges_for_this_week_async(
	session: 'aiohttp.ClientSession | None' = None,
) -> Sequence[DailyChallengeInfo]:
	"""Does not necessarily need authentication, but friends will be empty otherwise, so we ensure it uses the ncfa cookie"""
	return daily_challenge_list_adapter.validate_json(
		await call_api_async(
			'api/v3/challenges/daily-challenges/previous',
			session,
			expiry=timedelta(days=1),
			needs_auth=True,
		)
	)


def get_challenge_highscore_page(
	challenge_token: ChallengeToken,
	limit: int = 50,
	pagination_token: str | None = None,
	min_rounds: int | None = 5,
	country_code: CountryCode | None = None,
	*,
	friends: bool = False,
):
	# limit can be up to 50, seems to be 25 by default but browser client uses 26?
	params = {'friends': 'true' if friends else 'false', 'limit': limit}
	if pagination_token:
		params['paginationToken'] = pagination_token
	if min_rounds is not None:
		params['minRounds'] = min_rounds
	if country_code:
		if friends:
			raise ValueError('Specifying country code is ineffective for friends=true')
		params['countryCode'] = country_code.lower()
	# TODO: synced paginate (whatever)

	return ChallengeHighscoresPage.model_validate_json(
		call_api(f'api/v3/results/highscores/{challenge_token}', params, needs_auth=True)
	)


async def _get_challenge_highscore_page_async(
	session: 'aiohttp.ClientSession',
	challenge_token: ChallengeToken,
	limit: int = 50,
	pagination_token: str | None = None,
	min_rounds: int | None = 5,
	country_code: CountryCode | None = None,
	*,
	friends: bool = False,
) -> ChallengeHighscoresPage:
	# The pagination won't work if you have different sessions, e.g. using the default async session every time
	# limit can be up to 50, seems to be 25 by default but browser client uses 26?
	params = {'friends': 'true' if friends else 'false', 'limit': limit}
	if pagination_token:
		params['paginationToken'] = pagination_token
	if min_rounds is not None:
		params['minRounds'] = min_rounds
	if country_code:
		if friends:
			raise ValueError('Specifying country code is ineffective for friends=true')
		params['countryCode'] = country_code.lower()

	return ChallengeHighscoresPage.model_validate_json(
		await call_api_async(
			f'api/v3/results/highscores/{challenge_token}', session, params, needs_auth=True
		)
	)


async def iter_challenge_highscores_async(
	challenge_token: ChallengeToken,
	min_rounds: int | None = 5,
	country_code: CountryCode | None = None,
	session: 'aiohttp.ClientSession | None' = None,
	*,
	friends: bool = True,
) -> AsyncIterator[ChallengeHighscore]:
	"""Seems to raise 401 errors if you haven't played the challenge yet? Which is odd, but it also has done that at times if you spam the API too much… hrm"""
	if session is None:
		async with get_default_async_session() as default_session:
			async for high_score in iter_challenge_highscores_async(
				challenge_token, min_rounds, country_code, default_session, friends=friends
			):
				yield high_score
		return

	pagination_token = None
	while True:
		page = await _get_challenge_highscore_page_async(
			session,
			challenge_token,
			pagination_token=pagination_token,
			min_rounds=min_rounds,
			country_code=country_code,
			friends=friends,
		)
		for high_score in page.items:
			yield high_score
		if not page.paginationToken:
			break
		pagination_token = page.paginationToken


# TODO: api/v3/results/highscores/{token}/round can get you per-round scores if you want that
# TODO: api/v3/challenges/post-game-challenge - POST, seems to use gameId and friendId in the JSON params
# TODO: api/v3/challenges/rematch/{token} - PUT, can that be done normally without the API? Not a feature I'm aware of
# TODO: # /api/v3/challenges/game/{game token} - may just return a "NoSuchChallenge" error, doesn't create anything
