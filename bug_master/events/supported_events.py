from .url_verification_event import UrlVerificationEvent
from .channel_join_event import ChannelJoinEvent
from .file_events import FileShareEvent, FileChangeEvent
from .message_channel_event import MessageChannelEvent


class SupportedEvents:
    MESSAGE_TYPE = "message"
    URL_VERIFICATION = "url_verification"
    CHANNEL_JOIN_SUBTYPE = "channel_join"
    FILE_SHARE_SUBTYPE = "file_share"
    FILE_CHANGED_EVENT = "file_change"

    @classmethod
    def get_events_map(cls):
        return {
            (cls.MESSAGE_TYPE, ""): MessageChannelEvent,
            (cls.URL_VERIFICATION, ""): UrlVerificationEvent,
            (cls.MESSAGE_TYPE, cls.FILE_SHARE_SUBTYPE): FileShareEvent,
            (cls.MESSAGE_TYPE, cls.CHANNEL_JOIN_SUBTYPE): ChannelJoinEvent,
            (cls.FILE_CHANGED_EVENT, ""): FileChangeEvent,
        }


class NotSupportedEventError(Exception):
    pass