## py-geoguessr

py-geoguessr is an unoriginally named Python wrapper for the GeoGuessr API, intended for getting interesting stats and insights about games you have played. It uses pydantic to ensure all the data is type hinted and consistent with what is expected.

This readme is not complete and needs suggestions for improvement.

This project, for that matter, is not necessarily complete either.

## Warnings!
1. GeoGuessr's API is not formally documented, or intended to be used by third parties, it is (as far as I can tell) only there for GeoGuessr's developers. Therefore this  might break at any given time, which is true anyway for a hobbyist project of this nature, but especially so.
2. For many operations, py-geoguessr will need access to your GeoGuessr account. It does this by using the `_ncfa` cookie from your browser, which you need to provide yourself in an environment variable called `NCFA_COOKIE`. You should be careful with this, as anyone who gets their hands on it can potentially do all sorts of nasty things with it, effectively having access to your entire account. py-geoguessr does not do anything nefarious, and does not send your cookie anywhere other than GeoGuessr's servers as a cookie to authenticate, and as it is open source you can scrutinize the code yourself. I felt that it was still important to warn about this, out of principle.

## Getting started
This is a library and not something for end users, but to start using it in Python code:

1. Install pydantic and requests-cache as specified in requirements.txt
2. As specified above, set the environment variable NCFA_COOKIE to the `_ncfa` cookie from your browser. Yes, it's a bit clunky, but it was either that or it would need your username and password and call the login API, and that seemed even more sketchy to me.
3. `import pygeoguessr` wherever you want to use it. `iter_activity_feed()` is how you go about getting previous games you've played, so is the most likely starting point.
You can skip step 2 if all you want is to look up things like maps or challenges or singleplayer games that don't require a logged in user (the docstrings for the various API functions should tell you if something requires authentication when it's not completely apparent that it does).

(TODO: Put some screenshots here of how to get at that from Chrome/Firefox. Not everyone is a nerd like me and presses F12 on every website they visit)

See also the 'settings' module for some other options, which should use pydantic-settings ideally, but doesn't right now because I haven't gotten around to that.

## Future plans
- Fix up battle royale/live challenge/bullseye games
- Probably some convenient wrapper classes (which look up all the tokens and present the info more nicely, make activities better to deal with, etc)
- Make requests-cache optional
- Make aiohttp-client-cache optional