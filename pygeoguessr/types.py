"""Enums and type aliases used throughout the API"""

from enum import StrEnum
from typing import Annotated, Any, Literal

import pydantic
from annotated_types import Interval, Unit

RoundScore = Annotated[Annotated[int, Interval(ge=0, le=5000)], Unit('points')]
"""Indicates this represents an individual round score (up to 5000)"""
Metres = Annotated[float, Unit('m')]
"""Indicates this represents a distance in metres"""
ChallengeToken = str
"""Opaque ID for challenges"""
GameToken = str
"""Opaque ID for singleplayer games"""
LobbyToken = str
"""Opaque ID for multiplayer lobbies, sorta looks like a UUID"""
UserID = str
"""Opaque ID for users"""
MapSlug = str
"""Either sluggified version of a builtin map or an opaque ID, used to uniquely identify a map"""
PanoIDAsHexBytes = Annotated[str, pydantic.BeforeValidator(bytes.fromhex)]
"""Street View panorama ID, where the response encodes it as hex instead (this type uses validation to automatically convert it to a normal str as expected)"""
QuizID = str
"""Opaque ID for quizzes"""
PartyID = str
"""Opaque ID for parties"""


def country_code_validate(s: str | Any) -> str:
	if not isinstance(s, str):
		raise TypeError(s)
	if len(s) != 2:
		raise ValueError('Not 2 letters')
	return s.upper()


def us_state_code_validate(s: str) -> str:
	if len(s) != 2:
		raise ValueError('Not 2 letters')
	return f'US-{s.upper()}'


CountryCode = Annotated[str, pydantic.AfterValidator(country_code_validate)]
"""Uppercase ISO 3166-1 alpha-2 code (validation ensures it is uppercase for consistency with other libraries and the ISO standard, even if a lot of the APIs return lowercase codes)"""
USStateCode = Annotated[str, pydantic.AfterValidator(us_state_code_validate)]
"""Uppercase ISO 3166-2 subdivision code (validation automatically ensures it is US-<code>)"""


class GameMode(StrEnum):
	Standard = 'Standard'
	Streak = 'Streak'
	Duels = 'Duels'
	LiveChallenge = 'LiveChallenge'
	TeamDuels = 'TeamDuels'
	BattleRoyaleCountries = 'BattleRoyaleCountries'
	BattleRoyaleDistance = 'BattleRoyaleDistance'
	Bullseye = 'Bullseye'
	CityStreak = 'CompetitiveCityStreak'


class StreakType(StrEnum):
	CountryStreak = 'countrystreak'
	USStateStreak = 'usstatestreak'
	CustomStreak = 'customstreak'


class Medal(StrEnum):
	"""Medals as they appear in the API. TODO: Better type that can convert from int and str"""

	NoMedal = 'None'
	Bronze = 'Bronze'  # >5000
	Silver = 'Silver'  # >15000
	Gold = 'Gold'  # >22500
	Platinum = 'Platinum'  # 25000


class CompetitiveGameMode(StrEnum):
	NA = 'None'
	StandardDuels = 'StandardDuels'
	NoMoveDuels = 'NoMoveDuels'
	NoMovePanZoomDuels = 'NmpzDuels'


XPReason = Literal[
	'Score',
	'StreakExperience',
	'TutorialBonus',
	'SpeedBonus',
	'Flawless',
	'DifficultyBonus',
	'BigStreak',
	'SmallStreak',
	'HotStreak',
	'DailyChallengeParticipation',
	'DuelCompleted',
	'Marathon',
	'HpBonus',
	'Untouchable',
]


class UserType(StrEnum):
	Pro = 'Pro'
	Registered = 'Registered'
	Unlimited = 'Unlimited'
	Elite = 'Elite'
	Basic = 'Basic'
	ProMobile = 'ProMobile'
