from enum import Enum


class TableNames(str, Enum):
    USERS = "users"
    EVENTS = "events"
    GUESTS = "guests"
    DIETARY_OPTIONS = "dietary_options"
