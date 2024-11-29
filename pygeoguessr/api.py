import asyncio
import contextlib
import logging
import os
import warnings
from collections.abc import Mapping
from functools import cache
from pathlib import Path
from typing import Any

import aiohttp
import aiohttp_client_cache
import aiohttp_client_cache.cache_control
import pydantic_core
import requests
import requests_cache
from aiohttp.client_exceptions import ClientResponseError
from aiohttp_client_cache.session import CachedSession as CachedAsyncSession
from requests.cookies import RequestsCookieJar

from pygeoguessr import settings

from .filesystem_cache_with_dirs import FileCacheWithDirectories

user_agent = 'py-geoguessr'

logger = logging.getLogger(__name__)


@cache
def get_ncfa_cookie():
	return os.environ.get('NCFA_COOKIE', '')


@cache
def _get_cache():
	return FileCacheWithDirectories('geoguessr_api', use_cache_dir=True)


@cache
def get_cookie_jar():
	cookies = RequestsCookieJar()
	cookies.set('_ncfa', get_ncfa_cookie(), domain='www.geoguessr.com')
	return cookies


@cache
def get_default_session(*, cached: bool = True) -> requests.Session:
	# TODO: Should this really use functools.cache? Be careful we aren't leaving connections open
	sesh = (
		requests_cache.CachedSession(
			'geoguessr_api', _get_cache(), stale_if_error=True, allowable_methods={'GET', 'POST'}
		)
		if cached
		else requests.Session()
	)
	sesh.headers['User-Agent'] = user_agent
	return sesh


@cache
def _get_async_cache():
	cache_path = Path('~/.cache/geoguessr-async')
	# We need POST for e.g. the geocoding API, anything that actually changes things should just use DO_NOT_CACHE
	return aiohttp_client_cache.FileBackend(cache_path, allowed_methods={'GET', 'POST'})


async def clear_expired_cache_async():
	await _get_async_cache().delete_expired_responses()


def get_default_async_session(*, cached: bool = True) -> aiohttp.ClientSession:
	"""Gets a session for use with the async functions, which may be a cached session by default but optionally not.

	Returns:
	        ClientSession or CachedSession"""
	if not cached:
		return aiohttp.ClientSession()
	with warnings.catch_warnings(action='ignore', category=DeprecationWarning):
		# aiohttp warns about CachedSession setting attributes, but that doesn't have anything to do with us other than we use it
		session = CachedAsyncSession(cache=_get_async_cache())
	session.headers['User-Agent'] = user_agent
	return session


class NotFoundError(requests.HTTPError, ClientResponseError):
	"""Easier to catch only 404 this way"""


class UnauthorizedError(requests.HTTPError, ClientResponseError):
	"""Easier to catch only 401 this way"""


def _parse_error_message(text: str | None, reason: str | None):
	if text:
		try:
			response_json = pydantic_core.from_json(text)
		except ValueError:
			# not always JSON
			return f'{reason}: {text}'
		message = response_json.pop('message', None)
		error = response_json.pop('error', None)
		payload = response_json.pop('payload', None)
		args = f'{error or reason}:'
		if message:
			args += f' {message}'
		if payload:
			args += f', payload: {payload}'
		if response_json:
			args += f', other: {response_json}'
		return args
	return reason


def call_api(
	url: str,
	params: Mapping[str, str | int | float] | None = None,
	expiry: Any | None = None,
	method: str = 'GET',
	json_body: Mapping[str, Any] | None = None,
	*,
	needs_auth: bool = False,
	do_not_cache: bool = False,
) -> str:
	"""
	Arguments:
	        url: URL to yoink
	        params: Query params
	        expiry: Custom expire_after param

	Raises:
			UnauthorizedError: On 401 errors
	        NotFoundError: On 404 errors

	Returns:
	        JSON as str
	"""
	if do_not_cache:
		expiry = requests_cache.DO_NOT_CACHE
	# TODO: Could have a session parameter here I guess
	sesh = get_default_session()
	kwargs = {}
	if expiry and isinstance(sesh, requests_cache.CachedSession):
		kwargs['expire_after'] = expiry
		if expiry == requests_cache.DO_NOT_CACHE:
			kwargs['force_refresh'] = True
	kwargs['cookies'] = {'_ncfa': get_ncfa_cookie()} if needs_auth else {}

	if '://' not in url:
		url = f'https://www.geoguessr.com/{url.removeprefix("/")}'

	response = sesh.request(
		method, url, params=params, timeout=settings.default_timeout, json=json_body, **kwargs
	)
	text = response.text
	if not response.ok:
		args = _parse_error_message(text, response.reason)
		if response.status_code == 404:
			raise NotFoundError(args, response=response)
		if response.status_code == 401:
			raise UnauthorizedError(args, response=response)
	response.raise_for_status()
	return text


_semaphore = (
	contextlib.nullcontext()
	if settings.max_connections is None
	else asyncio.Semaphore(settings.max_connections)
)


async def call_api_async(
	url: str,
	session: aiohttp.ClientSession | None = None,
	params: Mapping[str, str | int | float] | None = None,
	expiry: Any | None = None,
	method: str = 'GET',
	json_body: Mapping[str, Any] | None = None,
	*,
	needs_auth: bool = False,
	do_not_cache: bool = False,
):
	"""
	Arguments:
	        url: URL to yoink
	        params: Query params
	        expiry: Custom expire_after param

	Raises:
			UnauthorizedError: On 401 errors
	        NotFoundError: On 404 errors

	Returns:
	        JSON as str
	"""
	if session is None:
		#TODO: Does this actually work, or does it always create a race condition with the redirects database?
		async with get_default_async_session() as default_session:
			return await call_api_async(url, default_session, params, expiry, method, json_body)

	if '://' not in url:
		url = f'https://www.geoguessr.com/{url.removeprefix("/")}'

	kwargs = {}
	cache_disabler = contextlib.nullcontext()
	if expiry == aiohttp_client_cache.cache_control.DO_NOT_CACHE:
		do_not_cache = True
	if do_not_cache and isinstance(session, CachedAsyncSession):
		# I couldn't figure out how to get it to work how I think it works, so just conditionally disable the cache if we say do not cache
		cache_disabler = session.disabled()
		in_cache = False
	else:
		in_cache = (
			await session.cache.has_url(url, method, params=params, json=json_body)
			if isinstance(session, CachedAsyncSession)
			else False
		)

	sem = contextlib.nullcontext() if in_cache else _semaphore
	if expiry:
		kwargs['expire_after'] = expiry
	cookies = {'_ncfa': get_ncfa_cookie()} if needs_auth else {}

	async with (
		cache_disabler,
		sem,
		session.request(
			method, url, params=params, json=json_body, cookies=cookies, **kwargs
		) as response,
	):
		text = await response.text()
		if not response.ok:
			args = _parse_error_message(text, response.reason)
			if response.status == 404:
				raise NotFoundError(args)
			if response.status == 401:
				raise UnauthorizedError(args)
		response.raise_for_status()
		return text
