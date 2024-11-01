"""Some stuff that's not an API call, but arguably belongs in this project… hrm I dunno what else to call it"""

from pygeoguessr.types import Medal


def get_medal(score: int) -> Medal | None:
	if score == 25_000:
		return Medal.Platinum
	if score >= 22_500:
		return Medal.Gold
	if score >= 15_000:
		return Medal.Silver
	if score >= 5_000:
		return Medal.Bronze
	return None
