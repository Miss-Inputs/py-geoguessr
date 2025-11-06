"""pydantic models used throughout the API"""

import datetime
from enum import IntEnum, StrEnum
from typing import Annotated, Any, Literal

import pydantic

from pygeoguessr.settings import BaseModel

# ruff: noqa: TC001
from .types import CompetitiveGameMode, CountryCode, GameToken, MapSlug, UserID, UserType, XPReason


class LatLng(BaseModel):
	lat: float
	lng: float


class UserPin(BaseModel):
	url: str
	"""pin/{blah}.png"""
	anchor: str
	"""CSS class? Have only ever seen this be "center-center" """
	isDefault: bool


class BattleRoyaleInfo(BaseModel):
	"""Not sure what this is and just presuming this is what br stands for, maybe remnants of a different BR game mode. Level seems to be 1-200"""

	level: int
	division: int


class CompetitiveDivision(IntEnum):
	"""From 71210-880a3b824e03d651.js func 75958"""

	Bronze = 10
	Silver = 20
	Gold = 30
	Master = 40
	Champion = 50


class DivisionInfo(pydantic.BaseModel):
	type: CompetitiveDivision
	startRating: int
	endRating: int


class UserCompetitiveInfo(pydantic.BaseModel):
	elo: int
	"""Not quite your rating? Seems to be anywhere from -501 to 1179"""
	rating: int
	lastRatingChange: int  # Can be negative
	division: DivisionInfo


class ProgressTitle(BaseModel):
	id: int
	"""10-410, always multiple of 10?"""
	tierId: int
	"""10-200, always multiple of 10?"""


class ProgressRankDivision(BaseModel):
	id: int
	divisionId: int
	tierId: int


class ProgressRank(BaseModel):
	rating: int
	rank: None  # TODO: type
	gamesLeftBeforeRanked: int
	division: ProgressRankDivision


class ProgressMedals(BaseModel):
	bronze: int
	silver: int
	gold: int
	platinum: int


class ProgressStreaks(BaseModel):
	brCountries: int
	brDistance: int
	csCities: int
	duels: int


class Progress(BaseModel):
	xp: int
	level: int
	levelXp: int
	"""XP needed to get to level"""
	nextLevel: int
	nextLevelXp: int
	title: ProgressTitle
	# These might be for each week of a season? Or maybe they are not actually in here, whoops
	# brRank: ProgressRank
	# csRank: ProgressRank
	# duelsRank: ProgressRank
	competitionMedals: ProgressMedals
	# streaks: ProgressStreaks


class UserAvatar(BaseModel):
	fullBodyPath: str


class Wallet(BaseModel):
	coins: int
	mobileCoins: int


class Club(BaseModel):
	tag: str
	clubId: str
	level: int


def _ignore_invalid_date(s: Any):
	if isinstance(s, str) and s == '0001-01-01T00:00:00.0000000Z':
		return None
	return s


_MaybeDate = Annotated[datetime.datetime | None, pydantic.BeforeValidator(_ignore_invalid_date)]
"""Some dates are always there in the API, but they use invalid dates in place of null values"""


