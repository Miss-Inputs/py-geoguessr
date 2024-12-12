from collections.abc import AsyncIterator, Iterator
from datetime import datetime
from enum import IntEnum
from typing import TYPE_CHECKING, Any

import pydantic

from pygeoguessr.api import call_api, call_api_async, get_default_async_session
from pygeoguessr.settings import BaseModel

# ruff: noqa: TC001
from pygeoguessr.types import (
	ChallengeToken,
	CompetitiveGameMode,
	GameMode,
	GameToken,
	LobbyToken,
	MapSlug,
	UserID,
)

if TYPE_CHECKING:
	import aiohttp


class ActivityType(IntEnum):
	"""See also https://www.geoguessr.com/_next/static/chunks/pages/me/activities-95dd65fda6655cd8.js"""

	PlayedGame = 1
	PlayedChallenge = 2
	CreatedMap = 3
	"""Not sure if this is used. Doesn't seem to happen for the private activitie feed, at least"""
	ObtainedBadge = 4
	LikedMap = 5
	PlayedCompetitiveGame = 6  # Ranked stuff
	MultipleActivities = 7  # payload is array of {type, time, payload}
	PlayedSinglePlayerQuiz = 8
	PlayedMultiplayer = 9
	PlayedInfinityGame = 10  # Might be a single round?
	PlayedCasualGame = 11  # Might be the random unranked stuff ones on the multiplayer page?
	PlayedQuickplayGame = 12
	PlayedPublicTeamDuel = 13


class PlayedGameActivity(BaseModel):
	mapSlug: 'MapSlug'
	mapName: str | None = None
	"""If country streaks, this will be missing, even if the game's details reveal the map name of "country-streak" """
	points: int
	"""May be the total number of points across all rounds, or the number of successful guesses in a streak game, etc"""
	gameToken: 'GameToken'
	gameMode: 'GameMode'


class PlayedChallengeActivity(BaseModel):
	mapSlug: 'MapSlug'
	mapName: str
	points: int
	"""Number of points across all rounds, presumably >= 0 and <= 25000"""
	challengeToken: 'ChallengeToken'
	gameMode: 'GameMode'
	isDailyChallenge: bool | None = None
	"""Well, that's quite annoying that it's sometimes None"""


class CreatedMapActivity(BaseModel):
	mapSlug: 'MapSlug'
	mapName: str


class ObtainedBadgeActivity(BaseModel):
	badgeId: str
	"""Opaque ID representing which badge was obtained"""
	badgeName: str
	"""Human readable badge name"""
	badgeLevel: int
	"""1-10?"""
	imagePath: str
	"""Something like badge/c6f10b2b0c56f8a294b40e1c845689a1.png for example"""


class LikedMapActivity(BaseModel):
	"""User liked a map. Hmm, I guess this is the same as CreatedMapActivity, except for the capitalisation"""

	mapSlug: 'MapSlug'
	mapname: str  # sic


class PlayedCompetitiveActivity(BaseModel):
	gameId: 'LobbyToken'
	gameMode: 'GameMode'
	competitiveGameMode: 'CompetitiveGameMode | None' = None
	"""I don't know why this is sometimes here and sometimes not"""


class PlayedMultiplayerActivity(BaseModel):
	"""User played a multiplayer game with friends"""

	gameId: 'LobbyToken'
	partyId: str
	"""Opaque token for the party"""
	gameMode: 'GameMode'


class PlayedQuizActivity(BaseModel):
	quizId: str
	"""Opaque token for the quiz"""
	quizName: str


class InfinityGameActivity(BaseModel):
	"""User played an Infinity game, back when that was a thing"""

	points: int
	gameToken: 'GameToken'
	isChallenge: bool


class ActivityUserAvatar(BaseModel):
	url: str
	isDefault: bool
	anchor: str


class ActivityUser(BaseModel):
	id: UserID
	nick: str
	isVerified: bool
	flair: int
	avatar: ActivityUserAvatar


class ActivityWithoutUser(BaseModel):
	type: ActivityType
	time: datetime
	payload: Any


class RawActivity(ActivityWithoutUser):
	"""This is kind of an asshole to parse with just pydantic, so we'll need to do it ourselves"""

	user: ActivityUser


class Activity(RawActivity):
	payload: (
		PlayedGameActivity
		| PlayedChallengeActivity
		| CreatedMapActivity
		| ObtainedBadgeActivity
		| LikedMapActivity
		| PlayedCompetitiveActivity
		| PlayedMultiplayerActivity
		| PlayedQuizActivity
		| InfinityGameActivity
	)


