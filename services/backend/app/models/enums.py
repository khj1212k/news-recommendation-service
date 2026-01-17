import enum


class NewsletterStatus(str, enum.Enum):
    ok = "ok"
    failed = "failed"


class EventType(str, enum.Enum):
    impression = "impression"
    click = "click"
    dwell = "dwell"
    hide = "hide"
    follow = "follow"
    save = "save"
