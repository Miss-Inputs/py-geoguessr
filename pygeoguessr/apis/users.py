from typing import TYPE_CHECKING

from pygeoguessr.api import call_api, call_api_async
from pygeoguessr.models import User

if TYPE_CHECKING:
	import aiohttp

	from pygeoguessr.types import UserID


def get_user(user_id: 'UserID') -> User:
	return User.model_validate_json(call_api(f'https://www.geoguessr.com/api/v3/users/{user_id}'))


async def get_user_async(user_id: 'UserID', session: 'aiohttp.ClientSession | None' = None) -> User:
	return User.model_validate_json(
		await call_api_async(f'https://www.geoguessr.com/api/v3/users/{user_id}', session)
	)


# TODO: https://www.geoguessr.com/api/v3/users/ratings/me - ratings leaderboard with the page of 5 people you are in
# TODO: https://www.geoguessr.com/api/v3/users/ratings/friends?offset={offset}&limit=?
# TODO: https://www.geoguessr.com/api/v3/users/ratings?offset={offset}&limit=?, will only give you 30 at a time despite limit
