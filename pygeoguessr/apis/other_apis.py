"""Things that don't really warrant their own module"""
from typing import TYPE_CHECKING

import pydantic

from pygeoguessr.api import call_api, call_api_async

if TYPE_CHECKING:
	import aiohttp

	from pygeoguessr.types import MapSlug

bool_adapter = pydantic.TypeAdapter(bool)


def is_map_liked(map_slug: 'MapSlug') -> bool:
	"""Returns whether or not the logged in user likes a given map"""
	return bool_adapter.validate_json(call_api(f'api/v3/likes/{map_slug}', do_not_cache=True, needs_auth=True))


async def is_map_liked_async(
	map_slug: 'MapSlug', session: 'aiohttp.ClientSession|None' = None
) -> bool:
	"""Returns whether or not the logged in user likes a given map"""
	return bool_adapter.validate_json(
		await call_api_async(f'api/v3/likes/{map_slug}', session=session, do_not_cache=True, needs_auth=True)
	)


# TODO https://www.geoguessr.com/api/v3/likes?page= - MapDetails of all the liked maps
# async getMyLikedMapsV2(e) {
#     let t = arguments.length > 1 && void 0 !== arguments[1] ? arguments[1] : 10,
#     a = arguments.length > 2 && void 0 !== arguments[2] ? arguments[2] : void 0;
#     try {
#       let {
#         payload: n
#       }
#       = await r.Mb.get('/api/v3/likes/maps?limit='.concat((0, r.Nw) (t)).concat(e ? '&paginationToken='.concat((0, r.Nw) (e)) : ''), a);

# https://geoguessr.com/api/v4/seasons/active/
# https://geoguessr.com/api/v4/seasons/active/user-season
# https://geoguessr.com/api/v4/seasons/active/stats
# TODO: https://geoguessr.com/api/v4/olympics - returns games from the French Olympic Torch Relay thing (would this still work?)
# TODO: api/v4/adventures - New Maprunner stats
# Oh but it also has the Olde Maprunner things too, see also https://www.geoguessr.com/api/v4/adventures/3f35bd4c-1e8e-4565-8692-134000c72906
# I don't think you can get any info on any previously played games though
# TODO: # https://www.geoguessr.com/api/v3/blueprints/{quiz token} - Shows all the questions and correct answers for a quiz
# https://www.geoguessr.com/api/v4/missions Missions for today that you haven't done yet {missions: list of {id, type: "WinGames" or some such, gameMode: "Duels" etc, currentProgress: 0, targetProgress: 1, completed: bool, endDate, rewardAmount: 90, rewardType: "Coins"}, nextMissionDate}
