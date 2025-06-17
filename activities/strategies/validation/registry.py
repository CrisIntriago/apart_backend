class ValidationStrategyRegistry:
    _registry = {}

    @classmethod
    def register(cls, activity_type, serializer):
        def decorator(strategy_cls):
            cls._registry[activity_type] = {
                "strategy": strategy_cls(),
                "serializer": serializer,
            }
            return strategy_cls

        return decorator

    @classmethod
    def get_strategy(cls, activity_type):
        entry = cls._registry.get(activity_type)
        return entry["strategy"] if entry else None

    @classmethod
    def get_serializer(cls, activity_type):
        entry = cls._registry.get(activity_type)
        return entry["serializer"] if entry else None
