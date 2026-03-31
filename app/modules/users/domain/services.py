class UserService:
    """
    Capa de Dominio (Users).
    Reglas estrictas de negocio (Ej. Si el usuario es Gratis, restar -1 a sus créditos de IA).
    """

    def get_user_profile(self):
        return {
            "name": "Abogado Hexagonal",
            "plan": "Premium (MVP)",
            "busquedas_ia_restantes": 99,
        }
