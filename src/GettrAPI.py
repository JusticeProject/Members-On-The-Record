"""Adapted from https://github.com/stanfordio/gogettr"""

from concurrent.futures import ThreadPoolExecutor
from collections import deque
import itertools
import logging
import time
from typing import Callable, Iterator, Any, Literal

import requests
from requests.exceptions import ReadTimeout

###################################################################################################

def merge(*dicts):
    """Merges the given dictionaries into a single dictionary, ignoring overlapping keys."""

    out = dict()
    for dictionary in dicts:
        for (key, val) in dictionary.items():
            out[key] = val
    return out


def extract(obj: dict, path: Iterator[str], default: Any = None):
    """Tries to get the object at `path` out of the object, returning `default`
    if not found."""
    for key in path:
        if isinstance(obj, dict) and key in obj:
            obj = obj[key]
        else:
            return default
    return obj


# Following two functions adapted from
# https://stackoverflow.com/questions/1181919/python-base-36-encoding
def b36encode(number: int) -> str:
    """Convert the number to base36."""
    alphabet, base36 = ["0123456789abcdefghijklmnopqrstuvwxyz", ""]

    while number:
        number, i = divmod(number, 36)
        base36 = alphabet[i] + base36

    return base36 or alphabet[0]


def b36decode(number: str) -> int:
    """Convert the base36 number to an integer."""
    return int(number, 36)

###################################################################################################

class GettrApiError(RuntimeError):
    """This error is for when the GETTR API experiences an internal
    failure. Sometimes these can be resolved be retrying; sometimes
    not."""

    def __init__(self, issue: Any):
        self.issue = issue
        super().__init__()

###################################################################################################

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
)

class ApiClient:
    """A standard and safe way to interact with the GETTR API. Catches errors, supports
    retries, etc."""

    def __init__(self, api_base_url: str = None):
        """Initializes the API client. Optionally takes in a base URL for the GETTR api."""
        self.api_base_url = api_base_url or "https://api.gettr.com"

    def get(
        self, url: str, params: dict = None, retries: int = 3, key: str = "result"
    ) -> dict:
        """Makes a request to the given API endpoint and returns the 'results' object.
        Supports retries. Soon will support authentication."""
        tries = 0
        errors = []  # keeps track of the errors we've encountered

        def handle_error(issue):
            logging.warning(
                "Unable to pull from API: %s. Waiting %s seconds before retrying (%s/%s)...",
                issue,
                4 ** tries,
                tries,
                retries,
            )
            time.sleep(4 ** tries)
            errors.append(issue)

        while tries < retries:
            logging.info("Requesting %s (params: %s)...", url, params)
            tries += 1

            try:
                resp = requests.get(
                    self.api_base_url + url,
                    params=params,
                    timeout=10,
                    headers={"User-Agent": USER_AGENT},
                )
            except ReadTimeout as err:
                handle_error({"timeout": err})
                continue
            except Exception as e:
                handle_error({"error": str(e)})
                continue

            logging.info("%s gave response: %s", url, resp.text)

            if resp.status_code in [429, 500, 502, 503, 504]:
                handle_error({"status_code": resp.status_code})
                continue

            logging.debug("GET %s with params %s yielded %s", url, params, resp.content)

            data = resp.json()
            if key in data:
                return data[key]

            # Couldn't find the key, so it's an error.
            errors.append(data)  # Retry but without sleep.

        raise GettrApiError(errors[-1])  # Throw with most recent error

    def get_paginated(
        self,
        *args,
        offset_param: str = "offset",
        offset_start: int = 0,
        offset_step: int = 20,
        result_count_func: Callable[[dict], int] = lambda k: len(k["data"]["list"]),
        **kwargs
    ) -> Iterator[dict]:
        """Paginates requests to the given API endpoint."""
        for i in itertools.count(start=offset_start, step=offset_step):
            params = kwargs.get("params", {})
            params[offset_param] = i
            kwargs["params"] = params
            data = self.get(*args, **kwargs)
            yield data

            # End if no more results
            if result_count_func(data) == 0:
                return

###################################################################################################

class Capability:
    """Provides base functionality for the individual capabilities."""

    def __init__(self, client: ApiClient):
        self.client = client

    def pull(self, *args, **kwargs) -> Any:
        """Pull the desired data from GETTR."""
        raise NotImplementedError

###################################################################################################

