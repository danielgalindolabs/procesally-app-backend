"""
Script para actualizar materias_juridicas en la tabla legal_documents.

Uso:
    uv run python scripts/update_document_materias.py
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text

from app.modules.share.infrastructure.db.session import async_session_maker
from app.modules.share.infrastructure.parsers.dof_parser import (
    _infer_materia_from_keywords,
)


async def update_document_materias():
    """Actualiza las materias de todos los documentos existentes."""
    async with async_session_maker() as session:
        print("Obteniendo documentos...")

        result = await session.exec(
            text("""
            SELECT id, titulo 
            FROM legal_documents
        """)
        )
        docs = result.all()

        print(f"Encontrados {len(docs)} documentos")

        count = 0
        for doc_id, titulo in docs:
            if titulo:
                materias = _infer_materia_from_keywords(titulo.lower())
                materia_str = ", ".join(materias)

                await session.exec(
                    text("""
                        UPDATE legal_documents 
                        SET materias_juridicas = :materia
                        WHERE id = :id
                    """),
                    params={"materia": materia_str, "id": doc_id},
                )
                count += 1
                if count % 50 == 0:
                    print(f"  Actualizados {count}/{len(docs)}...")

        await session.commit()
        print(f"\n✅ Actualizados {count} documentos")

        print("\nVerificando...")
        result = await session.exec(
            text("""
            SELECT materias_juridicas, COUNT(*) as cnt
            FROM legal_documents
            GROUP BY materias_juridicas
            ORDER BY cnt DESC
            LIMIT 15
        """)
        )
        rows = result.all()
        print("\nDistribución de materias en documentos:")
        for r in rows:
            print(f"  {str(r[0])[:50]:<50}: {r[1]:>4} docs")


async def main():
    print("=" * 60)
    print("ACTUALIZACIÓN DE MATERIAS EN DOCUMENTOS")
    print("=" * 60)
    await update_document_materias()
    print("\n" + "=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
