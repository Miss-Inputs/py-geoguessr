from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Literal

#ruff: noqa: TCH001, TCH002
import pydantic

from pygeoguessr.api import call_api, call_api_async
from pygeoguessr.settings import BaseModel
from pygeoguessr.types import CountryCode, QuizID, UserID

if TYPE_CHECKING:
	import aiohttp


class QuizStats(BaseModel):
	numRounds: int
	questionTypeCount: dict[
		Literal['quizQuestion', 'fixedPanorama', 'staticContent'], pydantic.PositiveInt
	]
	estimatedPlayingTime: timedelta
	maxTotalPoints: pydantic.PositiveInt


class QuizCreator(BaseModel):
	id: UserID | Literal['']
	nick: str
	avatarPath: str
	"""URL fragment, or empty string"""
	flair: int


class QuizDetails(BaseModel):
	id: QuizID
	name: str
	description: str
	image: str
	"""quiz/{blah}.png"""
	created: datetime
	stats: QuizStats
	isVisible: bool
	isHighlighted: bool
	alreadyPlayed: bool
	background: None
	owner: None
	creator: QuizCreator
	isLeaderboardPublic: bool


def get_quiz_details(quiz: QuizID) -> QuizDetails:
	return QuizDetails.model_validate_json(call_api(f'api/v3/quizzes/{quiz}'))


async def get_quiz_details_async(
	quiz: QuizID, session: 'aiohttp.ClientSession | None' = None
) -> QuizDetails:
	return QuizDetails.model_validate_json(await call_api_async(f'api/v3/quizzes/{quiz}', session))


class QuizPlayer(BaseModel):
	userId: UserID
	nick: str
	flair: int
	avatarPath: str
	countryCode: CountryCode


class QuizLeaderboardItem(BaseModel):
	user: QuizPlayer
	points: int
	time: timedelta
	"""Usually just 0"""
	playedAt: datetime


class QuizLeaderboard(BaseModel):
	friends: list[QuizLeaderboardItem]
	total: list[QuizLeaderboardItem]
	you: None  # TODO: What type would this ever be


def get_quiz_leaderboards(quiz: QuizID):
	response = call_api(f'api/v3/quizzes/{quiz}/leaderboards/game', needs_auth=True)
	return QuizLeaderboard.model_validate_json(response)


async def get_quiz_leaderboards_async(quiz: QuizID, session: 'aiohttp.ClientSession | None' = None):
	response = await call_api_async(f'api/v3/quizzes/{quiz}/leaderboards/game', session, needs_auth=True)
	return QuizLeaderboard.model_validate_json(response)