class User(BaseModel):
	nick: str
	created: _MaybeDate
	isProUser: bool
	type: UserType
	consumedTrial: bool | None=None
	"""Maybe not there anymore"""
	isVerified: bool
	pin: UserPin
	fullBodyPin: str
	"""e.g. pin/{blah}.png"""
	color: Literal[0]
	"""??? just 0? What is it for"""
	url: str
	"""Profile page, without the geoguessr.com/ part"""
	id: UserID
	countryCode: CountryCode | None
	"""Hmm, this can have "xf" (e.g. BOKSA/5b6ae3177135fa0e48b4df1f) which doesn't seem to display as a flag"""
	br: BattleRoyaleInfo
	club: Club | None = None

	# I'm guessing these ones wouldn't be static and would be dependent on what contains the user info?
	streakProgress: None
	explorerProgress: None
	dailyChallengeProgress: Literal[0]  # TODO What is this
	progress: Progress
	competitive: UserCompetitiveInfo

	lastNameChange: datetime.datetime
	"""Can also be '2000-01-01T00:00:00.0000000Z', or sometimes just '2000-01-01T00:00:00.000'"""
	isBanned: bool  # Interestingly this includes the GeoGuessr user that posted the official learning challenges from Twitter
	chatBan: bool
	nameChangeAvailableAt: datetime.datetime | None
	"""Presumably a timestamp? But it's null even for get_logged_in_user_info()"""
	avatar: UserAvatar
	"""Maybe not always filled in?"""
	isBotUser: bool

	suspendedUntil: datetime.datetime | None
	wallet: Wallet | None
	"""None if not you"""
	flair: int
	"""Usually 0 if no flair, have also seen 2 and 6, could mean something"""
	lastNickOrCountryChange: datetime.datetime
	"""May be midnight 1 Jan 2000 if never changed"""
	isCreator: bool
	isAppAnonymous: bool
	customImage: str | None
	"""e.g. pin/whatever.png"""
	lastClaimedLevel: int
	steamUserType: int | None = None  # why


class Onboarding(BaseModel):
	tutorialToken: GameToken
	tutorialState: Literal['Done', 'Unknown']


class UserDetails(User):
	onboarding: Onboarding | None = None
	"""Tutorial onboarding info, but this might be not there anymore anyway"""


class MapBounds(BaseModel):
	"""bounds item of MapDetails"""

	min: LatLng
	max: LatLng

	@pydantic.computed_field  # type: ignore[misc]
	@property
	def width(self) -> float:
		# We use abs as max might not necessarily be greater than min, in case of crossing hemispheres but also sometimes just weirdness
		return abs(self.max.lng - self.min.lng)

	@pydantic.computed_field  # type: ignore[misc]
	@property
	def height(self) -> float:
		# We use abs as max might not necessarily be greater than min, in case of sometimes just weirdness
		return abs(self.max.lat - self.min.lat)


class MapAvatar(BaseModel):
	"""Components of the map avatar, all of these are preset strings"""

	background: str
	decoration: str
	ground: str
	landscape: str


class MapImages(BaseModel):
	backgroundLarge: str | None
	"""URL fragment, e.g. map/{something}.png"""
	incomplete: bool


class MapSelectionMode(IntEnum):
	Unknown = 0
	Coordinates = 1
	Polygons = 2


class MapDifficulty(IntEnum):
	"""Values for map difficultyLevel"""

	VERY_EASY = 1  # >20K
	EASY = 2  # >17K
	MEDIUM = 3  # >10K
	HARD = 4  # presumably over 5K, maybe?
	VERY_HARD = 5


class Map(BaseModel):
	id: MapSlug
	"""Usually the same as the map slug, except for official maps, where it will be an opaque ID instead of the sluggified name"""
	name: str
	slug: MapSlug
	description: str | None
	url: str
	"""/maps/{slug}"""
	playUrl: str
	"""/maps/{slug}.play"""
	published: bool
	banned: bool
	images: MapImages
	bounds: MapBounds
	customCoordinates: None  # TODO: Type, I think only present for your own maps
	coordinateCount: str | None
	"""If > 250, rounded to 500/nearest thousand/million/etc and abbrev'd"""
	regions: None  # TODO: Type, only present for your own maps, for polygon mode
	creator: User | None
	"""Only if isUserMap, full whole entire user info dict"""
	createdAt: _MaybeDate
	updatedAt: datetime.datetime
	numFinishedGames: int
	likedByUser: bool | None  # TODO: Not sure, might be a bool? But why is it null most of the time
	averageScore: int = pydantic.Field(ge=0)
	"""Average score of all normal games on this map"""
	avatar: MapAvatar
	difficulty: Literal['VERY EASY', 'EASY', 'MEDIUM', 'HARD', 'VERY HARD'] | None
	"""String version of difficultyLevel, displayed on the map page"""
	difficultyLevel: MapDifficulty
	"""How difficult this map seems to be as decided by averageScore"""
	highscore: None  # TODO: Why is this not returning anything? Shouldn't that work that way? Maybe the API endpoint does not care about logged in info
	isUserMap: bool
	"""True if this is created by any user, else it will say it is created by "GeoGuessr" """
	highlighted: bool
	free: bool
	panoramaProvider: Literal['Unknown', 'StreetView', 'Mapillary']
	"""These values are listed in chunk 5887 function 93949, I don't think anything except StreetView will ever be seen"""
	inExplorerMode: bool
	maxErrorDistance: int
	likes: int
	locationSelectionMode: MapSelectionMode
	"""How the map was made, and therefore how locations are chosen. I don't know how official maps (0) work exactly in that sense, maybe it's a secret"""
	tags: list[str]


