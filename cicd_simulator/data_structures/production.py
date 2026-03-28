from dataclasses import dataclass, field
import time


@dataclass
class ProductionVersion:
    version: str
    commit_hash: str
    timestamp: float = field(default_factory=time.time)


class RollbackStack:
    def __init__(self):
        self._stack: list[ProductionVersion] = []

    def push(self, version: ProductionVersion):
        self._stack.append(version)

    def rollback(self) -> ProductionVersion | None:
        if len(self._stack) > 1:
            self._stack.pop()
            return self._stack[-1]
        return None

    def top(self) -> ProductionVersion | None:
        return self._stack[-1] if self._stack else None

    def get_stack(self) -> list[ProductionVersion]:
        return list(reversed(self._stack))


@dataclass
class LogEntry:
    level: str
    message: str
    stage: str
    timestamp: float = field(default_factory=time.time)


class LogList:
    def __init__(self):
        self._logs: list[LogEntry] = []

    def add(self, level: str, message: str, stage: str):
        self._logs.append(LogEntry(level=level, message=message, stage=stage))

    def filter(
        self,
        level: str | None = None,
        text: str | None = None,
    ) -> list[LogEntry]:
        result = self._logs
        if level:
            result = [l for l in result if l.level == level]
        if text:
            result = [l for l in result if text.lower() in l.message.lower()]
        return result