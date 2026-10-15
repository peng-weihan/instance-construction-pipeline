from enum import StrEnum

class EventState(StrEnum):
    DONE = "done"
    READY = "ready"

    def __str__(self) -> str:
        return str(self.value)