class LevelInfo(BaseModel):
	level: int
	xpStart: int


class XPProgressionTitle(BaseModel):
	id: int
	tierId: int
	minimumLevel: int | None = None
	"""Seems to only be present if the progression is from a singleplayer game"""
	name: str | None = None
	"""Seems to only be present if the progression is from a singleplayer game"""


class XPProgression(BaseModel):
	xp: int
	currentLevel: LevelInfo
	nextLevel: LevelInfo
	currentTitle: XPProgressionTitle


class XPAward(BaseModel):
	xp: int
	reason: XPReason
	count: int


class XPAwardInfo(BaseModel):
	totalAwardedXp: int
	xpAwards: list[XPAward]


class SeasonProgress(BaseModel):
	qualificationPointsBefore: int
	qualificationPointsAfter: int
	seasonPointsBefore: int
	seasonPointsAfter: int
	seasonBasePointsBefore: int
	seasonBasePointsAfter: int
	currentGameModeSeasonPointsBefore: int
	currentGameModeSeasonPointsAfter: int
	currentGameModeSeasonBasePointsBefore: int
	currentGameModeSeasonBasePointsAfter: int
	awardBefore: int
	awardAfter: int
	gamesPlayed: int


class CompetitiveProgress(BaseModel):
	ratingBefore: int
	ratingAfter: int
	divisionBefore: DivisionInfo
	divisionAfter: DivisionInfo


class BucketSortedBy(StrEnum):
	Points = 'Points'
	Rating = 'Rating'


class RankedSystemProgress(BaseModel):
	points: dict[
		Literal['winRounds', 'winWithinWeeklyCap', 'firstWinOfTheDay', 'winBeyondWeeklyCap'], int
	]  # some keys not always there?
	totalWeeklyPoints: int
	weeklyCap: int
	gamesPlayedWithinWeeklyCap: int
	positionBefore: int | None
	positionAfter: int
	ratingBefore: int | None
	ratingAfter: int | None
	winStreak: int
	bucketSortedBy: BucketSortedBy
	"""Not sure what this is exactly for"""
	gameMode: CompetitiveGameMode
	gameModeRatingBefore: int | None
	gameModeRatingAfter: int | None
	gameModeGamesPlayed: int | None
	gameModeGamesRequired: int | None
	placementGamesPlayed: int | None
	placementGamesRequired: int | None


class Empty(BaseModel):
	"""huh???"""


class RankedTeamDuelsProgress(BaseModel):
	ratingBefore: int
	ratingAfter: int
	points: Empty
	totalWeeklyPoints: int
	weeklyCap: int
	gamesPlayedWithinWeeklyCap: int
	positionBefore: int | None
	positionAfter: int
	winStreak: int
	bucketSortedBy: BucketSortedBy


class ProgressChange(BaseModel):
	xpProgressions: list[XPProgression]
	awardedXp: XPAwardInfo
	medal: Literal[0, 'None']  # TODO: What actually is this? Not a medal in the usual sense

	seasonProgress: SeasonProgress | None = None
	"""Only for multiplayer games, though does not seem to be a field anymore"""
	competitiveProgress: CompetitiveProgress | None
	"""Only for multiplayer games, though seems to now just be always null"""
	rankedSystemProgress: RankedSystemProgress | None
	rankedTeamDuelsProgress: RankedTeamDuelsProgress | None
	quickplayDuelsProgress: Any | None  # nah don't care
