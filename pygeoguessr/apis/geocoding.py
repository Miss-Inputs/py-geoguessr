import logging
from enum import IntEnum
from typing import TYPE_CHECKING

#ruff: noqa: TC001
from pygeoguessr.api import NotFoundError, call_api, call_api_async
from pygeoguessr.settings import BaseModel
from pygeoguessr.types import CountryCode

if TYPE_CHECKING:
	import aiohttp

logger = logging.getLogger(__name__)


class CountryCodeResponse(BaseModel):
	countryCode: CountryCode


class Terrain(IntEnum):
	"""chunk 5887, function 93949"""

	Unknown = 0
	Water = 1
	Land = 2


class TerrainResponse(BaseModel):
	terrain: Terrain


def get_country_code(lat: float, lng: float) -> CountryCode | None:
	"""Returns what GeoGuessr considers to be the country for a given coordinate, or None if in the ocean or a disputed territory
	Seemingly, this is only used on pages/quiz/[id]/edit-*.js (the custom quiz editor), not entirely sure what exactly for

	Returns:
		CountryCode or None"""
	try:
		response = call_api(
			'api/v4/geo-coding/country/', method='POST', json_body={'lat': lat, 'lng': lng}
		)
	except NotFoundError as e:
		logger.debug('get_country_code(%s, %s): %s', lat, lng, e.args)
		return None
	else:
		return CountryCodeResponse.model_validate_json(response).countryCode


async def get_country_code_async(
	lat: float, lng: float, session: 'aiohttp.ClientSession | None' = None
) -> CountryCode | None:
	"""Returns what GeoGuessr considers to be the country for a given coordinate, or None if in the ocean or a disputed territory
	Seemingly, this is only used on pages/quiz/[id]/edit-*.js (the custom quiz editor), not entirely sure what exactly for

	Returns:
		CountryCode or None"""
	try:
		response = await call_api_async(
			'api/v4/geo-coding/country/', session, method='POST', json_body={'lat': lat, 'lng': lng}
		)
	except NotFoundError:
		return None
	else:
		return CountryCodeResponse.model_validate_json(response).countryCode


def get_terrain(lat: float, lng: float) -> Terrain:
	response = call_api(
		'api/v4/geo-coding/terrain', method='POST', json_body={'lat': lat, 'lng': lng}
	)
	return TerrainResponse.model_validate_json(response).terrain


async def get_terrain_async(lat: float, lng: float, session: 'aiohttp.ClientSession | None' = None) -> Terrain:
	response = await call_api_async(
		'api/v4/geo-coding/terrain', session, method='POST', json_body={'lat': lat, 'lng': lng}
	)
	return TerrainResponse.model_validate_json(response).terrain
