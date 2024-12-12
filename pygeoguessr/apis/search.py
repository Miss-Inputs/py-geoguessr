from collections.abc import AsyncIterator, Iterator, Sequence
from datetime import datetime
from typing import TYPE_CHECKING, Literal

import pydantic

# ruff: noqa: TC001
from pygeoguessr.api import call_api, call_api_async
from pygeoguessr.models import MapAvatar
from pygeoguessr.settings import BaseModel
from pygeoguessr.types import CountryCode, MapSlug, UserID

if TYPE_CHECKING:
	import aiohttp

# api/v3/search/any: Results for both maps and users (distinguished by type field), but do we really need that


class UserSearchResult(BaseModel):
	id: UserID
	name: str
	lastVisitAt: datetime
	"""Could be when they last visited the website?"""
	countryCode: CountryCode
	"""Country this user is from"""
	xp: int
	"""Amount of experience points this user has"""
	isVerified: bool
	flair: int  # TODO: What does this mean again
	url: str
	"""URL fragment = /user/{id}"""
	imageUrl: str
	"""URL fragment = pin/some other ID.png"""
	type: Literal[0]
	"""Seems to just specify this was a search result for a user"""


class MapSearchResult(BaseModel):
	id: MapSlug
	"""Map slug/ID"""
	name: str
	"""Map name"""
	description: str | None
	likes: int
	"""Current number of likes"""
	coordinateCount: int
	"""Precise coordinate count, which is only shown here in the search result and not on usual maps"""
	numberOfGamesPlayed: int
	isUserMap: bool
	creatorId: UserID
	created: datetime
	updated: datetime
	imageUrl: str | None
	creator: str
	'Display name/nick of map creator'
	mapAvatar: MapAvatar
	type: Literal[1]
	"""Just seems to indicate that this was a search for maps"""


_map_search_result_adapter = pydantic.TypeAdapter(list[MapSearchResult])

_map_search_url = 'api/v3/search/map'


def _search_maps_page(q: str, page: int, count: int = 100):
	params: dict[str, str | int] = {'page': page, 'count': count, 'q': q}
	response = call_api(_map_search_url, params)
	return _map_search_result_adapter.validate_json(response)


def search_maps(q: str) -> Iterator[MapSearchResult]:
	"""Gets a list of maps for a given query, as with https://www.geoguessr.com/search?query=q and selecting Maps"""
	# TODO: Should this be uncached or have a different expiry?
	# Hrm why does this never return some official maps? (Curacao/Christmas Island/Gibraltar/Monaco)
	# Well, Curacao is possibly due to the map name having an accent, but if you replace it with normal c it works, which makes no sense
	# But I guess that's because the website's search feature sucks

	i = 0
	while True:
		page = _search_maps_page(q, i)
		if not page:
			break
		yield from page
		i += 1


async def _search_maps_page_async(
	session: 'aiohttp.ClientSession | None', q: str, page: int, count: int = 100
) -> Sequence[MapSearchResult]:
	params: dict[str, str | int] = {'page': page, 'count': count, 'q': q}
	response = await call_api_async(_map_search_url, session, params)
	return _map_search_result_adapter.validate_json(response)


async def search_maps_async(
	q: str, session: 'aiohttp.ClientSession | None' = None
) -> AsyncIterator[MapSearchResult]:
	"""Yields maps for a given query, as with https://www.geoguessr.com/search?query=q and selecting Maps"""
	# TODO: Should this be cached or have a different expiry?
	i = 0
	while True:
		page = await _search_maps_page_async(session, q, i)
		if not page:
			break
		for item in page:
			yield item
		i += 1


_user_result_adapter = pydantic.TypeAdapter(list[UserSearchResult])

_user_search_url = 'api/v3/search/user'


def _search_users_page(q: str, page: int, count: int = 100) -> Sequence[UserSearchResult]:
	params: dict[str, str | int] = {'page': page, 'count': count, 'q': q}
	response = call_api(_user_search_url, params)
	return _user_result_adapter.validate_json(response)


def search_users(q: str) -> Sequence[UserSearchResult]:
	i = 0
	results: list[UserSearchResult] = []
	while True:
		page = _search_users_page(q, i)
		if not page:
			break
		results += page
		i += 1
	return results


async def _search_users_page_async(
	session: 'aiohttp.ClientSession | None', q: str, page: int, count: int = 100
) -> Sequence[UserSearchResult]:
	params: dict[str, str | int] = {'page': page, 'count': count, 'q': q}
	response = await call_api_async(_user_search_url, session, params)
	return _user_result_adapter.validate_json(response)


async def search_users_async(
	q: str, session: 'aiohttp.ClientSession | None' = None
) -> Sequence[UserSearchResult]:
	i = 0
	results: list[UserSearchResult] = []
	while True:
		page = await _search_users_page_async(session, q, i)
		if not page:
			break
		results += page
		i += 1
	return results