class All(Capability):
    def pull(
        self,
        first: str = None,
        last: str = None,
        max: int = None,
        type: Literal["posts", "comments"] = "posts",
        order: Literal["up", "down"] = "up",
        workers: int = 10,
    ) -> Iterator[dict]:
        """Pulls all the posts from the API sequentially.

        :param str first: the id of the earliest post to include
        :param str last: the id of the last post to include
        :param int max: the maximum number of posts to pull
        :param str type: whether to pull posts or comments
        :order ["up" | "down"] order: whether to go from first to last (chronological)
            or last to first (reverse chronological)
        :param int workers: number of workers to run in parallel threads
        """

        assert type in ["posts", "comments"]

        n = 0  # How many posts we've emitted
        post_ids = self._post_id_generator(first, last, type, order)

        with ThreadPoolExecutor(max_workers=workers) as ex:
            # Submit initial work
            futures = deque(
                ex.submit(self._pull_post, post_id)
                for post_id in itertools.islice(post_ids, workers * 2)
            )

            while futures:
                result = futures.popleft().result()

                # Yield the result if it's valid
                if result is not None:
                    n += 1
                    yield result

                # Exit if we've hit the max number of posts
                if max is not None and n >= max:
                    return

                # Schedule more work, if available
                try:
                    futures.append(ex.submit(self._pull_post, next(post_ids)))
                except StopIteration:
                    # No more unscheduled post IDs to process
                    pass

    def _post_id_generator(
        self,
        first: str = None,
        last: str = None,
        type: Literal["posts", "comments"] = "posts",
        order: Literal["up", "down"] = "up",
    ) -> Iterator[str]:
        """Returns a generator of GETTR post IDs to pull."""

        # We remove the first character from the post IDs below because they are
        # always `p` and not part of the numbering scheme
        if order == "up":
            start_at = b36decode(first[1:]) if first is not None else 1
            end_at = b36decode(last[1:]) if last is not None else None
        else:
            if last is None:
                raise ValueError(
                    "the last post (i.e., the starting post) must be defined when"
                    "pulling posts reverse chronologically (we need to know where to start!)"
                )
            start_at = b36decode(last[1:])
            end_at = b36decode(first[1:]) if first is not None else 1

        for id in itertools.count(start_at, 1 if order == "up" else -1):
            yield ("p" if type == "posts" else "c") + b36encode(id)

            if end_at is not None and id == end_at:
                return

    def _pull_post(self, post_id: str) -> dict:
        """Attempt to pull the given post from GETTR."""

        try:
            data = self.client.get(
                f"/u/post/{post_id}",
                params={
                    "incl": "poststats|userinfo|posts|commentstats",
                },
                key="result",
            )
        except GettrApiError as e:
            logging.warning("Hit API error while pulling: %s", e)
            return
        if "txt" in data and data["data"]["txt"] == "Content Not Found":
            # Yes, this is how they do it. It's just a string.
            logging.info("Post %s not found...", post_id)
            return

        user_id = extract(data, ["data", "uid"])
        if user_id is None:
            return

        # At this point we know the post exists. Let's assemble and return it.
        post = merge(
            data["data"],
            dict(
                uinf=extract(data, ["aux", "uinf", user_id]),
                shrdpst=extract(data, ["aux", "shrdpst"]),
                s_pst=extract(data, ["aux", "s_pst"]),
                s_cmst=extract(data, ["aux", "s_cmst"]),
                post=extract(data, ["aux", "post"]),
            ),
        )

        return post

###################################################################################################

class UserActivity(Capability):
    def pull(
        self,
        username: str,
        max: int = None,
        until_id: str = None,
        until_time: int = None,
        type: Literal["posts", "comments", "likes"] = "posts",
    ) -> Iterator[dict]:
        """Pull the users' posts, comments, and likes from the API. Gettr groups all
        these different activities under the same API endpoint, so they are grouped
        here as well.

        :param str username: the username of the desired user
        :param int max: the maximum number of posts to pull
        :param str until_id: the earliest post ID to pull
        :param int until_time: the earliest post to pull specified by timestamp (milliseconds since the epoch, UTC)
        :param str type: whether to pull posts, comments, or likes"""

        assert type in ["posts", "comments", "likes"]

        url = f"/u/user/{username}/posts"
        n = 0  # Number of posts emitted

        # There is a fourth option, `f_u`, which for some users seems to return
        # all their activity. It does not seem to work on all users, however.
        if type == "posts":
            fp_setting = "f_uo"
        elif type == "comments":
            fp_setting = "f_uc"
        elif type == "likes":
            fp_setting = "f_ul"

        for data in self.client.get_paginated(
            url,
            params={
                "max": 20,
                "dir": "fwd",
                "incl": "posts|stats|userinfo|shared|liked",
                "fp": fp_setting,
            },
        ):

            for event in data["data"]["list"]:
                id = event["activity"]["tgt_id"]

                # Information about posts is spread across three objects, so we merge them together here.
                post = merge(
                    event, data["aux"]["post"].get(id), data["aux"]["s_pst"].get(id)
                )

                # Verify that we haven't passed the `until_id` post
                if until_id is not None and until_id > id:
                    return

                # Verify that we hanve't passed the `until_time` post
                if until_time is not None:
                    udate = post["udate"]
                    if until_time > udate:
                        return

                # Verify that we haven't passed the max number of posts
                if max is not None and n >= max:
                    return

                n += 1
                yield post

###################################################################################################

class PublicClient:
    def __init__(self):
        self.api_client = ApiClient()

    def user_activity(self, *args, **kwargs):
        return UserActivity(self.api_client).pull(*args, **kwargs)

    def all(self, *args, **kwargs):
        return All(self.api_client).pull(*args, **kwargs)