class ActivityFeedPage(BaseModel):
	entries: list[RawActivity]
	paginationToken: str | None
	"""Token for the next page, unless this is the last one"""


def _get_activity_feed_page(
	pagination_token: str | None = None, per_page: int = 50, *, friends: bool = False
) -> ActivityFeedPage:
	feed_type = 'friends' if friends else 'private'
	url = f'api/v4/feed/{feed_type}'
	params: dict[str, str | int] = {'count': per_page}
	if pagination_token:
		params['paginationToken'] = pagination_token
	# Avoid caching the first page because that would be a bit silly
	response = call_api(url, params, do_not_cache=pagination_token is None, needs_auth=True)
	return ActivityFeedPage.model_validate_json(response)


async def _get_activity_feed_page_async(
	session: 'aiohttp.ClientSession',
	pagination_token: str | None = None,
	per_page: int = 50,
	*,
	friends: bool = False,
) -> ActivityFeedPage:
	feed_type = 'friends' if friends else 'private'
	url = f'https://www.geoguessr.com/api/v4/feed/{feed_type}'
	params: dict[str, str | int] = {'count': per_page}
	if pagination_token:
		params['paginationToken'] = pagination_token
	# Avoid caching the first page because that would be a bit silly
	response = await call_api_async(url, session, params, do_not_cache=pagination_token is None, needs_auth=True)
	return ActivityFeedPage.model_validate_json(response)


def _parse_activity(activity: ActivityWithoutUser, user: ActivityUser, *, from_json: bool = False):
	model: type[pydantic.BaseModel]
	if activity.type in {ActivityType.PlayedGame, ActivityType.PlayedQuickplayGame}:
		model = PlayedGameActivity
	elif activity.type == ActivityType.PlayedChallenge:
		model = PlayedChallengeActivity
	elif activity.type == ActivityType.CreatedMap:
		model = CreatedMapActivity
	elif activity.type == ActivityType.ObtainedBadge:
		model = ObtainedBadgeActivity
	elif activity.type == ActivityType.LikedMap:
		model = LikedMapActivity
	elif activity.type in {ActivityType.PlayedCompetitiveGame, ActivityType.PlayedCasualGame}:
		model = PlayedCompetitiveActivity
	elif activity.type == ActivityType.PlayedMultiplayer:
		model = PlayedMultiplayerActivity
	elif activity.type == ActivityType.PlayedInfinityGame:
		model = InfinityGameActivity
	elif activity.type == ActivityType.PlayedSinglePlayerQuiz:
		model = PlayedQuizActivity
	else:
		raise ValueError('uh oh')
	return Activity(
		type=activity.type,
		time=activity.time,
		payload=model.model_validate_json(activity.payload)
		if from_json
		else model.model_validate(activity.payload),
		user=user,
	)


activity_list_adapter = pydantic.TypeAdapter(list[ActivityWithoutUser])


def iter_activity_feed(per_page: int = 50, *, friends: bool = False) -> Iterator[Activity]:
	pagination_token: str | None = None
	while True:
		page = _get_activity_feed_page(pagination_token, per_page, friends=friends)
		for entry in page.entries:
			if entry.type == ActivityType.MultipleActivities:
				for subentry in activity_list_adapter.validate_json(entry.payload):
					yield _parse_activity(subentry, entry.user)
			else:
				yield _parse_activity(entry, entry.user, from_json=True)
		pagination_token = page.paginationToken
		if not pagination_token:
			break


async def iter_activity_feed_async(
	per_page: int = 50, session: 'aiohttp.ClientSession | None' = None, *, friends: bool = False
) -> AsyncIterator[Activity]:
	pagination_token: str | None = None
	if session is None:
		async with get_default_async_session() as default_session:
			async for activity in iter_activity_feed_async(
				per_page, default_session, friends=friends
			):
				yield activity
		return

	while True:
		page = await _get_activity_feed_page_async(
			session, pagination_token, per_page, friends=friends
		)
		for entry in page.entries:
			if entry.type == ActivityType.MultipleActivities:
				for subentry in activity_list_adapter.validate_json(entry.payload):
					yield _parse_activity(subentry, entry.user)
			else:
				yield _parse_activity(entry, entry.user, from_json=True)
		pagination_token = page.paginationToken
		if not pagination_token:
			break
