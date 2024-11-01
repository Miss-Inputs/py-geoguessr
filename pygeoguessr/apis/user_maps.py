from collections.abc import Sequence
from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING

import pydantic

#ruff: noqa: TCH001
from pygeoguessr.api import call_api, call_api_async
from pygeoguessr.models import LatLng, MapAvatar
from pygeoguessr.settings import BaseModel
from pygeoguessr.types import CountryCode, MapSlug

if TYPE_CHECKING:
	import aiohttp


class _RegionCountResponse(BaseModel):
	count: int


def count_panoramas_in_region(coordinates: Sequence[LatLng]) -> int:
	# Hmm, not sure how you'd get this to recognize holes, but I guess you can't do that in map maker anyway
	url = 'api/v4/user-maps/region-count'
	response = _RegionCountResponse.model_validate_json(
		call_api(url, method='POST', json_body={'coordinates': coordinates})
	)
	return response.count


async def count_panoramas_in_region_async(
	coordinates: Sequence[LatLng], session: 'aiohttp.ClientSession | None' = None
) -> int:
	# Hmm, not sure how you'd get this to recognize holes, but I guess you can't do that in map maker anyway
	url = 'api/v4/user-maps/region-count'
	response = _RegionCountResponse.model_validate_json(
		await call_api_async(url, session, method='POST', json_body={'coordinates': coordinates})
	)
	return response.count


class UserMapMode(StrEnum):
	Coordinates = 'coordinates'
	Regions = 'regions'


class Coordinate(LatLng):
	panoId: str | None
	heading: float
	pitch: float
	zoom: float
	countryCode: CountryCode | None
	stateCode: str | None


class Region(BaseModel):
	coordinates: list[LatLng]


class BaseUserMap(BaseModel):
	slug: MapSlug
	name: str
	description: str | None
	highlighted: bool
	avatar: MapAvatar
	regions: list[Region] | None
	'Only if mode is regions'
	coordinates: list[Coordinate] | None
	'Only if mode is coordinates'


class MapDraft(BaseUserMap):
	mode: UserMapMode
	created: datetime
	updated: datetime


class UserMap(BaseUserMap):
	published: bool


_map_draft_list_adapter = pydantic.TypeAdapter(list[MapDraft])


def get_map_draft(map_slug: MapSlug):
	url = f'/api/v4/user-maps/drafts/{map_slug}'
	return MapDraft.model_validate_json(call_api(url, needs_auth=True))


async def get_map_draft_async(map_slug: MapSlug, session: 'aiohttp.ClientSession | None' = None):
	url = f'/api/v4/user-maps/drafts/{map_slug}'
	return MapDraft.model_validate_json(await call_api_async(url, session, needs_auth=True))


def get_map_drafts():
	"""Gets list of all maps you have made that are published or drafts, including the coordinates/regions for each one, so it may return a lot of data"""
	url = '/api/v4/user-maps/drafts/'
	return _map_draft_list_adapter.validate_json(call_api(url, needs_auth=True))


async def get_map_drafts_async(session: 'aiohttp.ClientSession | None' = None):
	"""Gets list of all maps you have made that are published or drafts, including the coordinates/regions for each one, so it may return a lot of data"""
	# Might be paginated?
	url = '/api/v4/user-maps/drafts/'
	return _map_draft_list_adapter.validate_json(await call_api_async(url, session, needs_auth=True))


# https://geoguessr.com/api/v4/user-maps/maps > actually just returns list[Map] with a page of 10 published maps (has page=<int> count=<default 10> params, start at 0 and break when amount of maps returned less than count)


def get_user_map(map_slug: MapSlug):
	"""Returns map you have made, as UserMap instead of MapDraft (no mode/created/updated, but published = bool)"""
	url = f'/api/v4/user-maps/maps/{map_slug}'
	return UserMap.model_validate_json(call_api(url, needs_auth=True))


async def get_user_map_async(map_slug: MapSlug, session: 'aiohttp.ClientSession | None' = None):
	"""Returns map you have made, as UserMap instead of MapDraft (no mode/created/updated, but published = bool)"""
	url = f'/api/v4/user-maps/maps/{map_slug}'
	return UserMap.model_validate_json(await call_api_async(url, session, needs_auth=True))


map_list_adapter = pydantic.TypeAdapter(list[UserMap])


def get_unpublished_maps():
	"""Requires login, returns all maps from the map maker that user has not published yet"""
	#this could be paginated? Haven't created enough unpublished maps to find out
	return map_list_adapter.validate_json(call_api('/api/v4/user-maps/dangling-drafts', needs_auth=True))


async def get_unpublished_maps_async(session: 'aiohttp.ClientSession | None' = None):
	"""Requires login, returns all maps from the map maker that user has not published yet"""
	return map_list_adapter.validate_json(
		await call_api_async('/api/v4/user-maps/dangling-drafts', session, needs_auth=True)
	)
