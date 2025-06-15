from abc import ABC, abstractmethod


class StrategyInterface(ABC):
    @abstractmethod
    def validate(self, activity, selected: list[int]) -> bool:
        pass
