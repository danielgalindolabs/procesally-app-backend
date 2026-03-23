from sentence_transformers import SentenceTransformer
import asyncio
import logging

logger = logging.getLogger("app.core.embeddings")

class EmbeddingEngine:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        logger.info(f"Cargando modelo de embeddings léxicos: {model_name}...")
        self.model = SentenceTransformer(model_name)
        logger.info("Modelo de embeddings cargado exitosamente en memoria RAM.")
        
    async def generate_embedding(self, text: str) -> list[float]:
        """
        Ejecuta la inferencia de la red neuronal en un thread separado
        para no bloquear el Application Event Loop de FastAPI.
        """
        # sentence-transformers retorna un numpy o tensor, lo convertimos a float list
        vector = await asyncio.to_thread(self.model.encode, text)
        return vector.tolist()

# Instancia global estática per-worker.
# En producción seria, esto vivirá en un microservicio de GPU tipo Triton/vLLM,
# pero para MVP el CPU estático es la mejor opción.
engine = EmbeddingEngine()
