"""Fancy 3D avatars, if you really wanted to get info on that"""

import datetime
from enum import Enum
from typing import TYPE_CHECKING

import pydantic

from pygeoguessr.api import call_api, call_api_async
from pygeoguessr.settings import BaseModel

if TYPE_CHECKING:
	import aiohttp

	from pygeoguessr.types import UserID


class AvatarAssetSlot(Enum):
	Hair = 1
	Tops = 2
	"""Shirts, suits, hoodies, jackets, etc, dresses go in here too"""
	Bottoms = 3
	"""Pants, skirts, etc"""
	Accessories = 4
	"""Glasses, masks, may hide mouth"""
	Eyelashes = 5
	Eyes = 6
	"""??? purrhaps"""
	Hats = 7
	"""Anything worn as a hat, may hide hair or mouth/face"""
	Skin = 8
	"""Skin colour is selectable, so it has a slot too, type might always be SKINBASIC"""
	Mouths = 9
	"""???? maybe, or maybe the whole entire face, or beards?"""
	FullBodyOutfit = 10
	"""Overalls, etc; may hide tops and bottoms"""


class AvatarAsset(BaseModel):
	id: str
	"""Might be just type + _ + variant"""
	group: str = pydantic.Field(examples=['Holiday celebration', '', 'vincent and mia', 'Summer'])
	slot: AvatarAssetSlot
	"""Which part of the avatar this item occupies"""
	hides: list[AvatarAssetSlot]
	"""Other parts of the avatar that aren't rendered while this is shown, e.g. masks hide mouth"""
	morphTarget: str = pydantic.Field(examples=['', 'Hat01'])
	"""??? I would think if this is Hat01 it would tie the wearer's hair back to fit as hats do in this game, but otherwise I dunno"""
	type: str = pydantic.Field(
		examples=[
			'BOW',
			'DIADELOSMUERTOSMASK',
			'EGGEASTERCRACKED',
			'SHIRTCASUALLONG',
			'ANIMESTYLE01',
		]
	)
	variant: str = pydantic.Field(examples=['WIN', 'PINK', 'ORANGE', 'FLOWERSBLUEGREEN'])
	"""What colour this is, etc, grouped together in the avatar editor"""
	mesh: str
	"""URL fragment starting with mesh/ pointing to .fbx file"""
	meshGlb: str
	"""URL fragment starting with mesh/ pointing to .glb file"""
	texture: str
	"""URL fragment starting with texture/ pointing to webp/png/etc file"""
	icon: str
	"""URL fragment starting with avatarasseticon/ pointing to webp/png/etc file"""
	priority: int
	"""??? Not at all sure what this refers to, seems to be from 0 to 8, rendering priority? Ordering in some list? Dunno"""
	unlocked: bool = False
	"""Shows if you have it or not, probably"""
	category: int | None = None
	"""??? 1, 2, or not present at all?"""
	published: bool = True
	"""??? This field is only here from the shop"""


class BadgeLevelImage(BaseModel):
	diffuseMapPath: str
	"""URL fragment, starts with badge/, points to image file"""
	depthMapPath: str
	"""URL fragment, starts with badge/, points to image file"""


class BadgeProgression(BaseModel):
	current: int
	target: int


class EquippedBadge(BaseModel):
	id: str = pydantic.Field(
		examples=['gdJ0hoNtoq0JkYUFFyUJcYPt4aBIOd4E', '1VR5frpMc6hlIHMapBdadpouDa9LRLTV']
	)
	name: str = pydantic.Field(examples=['Explorer', 'Daily Challenge'])
	hint: str = pydantic.Field(examples=['Explore classic maps', 'Play the Daily Challenge'])
	description: str = pydantic.Field(
		examples=['Play 1000 classic games', 'A year of daily challenges']
	)
	imagePath: str
	"""URL fragment, starts with badge/, points to image file"""
	hasLevels: bool
	category: str = pydantic.Field(examples=['Special'])
	applyRounding: bool
	level: int  # maybe None if not hasLevels?
	levelImage: BadgeLevelImage  # maybe None if not hasLevels?
	awarded: datetime.datetime
	progression: BadgeProgression | None
	"""None if this badge has no levels (probably), or is at the max level"""
	totalLevels: int  # maybe None if not hasLevels?
	isSunsetted: bool
	nextLevelDescription: str = pydantic.Field(
		examples=['Play 2500 classic games', '', "You're one of the finest map makers"]
	)
	"""If this badge is at the max level, could be an empty string, or a congratulatory message"""
	nextLevelImage: BadgeLevelImage | None


class UserAvatarInfo(BaseModel):
	equipped: list[AvatarAsset]
	"""List of all avatar items the user has equipped, theoretically one per slot, whether purchasable or inbuilt things like eyes or skin colour"""
	equippedBadge: EquippedBadge | None
	"""None if the user does not display a badge"""


def get_user_avatar(user_id: 'UserID'):
	response = call_api(f'https://www.geoguessr.com/api/v4/avatar/user/{user_id}')
	return UserAvatarInfo.model_validate_json(response)


async def get_user_avatar_async(user_id: 'UserID', session: 'aiohttp.ClientSession|None' = None):
	response = await call_api_async(
		f'https://www.geoguessr.com/api/v4/avatar/user/{user_id}', session
	)
	return UserAvatarInfo.model_validate_json(response)


def get_current_user_avatar():
	"""Requires authentication, gets avatar for currently logged in user"""
	response = call_api('https://www.geoguessr.com/api/v4/avatar/', needs_auth=True)
	return UserAvatarInfo.model_validate_json(response)


async def get_current_user_avatar_async(session: 'aiohttp.ClientSession|None' = None):
	"""Requires authentication, gets avatar for currently logged in user"""
	response = await call_api_async('https://www.geoguessr.com/api/v4/avatar/', session, needs_auth=True)
	return UserAvatarInfo.model_validate_json(response)


# TODO: https://geoguessr.com/api/v4/avatar/assets -> all available
# TODO: # https://www.geoguessr.com/api/v4/avatar/assets/inventory - All your avatar items
