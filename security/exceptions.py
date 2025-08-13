class TokenInvalid(Exception):
    """El token no existe o no corresponde al tipo esperado."""


class TokenExpired(Exception):
    """El token existe pero está expirado (o ya fue usado)."""


class PasswordValidationError(Exception):
    """La contraseña no pasa validaciones de Django."""

    def __init__(self, messages):
        self.messages = messages
        super().__init__("; ".join(messages))
