# TODO: Put this in settings class
import sys

import pydantic

default_timeout = 30
"""Should definitely use a timeout, but I dunno what's a good one"""
max_connections: int | None = 1
"""Max simultaneous non-cached requests for async"""
forbid_extra_fields = sys.flags.dev_mode or 'debugpy' in sys.modules


class BaseModel(pydantic.BaseModel):
	model_config = pydantic.ConfigDict(extra='forbid' if forbid_extra_fields else 'allow')
