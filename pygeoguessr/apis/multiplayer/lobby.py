from datetime import datetime, timedelta
from enum import StrEnum
from typing import TYPE_CHECKING, Annotated, Literal

import pydantic

from pygeoguessr.api import call_api, call_api_async
from pygeoguessr.settings import BaseModel
from pygeoguessr.types import CompetitiveGameMode, LobbyToken, MapSlug, PartyID, QuizID, UserID
from pygeoguessr.utils import x_or_none

# ruff: noqa: TC001
from .common import MovementOptions, MultiplayerGameType, Player

if TYPE_CHECKING:
	import aiohttp


class AllowedCommunication(StrEnum):
	EmotesOnly = 'EmotesOnly'
	TextMessages = 'TextMessages'
	TeamTextMessages = 'TeamTextMessages'


MaybeQuizID = Annotated[QuizID | None, pydantic.BeforeValidator(x_or_none)]


class BaseLobby(BaseModel):
	gameLobbyId: LobbyToken
	title: str
	type: Literal['None', 'Unrated']
	status: Literal['Open', 'Closed']
	numPlayersJoined: int
	totalSpots: int
	numOpenSpots: int
	minPlayersRequired: int
	playerIds: list[UserID]
	players: list[Player]
	visibility: Literal['Public', 'Private']
	closingTime: datetime | None
	timestamp: datetime
	"""This seems to actually just be when you called get_lobby_details"""
	owner: str
	host: Player | None
	isAutoStarted: bool
	canBeStartedManually: bool
	isRated: bool
	"""Is ranked"""
	competitionId: str
	"""May be an empty string"""
	partyId: PartyID | None
	createdAt: datetime
	shareLink: pydantic.HttpUrl
	teams: list[dict[Literal['name'], str]]
	groupEventId: str
	quizId: MaybeQuizID  # Raw value can be empty string
	hostParticipates: bool
	isSinglePlayer: bool
	tripId: str
	blueprintId: str | None
	tournament: None
	allowedCommunication: AllowedCommunication
	accessToken: str
	mapName: str
	gameContext: Literal['career', 'public_unrated', 'party', 'party_v2']
	competitiveGameMode: CompetitiveGameMode


class DuelGameOptions(MovementOptions):
	mapSlug: MapSlug
	roundTime: timedelta
	initialHealth: int
	maxRoundTime: timedelta
	maxNumberOfRounds: int
	"""0 for no limit"""
	disableMultipliers: bool
	multiplierIncrement: int = pydantic.Field(examples=[5])
	disableHealing: bool
	individualInitialHealth: bool
	initialHealthTeamOne: int
	initialHealthTeamTwo: int


class BattleRoyaleGameOptions(MovementOptions):
	mapSlug: MapSlug
	roundTime: timedelta
	initialLives: int


class BattleRoyaleCountriesGameOptions(BattleRoyaleGameOptions):
	powerUp5050: bool
	powerUpSpy: bool


class CityStreakGameOptions(MovementOptions):
	duration: timedelta


class BullseyeGameOptions(MovementOptions):
	mapSlug: MapSlug
	roundTime: timedelta


class LiveChallengeOptions(MovementOptions):
	mapSlug: MapSlug
	roundTime: timedelta
	roundCount: int


class BullseyeLobby(BaseLobby):
	gameType: Literal[MultiplayerGameType.Bullseye]
	gameOptions: BullseyeGameOptions


class DuelLobby(BaseLobby):
	gameType: Literal[MultiplayerGameType.Duels]
	gameOptions: DuelGameOptions


class LiveChallengeLobby(BaseLobby):
	gameType: Literal[MultiplayerGameType.LiveChallenge]
	gameOptions: LiveChallengeOptions


class BattleRoyaleDistanceLobby(BaseLobby):
	gameType: Literal[MultiplayerGameType.Distance]
	gameOptions: BattleRoyaleGameOptions


class BattleRoyaleCountriesLobby(BaseLobby):
	gameType: Literal[MultiplayerGameType.Countries]
	gameOptions: BattleRoyaleCountriesGameOptions


class CityStreakLobby(BaseLobby):
	gameType: Literal[MultiplayerGameType.CityStreak]
	gameOptions: CityStreakGameOptions


class TeamDuelsLobby(BaseLobby):
	gameType: Literal[MultiplayerGameType.TeamDuels]
	gameOptions: DuelGameOptions


Lobby = Annotated[
	BattleRoyaleCountriesLobby
	| BattleRoyaleDistanceLobby
	| BullseyeLobby
	| CityStreakLobby
	| DuelLobby
	| LiveChallengeLobby
	| TeamDuelsLobby,
	pydantic.Field(discriminator='gameType'),
]
LobbyAdapter = pydantic.TypeAdapter(Lobby)


def get_lobby_details(lobby: LobbyToken) -> Lobby:
	return LobbyAdapter.validate_json(
		call_api(f'https://game-server.geoguessr.com/api/lobby/{lobby}')
	)


async def get_lobby_details_async(
	lobby: LobbyToken, session: 'aiohttp.ClientSession | None' = None
) -> Lobby:
	return LobbyAdapter.validate_json(
		await call_api_async(f'https://game-server.geoguessr.com/api/lobby/{lobby}', session)
	)
