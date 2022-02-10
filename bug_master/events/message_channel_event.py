import re
from typing import List

from loguru import logger
from starlette.responses import JSONResponse, Response

from .. import consts
from ..bug_master_bot import BugMasterBot
from ..entities import Comment
from ..models import MessageEvent
from ..prow_job import ProwJobFailure
from .event import Event


class MessageChannelEvent(Event):
    def __init__(self, body: dict, bot: BugMasterBot) -> None:
        super().__init__(body, bot)
        self._user = self._data.get("user")
        self._text = self._data.get("text")
        self._ts = self._data.get("ts")

    def __str__(self):
        return (
            f"id: {self._event_id}, user: {self._user}, channel: {self._channel} ts: {self._ts},"
            f" has_file: {self.contain_files}"
        )

    @property
    def channel(self) -> str:
        return self._channel

    @property
    def user(self) -> str:
        return self._user

    @property
    def is_self_event(self) -> bool:
        if "bot_id" in self._data:
            if self._bot.bot_id == self._data.get("bot_id"):
                return True
        return False

    @property
    def contain_files(self):
        return self._data and self._data.get("files")

    def is_command_message(self):
        return self._text and self._text.startswith("/bugmaster")

    async def handle(self, **kwargs) -> Response:
        logger.info(f"Handling {self.type}, {self._subtype} event")
        channel_name = kwargs.get("channel_info", {}).get("name", self.channel)

        # ignore messages sent by bots or retries
        if self.is_self_event:
            logger.info(
                f"Skipping event on channel {channel_name} sent by {self._bot.bot_id}:{self._bot.name} - "
                f"event: {self}"
            )
            return JSONResponse({"msg": "Success", "Code": 200})

        if not self._data.get("text", "").replace(" ", "").startswith(consts.EVENT_FAILURE_PREFIX):
            logger.info(f"Ignoring messages that do not start with {consts.EVENT_FAILURE_PREFIX}")
            return JSONResponse({"msg": "Success", "Code": 200})

        if not self._bot.has_channel_configurations(self.channel):
            await self._bot.try_load_configurations_from_history(self.channel)

        if not self._bot.has_channel_configurations(self.channel):
            await self._bot.add_comment(
                self.channel,
                f"BugMaster configuration file on channel `{channel_name}` is invalid or missing. "
                "Please add or fix the configuration file or remove the bot.",
            )
            return JSONResponse({"msg": "Failure", "Code": 401})

        logger.info(f"Handling event {self}")
        configuration = self._bot.get_configuration(self._channel)

        links = self._get_links()
        for link in links:
            if not link.startswith(ProwJobFailure.MAIN_PAGE_URL):
                logger.info(f"Skipping comment url {link}")
                continue
            try:
                pj = await ProwJobFailure(link).load()
                emojis, comments = await pj.get_failure_actions(self._channel, configuration)
                logger.debug(f"Adding comments={','.join([c.text for c in comments])} and emojis={emojis}")
                await self.add_reactions(emojis)
                await self.add_comments(comments)
                self.add_record(pj)
            except IndexError:
                continue

        return JSONResponse({"msg": "Success", "Code": 200})

    def add_record(self, job_failure: ProwJobFailure):
        MessageEvent.create(
            job_id=job_failure.build_id,
            job_name=job_failure.job_name,
            user=self._user,
            thread_ts=self._ts,
            url=job_failure.url,
            channel_id=self._channel,
        )

    async def add_reactions(self, emojis: List[str]):
        for emoji in emojis:
            logger.debug(f"Adding reactions to channel {self._channel} for ts {self._ts}")
            await self._bot.add_reaction(self._channel, emoji, self._ts)

    async def add_comments(self, comments: List[Comment]):
        for comment in sorted(comments, key=lambda c: c.type.value):
            logger.debug(f"Adding comment in channel {self._channel} for ts {self._ts}")
            await self._bot.add_comment(self._channel, comment.text, self._ts, comment.parse)

    def _get_links(self) -> List[str]:
        urls = list()
        for block in self._data.get("blocks", []):
            for element in block.get("elements", []):
                for e in element.get("elements", []):
                    element_type = e.get("type")
                    if element_type == "link":
                        urls.append(e.get("url"))

        # If url posted as plain text - try to get url using regex
        if not urls:
            urls = [
                url
                for url in re.findall(r"https://?[\w/\-?=%.]+\.[\w/\-&?=%.]+", self._text)
                if "prow.ci.openshift.org" in url
            ]

        logger.debug(f"Found {len(urls)} urls in event {self._data}")
        return urls
