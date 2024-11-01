from typing import TYPE_CHECKING

import pydantic

from pygeoguessr.api import call_api, call_api_async
from pygeoguessr.settings import BaseModel
from pygeoguessr.types import MapSlug, Medal, UserID

if TYPE_CHECKING:
	import aiohttp


class ExplorerModeMapStat(BaseModel):
	"""Item of get_explorer_mode_stats return value"""

	bestScore: int
	medal: Medal


explorer_map_dict_adapter = pydantic.TypeAdapter(dict[MapSlug, ExplorerModeMapStat])


def get_explorer_mode_stats(user: UserID | None = None) -> dict[MapSlug, ExplorerModeMapStat]:
	"""Return stats for each map for a user, or the logged in user
	:param user: If None, return the logged in user's stats"""
	url = 'api/v3/explorer/'
	if user:
		url += user
	return explorer_map_dict_adapter.validate_json(
		call_api(f'api/v3/explorer/user/{user}', do_not_cache=True, needs_auth=user is None)
	)


async def get_explorer_mode_stats_async(
	user: UserID | None = None, session: 'aiohttp.ClientSession | None' = None
) -> dict[MapSlug, ExplorerModeMapStat]:
	"""Return stats for each map for a user, or the logged in user
	:param user: If None, return the logged in user's stats"""
	url = 'api/v3/explorer/'
	if user:
		url += user
	return explorer_map_dict_adapter.validate_json(
		await call_api_async(f'api/v3/explorer/user/{user}', session, do_not_cache=True, needs_auth=user is None)
	)
