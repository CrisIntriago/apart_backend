class ValidationStrategy:
    def validate(self, activity, user_response: dict) -> bool:
        raise NotImplementedError("Subclases deben implementar el método `validate`.")
