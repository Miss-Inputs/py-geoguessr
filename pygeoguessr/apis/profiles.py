from typing import TYPE_CHECKING

from pygeoguessr.api import call_api, call_api_async
from pygeoguessr.models import UserDetails, Wallet

if TYPE_CHECKING:
	import aiohttp


def get_logged_in_user() -> UserDetails:
	return UserDetails.model_validate_json(call_api('api/v3/profiles/me', needs_auth=True))


async def get_logged_in_user_async(session: 'aiohttp.ClientSession | None' = None) -> UserDetails:
	return UserDetails.model_validate_json(
		await call_api_async('api/v3/profiles/me', session, needs_auth=True)
	)


def get_wallet() -> Wallet:
	"""Gets wallet for logged in user"""
	return Wallet.model_validate_json(
		call_api('api/v3/profiles/wallet', do_not_cache=True, needs_auth=True)
	)


async def get_wallet_async(session: 'aiohttp.ClientSession | None' = None) -> Wallet:
	"""Gets wallet for logged in user"""
	return Wallet.model_validate_json(
		await call_api_async('api/v3/profiles/wallet', session, do_not_cache=True, needs_auth=True)
	)


# TODO: # TODO: https://geoguessr.com/api/v3/profiles - User details of logged in user, and also email and settings etc
