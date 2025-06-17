class PayloadStrategyRegistry:
    _strategies = {}

    @classmethod
    def register(cls, activity_type):
        def decorator(strategy_cls):
            cls._strategies[activity_type] = strategy_cls()
            return strategy_cls

        return decorator

    @classmethod
    def get_strategy(cls, activity_type):
        return cls._strategies.get(activity_type)
