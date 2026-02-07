from enum import Enum


class TableNames(str, Enum):
    USERS = "users"
    GUESTS = "guests"
    FAMILIES = "families"
    DIETARY_OPTIONS = "dietary_options"
    RSVP_INFO = "rsvp_info"
