from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING, Literal

import pydantic

#ruff: noqa: TC001, TC002
from pygeoguessr.api import NotFoundError, call_api, call_api_async
from pygeoguessr.apis.multiplayer.lobby import AllowedCommunication
from pygeoguessr.settings import BaseModel
from pygeoguessr.types import LobbyToken, PartyID, UserID

if TYPE_CHECKING:
	import aiohttp


class PartyStatus(StrEnum):
	Created = 'Created'


class PartyCreator(BaseModel):
	id: UserID
	name: str
	avatarUrl: str
	"""URL fragment = pin/{something}.png"""
	titleTierId: int  # CompetitiveDivision?
	"""e.g. 40"""
	flair: int
	isGuest: bool


class PartyStyle(BaseModel):
	background: Literal['Blue']


class PartyGame(BaseModel):
	"""Yep this just holds one field"""

	gameId: LobbyToken


class Party(BaseModel):
	id: PartyID
	shareLink: pydantic.HttpUrl
	allowedCommunication: AllowedCommunication
	name: str
	status: PartyStatus
	createdAt: datetime
	creator: PartyCreator
	style: PartyStyle
	openGames: list[PartyGame]
	activeGames: list[PartyGame]
	bannedPlayers: list[
		UserID
	]  # TODO have only seen this be an empty list, check what type it actually is (just assuming)
	requiresPassword: bool
	playerCount: int
	numSpotsRemaining: int
	maxNumSpots: int
	allowGuests: bool


class PartyResponse(BaseModel):
	party: Party
	hasJoined: bool


def get_party_details(party: 'PartyID'):
	"""Seems to return none for ad-hoc parties created with guest users, for example"""
	try:
		response = call_api(f'api/v4/parties/{party}')
	except NotFoundError:
		return None
	else:
		return PartyResponse.model_validate_json(response)


async def get_party_details_async(party: 'PartyID', session: 'aiohttp.ClientSession | None' = None):
	"""Seems to return none for ad-hoc parties created with guest users, for example"""
	try:
		response = await call_api_async(f'api/v4/parties/{party}', session)
	except NotFoundError:
		return None
	else:
		return PartyResponse.model_validate_json(response)


# TODO: # https://geoguessr.com/api/v4/parties/8bf7366a-ece1-4449-84a5-9be37b586d7c/leaderboard -> paginated (has "paginateFrom" field)
# TODO: #https://geoguessr.com/api/v4/parties/8bf7366a-ece1-4449-84a5-9be37b586d7c/game-lobbies -> does this need a game to be played to work?
