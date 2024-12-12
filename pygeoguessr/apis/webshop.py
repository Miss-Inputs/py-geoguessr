from datetime import datetime
from enum import IntEnum
from typing import TYPE_CHECKING

import pydantic

# ruff: noqa: TC001
from pygeoguessr.api import call_api, call_api_async
from pygeoguessr.apis.avatars import AvatarAsset
from pygeoguessr.settings import BaseModel
from pygeoguessr.types import CountryCode

if TYPE_CHECKING:
	import aiohttp


class CoinClaimInfo(BaseModel):
	"""Returned from get_claimable_free_coins"""

	claimed: bool
	coinAmount: int
	nextPossibleClaim: datetime


class CoinClaimStatus(IntEnum):
	OK = 0
	AlreadyClaimedToday = 9


class CoinClaimResponse(BaseModel):
	"""Returned from claim_free_coins"""

	coinsGiven: int
	status: CoinClaimStatus


def get_claimable_free_coins() -> CoinClaimInfo:
	# May or may not have an argument? Probably not though
	return CoinClaimInfo.model_validate_json(
		call_api('api/v4/webshop/daily-shop-claim', do_not_cache=True, needs_auth=True)
	)


async def get_claimable_free_coins_async(
	session: 'aiohttp.ClientSession | None' = None,
) -> CoinClaimInfo:
	# May or may not have an argument? Probably not though
	return CoinClaimInfo.model_validate_json(
		await call_api_async(
			'api/v4/webshop/daily-shop-claim', session, do_not_cache=True, needs_auth=True
		)
	)


def claim_free_coins() -> CoinClaimResponse:
	# Of course, needs login or you get a 404 (not a 401, which is weird, but eh)
	return CoinClaimResponse.model_validate_json(
		call_api(
			'api/v4/webshop/daily-shop-claim', method='POST', do_not_cache=True, needs_auth=True
		)
	)


async def claim_free_coins_async(
	session: 'aiohttp.ClientSession | None' = None,
) -> CoinClaimResponse:
	# Of course, needs login or you get a 404 (not a 401, which is weird, but eh)
	return CoinClaimResponse.model_validate_json(
		await call_api_async(
			'api/v4/webshop/daily-shop-claim',
			session,
			method='POST',
			do_not_cache=True,
			needs_auth=True,
		)
	)


class Price(BaseModel):
	currency: str
	"""Currency code for real money cost, if it is purchasable with real money, or None if it is purchased with coins instead"""
	amount: float
	"""Amount of currency for real money cost, if it is purchasable with real money, or None if it is purchased with coins instead"""


class PresentationGroup(BaseModel):
	avatarAssetIds: list[str]
	"""Seems to just be the id field in avatarAssets"""


class ShopProduct(BaseModel):
	productId: str = pydantic.Field(examples=['easter-bundle', 'pantslongbasic_varsitywhite'])
	title: str = pydantic.Field(
		examples=['shop.easter-bundle-title', 'shop.title-pantslongbasic-varsitywhite']
	)
	"""Localization key for title"""
	description: str = pydantic.Field(
		examples=['shop.easter-bundle-description', 'shop.description-pantslongbasic']
	)
	"""Localization key for description"""
	coinsPrice: int | None = None
	"""Price in coins, or None if it is not purchasable with coins"""
	price: Price | None = None
	"""Real money cost, if it is purchasable with real money, or None if it is purchased with coins instead"""
	avatarAssets: list[AvatarAsset]
	presentationGroups: list[PresentationGroup] = pydantic.Field(default_factory=list)
	priceCategory: int | None = None
	"""??? 1/8/9 = coins, 10 = real money? Might be related to so-called rarity"""
	payLink: str | None = None
	"""URL for checkout, if real money"""
	isOwned: bool = False
	"""??? Not present on featured deal items?"""


class ShopDeal(BaseModel):
	id: str
	"""Somewhat like a slug in a URL, or '03/31/2024 00:00:00_03/31/2024 23:59:59_9176be8e-bf2c-4f43-9946-7d7a16756796'"""
	startDate: datetime
	endDate: datetime


class ShopFeaturedDeal(ShopDeal):
	product: ShopProduct
	promoImages: list[str]
	"""URL fragments starting with featureddealpromoimage/, all .png files"""
	titleImage: str | None
	"""URL fragment for a .png file, starts with featureddealtitleimage/"""
	mainBannerText: None  # TODO: Surely not always null
	mainSplashImage: str
	"""URL fragment for a .png file, starts with featureddealmainsplashimage/"""
	backgroundImage: str
	"""URL fragment for a .png file, starts with featureddealbackgroundimage/"""
	isPublished: bool


class ShopRandomItems(ShopDeal):
	"""Has multiple products in one "deal" instead"""

	products: list[ShopProduct]


class ShopCreatorBundle(BaseModel):
	id: str = pydantic.Field(examples=['zigzag-bundle', 'WC23_CN_Jupa'])
	title: str = pydantic.Field(examples=['zi8gzag', 'China'])
	backgroundImage: str
	"""URL fragment for image file, may be JPEG, starts with creatorshopproductbackgroundimage/"""
	previewAvatarImage: str
	"""URL fragment for image file, starts with previewavatarimage/"""
	creatorAffiliation: str
	"""Name of creator this is associated with"""
	countryAffiliation: CountryCode | None
	"""For world cup creator bundles, country of the creator this is for"""
	sortOrder: int
	product: ShopProduct


deal_list_adapter = pydantic.TypeAdapter(list[ShopDeal])
featured_deal_list_adapter = pydantic.TypeAdapter(list[ShopFeaturedDeal])
random_items_list_adapter = pydantic.TypeAdapter(list[ShopRandomItems])
creator_bundle_list_adapter = pydantic.TypeAdapter(list[ShopCreatorBundle])


def get_featured_shop_deals():
	"""Returns the featured deals in the shop (the two big ones on the left side)"""
	response = call_api('api/v4/webshop/featured-deals', do_not_cache=True)
	return featured_deal_list_adapter.validate_json(response)


async def get_featured_shop_deals_async(session: 'aiohttp.ClientSession | None' = None):
	"""Returns the featured deals in the shop (the two big ones on the left side)"""
	response = await call_api_async('api/v4/webshop/featured-deals', session, do_not_cache=True)
	return featured_deal_list_adapter.validate_json(response)


def get_shop_items():
	"""Returns single item, with products containing all the individually purchaseable items; but also id (meaningless ID including dates), startDate and endDate (timestamps)"""
	response = call_api('api/v4/webshop/conveyor-belt', do_not_cache=True)
	return random_items_list_adapter.validate_json(response)


async def get_shop_items_async(session: 'aiohttp.ClientSession | None' = None):
	"""Returns single item, with products containing all the individually purchaseable items; but also id (meaningless ID including dates), startDate and endDate (timestamps)"""
	response = await call_api_async('api/v4/webshop/conveyor-belt', session, do_not_cache=True)
	return random_items_list_adapter.validate_json(response)


def get_creator_shop_items():
	response = call_api('api/v4/webshop/creator-shop/products', do_not_cache=True)
	return creator_bundle_list_adapter.validate_json(response)


async def get_creator_shop_items_async(session: 'aiohttp.ClientSession | None' = None):
	response = await call_api_async(
		'api/v4/webshop/creator-shop/products', session, do_not_cache=True
	)
	return creator_bundle_list_adapter.validate_json(response)
