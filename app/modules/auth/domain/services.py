class AuthService:
    """
    Capa de Dominio (Auth). 
    Aquí es donde validas los hashes de contraseñas, o te comunicas con el Adaptador de Supabase.
    """
    def login_user(self):
        return {
            "token": "token_generado_en_dominio_12345", 
            "message": "Sesión iniciada exitosamente"
        }
