"""Putting stuff in here that doesn't seem to do anything useful at this point, but I may be doing it wrong, but it's here for completeness/experimentationq"""

from typing import TYPE_CHECKING

from pygeoguessr.api import call_api, call_api_async
from pygeoguessr.models import UserDetails
from pygeoguessr.settings import BaseModel

if TYPE_CHECKING:
	import aiohttp

	from pygeoguessr.types import LobbyToken


def login(email: str, password: str) -> UserDetails:
	"""Raises 401 if the email/password are incorrect
	Sets _ncfa and session cookies, the former is what counts you as logged in

	Returns:
	    UserDetails of user you logged in as"""
	#So yes, this does work, it's just that it's paired with logout
	data = {'email': email, 'password': password}
	return UserDetails.model_validate_json(
		call_api(
			'https://geoguessr.com/api/v3/accounts/signin',
			method='POST',
			json_body=data,
			do_not_cache=True,
		)
	)


async def login_async(
	email: str, password: str, session: 'aiohttp.ClientSession | None' = None
) -> UserDetails:
	"""Raises 401 if the email/password are incorrect
	Sets _ncfa and session cookies, the former is what counts you as logged in

	Returns:
	    UserDetails of user you logged in as"""
	data = {'email': email, 'password': password}
	return UserDetails.model_validate_json(
		await call_api_async(
			'https://geoguessr.com/api/v3/accounts/signin',
			session,
			method='POST',
			json_body=data,
			do_not_cache=True,
		)
	)


class LogoutResponse(BaseModel):
	message: str


def logout() -> str:
	"""Note: Doesn't seem to work - doesn't seem to invalidate the cookie, so I dunno how it works then

	Returns:
	    A message"""
	response = call_api(
		'https://geoguessr.com/api/v3/accounts/signout', method='POST', do_not_cache=True
	)
	return LogoutResponse.model_validate_json(response).message


async def logout_async(session: 'aiohttp.ClientSession | None' = None) -> str:
	"""Note: Doesn't seem to work - doesn't seem to invalidate the cookie, so I dunno how it works then

	Returns:
	    A message"""
	response = await call_api_async(
		'https://geoguessr.com/api/v3/accounts/signout', session, method='POST', do_not_cache=True
	)
	return LogoutResponse.model_validate_json(response).message


def get_competitive_streak_details(lobby: 'LobbyToken'):
	"""This doesn't seem to work and always returns 404?"""
	return call_api(f'https://game-server.geoguessr.com/api/competitive-streaks/{lobby}')
