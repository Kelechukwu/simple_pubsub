from enum import Enum, unique

@unique
class Command(Enum):
    SUB = "SUB" # to create and automatically subscribe to a new event
    UNSUB = "UNSUB" # Unsubscribe from an event
    PUB = "PUB" # Publish to an event