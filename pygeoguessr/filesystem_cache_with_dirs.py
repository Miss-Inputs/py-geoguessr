from collections.abc import Iterable, Iterator
from pathlib import Path

import requests
import requests_cache
from pydantic_core import Url
from requests_cache import AnyRequest, FileCache, FileDict, SerializerType


class FileCacheWithDirectories(FileCache):
	"""Like requests_cache filesystem backend, but puts files in subdirectories"""

	def __init__(
		self,
		cache_name='http_cache',
		use_temp: bool = False,  # noqa: FBT001, FBT002 #It's how requests_cache works
		decode_content: bool = True,  # noqa: FBT001, FBT002
		serializer: 'SerializerType | None' = None,
		**kwargs,
	):
		super().__init__(cache_name, use_temp, decode_content, serializer, **kwargs)
		skwargs = {'serializer': serializer, **kwargs} if serializer else kwargs
		self.responses: _FileDictWithDirectories = _FileDictWithDirectories(  # type:ignore[override]
			cache_name, use_temp=use_temp, decode_content=decode_content, **skwargs
		)

	def create_key(
		self, request: 'AnyRequest', match_headers: Iterable[str] | None = None, **_kwargs
	) -> str:
		# TODO: Can we have the cookie as part of the cache? Should we?
		if not request.url:
			return 'wat'
		url = Url(request.url)
		key = url.path.removeprefix('/') if url.path else (url.host or 'wat')

		if (
			isinstance(request, (requests.Request, requests_cache.CachedRequest))
			and request.cookies
		):
			key += ' '.join({f'{k}={v}' for k, v in request.cookies.iteritems()})

		query = ' '.join(f'{k}={v}' for k, v in sorted(url.query_params()) if k != 'api_key')
		if query:
			key += f'/{query}'
		return key


class _FileDictWithDirectories(FileDict):
	def _path(self, key) -> Path:
		return self.cache_dir.joinpath(key).with_suffix(self.extension)

	def __setitem__(self, key, value):
		with self._lock:
			self._path(key).parent.mkdir(parents=True, exist_ok=True)
		return super().__setitem__(key, value)

	def __delitem__(self, key):
		with self._try_io():
			path = self._path(key)
			path.unlink()
			if path.parent != self.cache_dir and len(list(path.parent.iterdir())) == 0:
				path.parent.rmdir()

	def paths(self) -> Iterator[Path]:
		with self._lock:
			return self.cache_dir.rglob(f'*{self.extension}')
