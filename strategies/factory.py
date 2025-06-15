from .strategies.base import StrategyInterface
from .strategies.choice import ChoiceStrategy


def get_strategy(activity_type: str) -> StrategyInterface:
    if activity_type == "choice":
        return ChoiceStrategy()
    raise ValueError(f"Estrategia desconocida: {activity_type}")
