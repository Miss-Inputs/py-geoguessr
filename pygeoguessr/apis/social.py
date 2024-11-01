from collections.abc import Sequence
from typing import TYPE_CHECKING

import pydantic

from pygeoguessr.api import call_api, call_api_async
from pygeoguessr.models import Map

if TYPE_CHECKING:
	import aiohttp


def get_personalized_map() -> Map:
	"""Map for where current user lives"""
	return Map.model_validate_json(call_api('/api/v3/social/maps/browse/personalized', needs_auth=True))


async def get_personalized_map_async(session: 'aiohttp.ClientSession | None' = None) -> Map:
	"""Map for where current user lives"""
	return Map.model_validate_json(
		await call_api_async('/api/v3/social/maps/browse/personalized', session, needs_auth=True)
	)


def get_random_map() -> Map:
	return Map.model_validate_json(
		call_api('api/v3/social/maps/browse/random', do_not_cache=True)
	)


async def get_random_map_async(session: 'aiohttp.ClientSession | None' = None) -> Map:
	return Map.model_validate_json(
		await call_api_async('api/v3/social/maps/browse/random', session, do_not_cache=True)
	)


map_list_adapter = pydantic.TypeAdapter(list[Map])


def get_official_maps() -> Sequence[Map]:
	"""Gets the official list of maps, as listed on https://www.geoguessr.com/maps/official"""
	page_num = 0
	maps: list[Map] = []
	while True:
		# count can only be up to 50, any more and it will just silently cut you off
		page = map_list_adapter.validate_json(
			call_api('api/v3/social/maps/browse/popular/official', {'count': 50, 'page': page_num})
		)
		if not page:
			break
		maps += page
		page_num += 1
	return maps


async def get_official_maps_async(session: 'aiohttp.ClientSession | None' = None) -> Sequence[Map]:
	"""Gets the official list of maps, as listed on https://www.geoguessr.com/maps/official"""
	page_num = 0
	maps: list[Map] = []
	while True:
		# count can only be up to 50, any more and it will just silently cut you off
		page = map_list_adapter.validate_json(
			await call_api_async(
				'api/v3/social/maps/browse/popular/official',
				session,
				{'count': 50, 'page': page_num},
			)
		)
		if not page:
			break
		maps += page
		page_num += 1
	return maps


# TODO api/v3/social/friends - UserDetails of your friends
# TODO: api/v3/social/events/unfinishedgames
# Not GameDetails, but: token, map, mapSlug, score (FormattedScore), dateTime (timestamp with +) (when you started the game originally?), lastActivity (timestamp with +), guesses, rounds, round (which one you got up to), type (but it's an int for some reason), mode (also an int for some reason), locationThumbnail (complete URL link to the static Street View API showing a pano you were up to), mapImage (empty string, null, whatever)
# Returns them in "games", and also has "nextOffset", so is probably paginated

# TODO: /api/v3/social/maps/browse/recommended?mapId=
#   async getRecommendedMaps(e) {
#     let t = arguments.length > 1 && void 0 !== arguments[1] ? arguments[1] : 3,
#     a = arguments.length > 2 ? arguments[2] : void 0;
#     try {
#       let {
#         payload: n
#       }
#       = await r.Mb.get('/api/v3/social/maps/browse/recommended?mapId='.concat((0, r.Nw) (e), '&count=').concat((0, r.Nw) (t)), a);
#       return (0, i.RP) (n)
#     } catch (e) {
#     }
#   }
# },


def _get_custom_streak_maps_page(per_page: int = 50, page: int = 0) -> Sequence[Map]:
	params = {'count': per_page, 'page': page}
	return map_list_adapter.validate_json(call_api('/api/v3/social/maps/browse/streaks', params))


def get_custom_streak_maps(per_page: int = 50) -> Sequence[Map]:
	"""Returns maps that are available for custom streak games."""
	maps = []
	page_num = 0
	while True:
		page = _get_custom_streak_maps_page(per_page, page_num)
		if not page:
			break
		maps += page
	return page


async def _get_custom_streak_maps_page_async(
	session: 'aiohttp.ClientSession|None', per_page: int = 50, page: int = 0
) -> Sequence[Map]:
	params = {'count': per_page, 'page': page}
	return map_list_adapter.validate_json(
		await call_api_async('/api/v3/social/maps/browse/streaks', session, params)
	)


async def get_custom_streak_maps_async(
	per_page: int = 50, session: 'aiohttp.ClientSession|None' = None
) -> Sequence[Map]:
	"""Returns maps that are available for custom streak games."""
	maps = []
	page_num = 0
	while True:
		page = await _get_custom_streak_maps_page_async(session, per_page, page_num)
		if not page:
			break
		maps += page
	return page


# TODO: https://geoguessr.com/api/v3/social/maps/browse/featured -> list of Map
# TODO: https://geoguessr.com/api/v3/social/maps/browse/featured/city -> list of Map, that are all for individual cities
