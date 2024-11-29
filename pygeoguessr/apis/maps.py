from collections.abc import Sequence
from typing import TYPE_CHECKING, Annotated

import pydantic

# ruff: noqa: TC001
from pygeoguessr.api import call_api, call_api_async
from pygeoguessr.models import Map, MapImages
from pygeoguessr.settings import BaseModel
from pygeoguessr.types import CountryCode, MapSlug
from pygeoguessr.utils import x_or_none

if TYPE_CHECKING:
	import aiohttp


class ExplorerMap(BaseModel):
	"""List item in return value of get_explorer_mode_maps"""

	id: str
	slug: MapSlug
	name: str
	countryCode: Annotated[CountryCode | None, pydantic.BeforeValidator(x_or_none)]
	medal: int  # Not at all sure what this is supposed to do, it's always 0?
	images: MapImages


def get_map_details(map_slug: MapSlug) -> Map:
	"""Returns info about a map.
	Raises NotFoundError if e.g. map was deleted, or never existed.

	Returns:
		Map
	"""
	return Map.model_validate_json(call_api(f'api/maps/{map_slug}'))


async def get_map_details_async(
	map_slug: MapSlug, session: 'aiohttp.ClientSession | None' = None
) -> Map:
	"""Returns info about a map.
	Raises NotFoundError if e.g. map was deleted, or never existed.

	Returns:
		Map
	"""
	return Map.model_validate_json(await call_api_async(f'api/maps/{map_slug}', session))


_explorer_map_list_adapter = pydantic.TypeAdapter(list[ExplorerMap])


def get_explorer_mode_maps() -> Sequence[ExplorerMap]:
	"""Returns info about all the maps that are officially available in Explorer Mode.

	Returns:
		Sequence of ExplorerMap
	"""
	return _explorer_map_list_adapter.validate_json(call_api('api/maps/explorer'))


async def get_explorer_mode_maps_async(
	session: 'aiohttp.ClientSession | None' = None,
) -> Sequence[ExplorerMap]:
	"""Returns info about all the maps that are officially available in Explorer Mode.

	Returns:
		Sequence of ExplorerMap
	"""
	return _explorer_map_list_adapter.validate_json(
		await call_api_async('api/maps/explorer', session)
	)


# TODO: #		  = await r.Mb.get('/api/maps?createdBy='.concat((0, r.Nw) (e)) + '&page='.concat((0, r.Nw) (t)) + '&count='.concat((0, r.Nw) (a)), n);
# TODO api/maps/map-of-the-day
# TODO: api/maps?createdBy=(user ID)&page=(page)&count=(count, default 9?) -> list of map objects (without createdBy or with createdBy empty string, returns official maps)
