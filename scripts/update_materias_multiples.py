"""
Script para actualizar la columna materia_juridica de todos los artículos existentes
usando la nueva lógica de inferencia de múltiples materias.

Uso:
    uv run python scripts/update_materias_multiples.py
"""

import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.share.infrastructure.db.session import async_session_maker


def _infer_materia_from_keywords(nombre_lower: str) -> list[str]:
    """Infiere la(s) materia(s) jurídica(s) basándose en keywords del nombre de la ley."""
    materias = set()

    if any(
        kw in nombre_lower
        for kw in [
            "penal",
            "delito",
            "cárcel",
            "prisión",
            "víctima",
            "imputado",
            "sentencia penal",
        ]
    ):
        materias.add("Penal")

    if any(
        kw in nombre_lower
        for kw in [
            "civil",
            "personas",
            "familia",
            "matrimonio",
            "divorcio",
            "tutela",
            "curatela",
            "patria potestad",
            "alimentos",
            "parentesco",
            "filiación",
            "adopción",
            "sucesiones",
            "herencia",
            "testamento",
            "legado",
            "obligaciones",
            "contratos",
            "bienes",
            "posesión",
            "usucapión",
            "hipoteca",
            "prenda civil",
        ]
    ):
        materias.add("Civil")

    if any(
        kw in nombre_lower
        for kw in [
            "trabajo",
            "laboral",
            "empleado",
            "patrón",
            "salario",
            "jornada",
            "vacaciones",
            "aguinaldo",
            "indemnización",
            "despido",
            "huelga",
            "sindicato",
            "contrato individual",
            "condiciones generales",
            "tiempoextra",
            "descanso",
            "maternal",
            "menor",
        ]
    ):
        materias.add("Laboral")

    if any(
        kw in nombre_lower
        for kw in [
            "seguridad social",
            "seguro social",
            "previsión social",
            "afiliación",
            "pensión",
            "jubilación",
            "vejez",
            "invalidez",
            "orfandad",
            "viudez",
            "issste",
            "imss",
            "sar",
            "infonavit",
            "cuenta individual",
            "servicio médico",
            "enfermedad",
            "ahorro para el retiro",
            "sistema de ahorro",
        ]
    ):
        materias.add("Seguridad Social")

    if any(
        kw in nombre_lower
        for kw in [
            "comercio",
            "mercantil",
            "comerciante",
            "acta constitutiva",
            "sociedad mercantil",
            "s.a.",
            "s.a.b.",
            "s. de r.l.",
            "s. en c.",
            "título de crédito",
            "letra de cambio",
            "pagaré",
            "cheque",
            "warrant",
            "corretaje",
            "comisión mercantil",
            "transporte",
            "depósito",
            "prenda civil",
        ]
    ):
        materias.add("Mercantil")

    if any(
        kw in nombre_lower
        for kw in [
            "fiscal",
            "tributari",
            "impuesto",
            "renta",
            "isr",
            "iva",
            "ieps",
            "ingresos",
            "aduana",
            "sat",
            "derechos",
            "contribuci",
            "fedatario",
            "generación de ingresos",
            "precio de transferencia",
            "consolidación fiscal",
        ]
    ):
        materias.add("Fiscal")

    if any(
        kw in nombre_lower
        for kw in [
            "amparo",
            "constitu",
            "derechos humanos",
            "garantías individuales",
            "principio constitucional",
            "reforma constitucional",
            "iniciativa",
            "poder legislativo",
            "poder ejecutivo",
            "poder judicial",
            "suprema corte",
            "tribunal electoral",
        ]
    ):
        materias.add("Constitucional")

    if any(
        kw in nombre_lower
        for kw in [
            "administrati",
            "ley orgánica",
            "reglamento interior",
            "municipio",
            "ayuntamiento",
            "seguridad pública",
            "protección civil",
            "adquisiciones públicas",
            "bienes muebles",
            "combate",
            "caminos",
            "puentes",
            "autotransporte",
            "transporte federal",
        ]
    ):
        materias.add("Administrativo")

    if any(
        kw in nombre_lower
        for kw in [
            "bancario",
            "banco",
            "crédito",
            "inversión",
            "valores",
            "bolsa",
            "sistema financiero",
            "cnmv",
            "banco de méxico",
            "banxico",
            "intermediario",
            "aseguramiento",
            "fondos de inversión",
            "deuda",
        ]
    ):
        materias.add("Financiero")

    if any(
        kw in nombre_lower
        for kw in [
            "ambiental",
            "ecológico",
            "recursos naturales",
            "protección ambiental",
            "fauna",
            "flora",
            "áreas naturales",
            "manejo de residuos",
            "sustancias peligrosas",
            "emisiones",
            "cambio climático",
            "desarrollo sostenible",
        ]
    ):
        materias.add("Ambiental")

    if any(
        kw in nombre_lower
        for kw in [
            "energía",
            "petróleos",
            "petroleo",
            "gas natural",
            "electricidad",
            "hydrocarburo",
            "refinación",
            "pemex",
            "cenace",
            "cre",
            "hidroeléctrica",
            "eólica",
            "solar",
            "renovable",
        ]
    ):
        materias.add("Energético")

    if any(
        kw in nombre_lower
        for kw in [
            "comunicaciones",
            "telecomunicaciones",
            "telefonía",
            "radio",
            "televisión",
            "satélite",
            "internet",
            "correos",
            "ift",
            "telecom",
        ]
    ):
        materias.add("Telecomunicaciones")

    if any(
        kw in nombre_lower
        for kw in [
            "propiedad industrial",
            "propiedad intelectual",
            "patente",
            "marca",
            "derecho autor",
            "copyright",
            "modelo utilidad",
            "diseño industrial",
            "secreto industrial",
            "licencia",
        ]
    ):
        materias.add("Propiedad Intelectual")

    if any(
        kw in nombre_lower
        for kw in [
            "educativo",
            "educación",
            "educación pública",
            "institución educativa",
            "educación superior",
            "sep",
        ]
    ):
        materias.add("Educativo")

    if any(
        kw in nombre_lower
        for kw in [
            "salud",
            "médico",
            "sanitario",
            "epidemia",
            "epidemiológic",
            "hospital",
            "clínica",
            "medicamento",
            "dispositivo médico",
            "permiso sanitario",
            "comisión federal",
            "coepris",
        ]
    ):
        materias.add("Salud")

    if any(
        kw in nombre_lower
        for kw in [
            "agrario",
            "agrícola",
            "ejidal",
            "comunal",
            "tierra",
            "dotación",
            "restitución",
            "procede",
            "panel alfa",
        ]
    ):
        materias.add("Agrario")

    if any(
        kw in nombre_lower
        for kw in [
            "marítimo",
            "navegación",
            "puertos",
            "mar territorial",
            "aguas jurisdiccionales",
            "cabotaje",
            "admisión temporal",
            "arqueo",
        ]
    ):
        materias.add("Marítimo")

    if any(
        kw in nombre_lower
        for kw in [
            "aéreo",
            "aviación",
            "aeropuerto",
            "aeronave",
            "piloto",
            "navegación aérea",
            "sct",
            "dgac",
        ]
    ):
        materias.add("Aviación")

    if any(
        kw in nombre_lower
        for kw in [
            "patrimonio cultural",
            "patrimonio histórico",
            "patrimonio arqueológic",
        ]
    ):
        materias.add("Cultural")

    if not materias:
        materias.add("General")

    return sorted(list(materias))


async def update_materias():
    """Actualiza todas las materias de los artículos existentes."""
    async with async_session_maker() as session:
        print("Obteniendo leyes únicas...")

        result = await session.exec(
            text("""
            SELECT DISTINCT ley_o_codigo 
            FROM legal_articles 
            WHERE ley_o_codigo IS NOT NULL 
            AND ley_o_codigo != ''
        """)
        )
        leyes = [row[0] for row in result.all()]

        print(f"Encontradas {len(leyes)} leyes únicas")

        updates = []
        for ley in leyes:
            materias = _infer_materia_from_keywords(ley.lower())
            materia_str = ", ".join(materias)
            updates.append((materia_str, ley))

        print(f"Generadas {len(updates)} actualizaciones")

        print("\nActualizando materias...")
        count = 0
        for materia_str, ley in updates:
            await session.exec(
                text("""
                    UPDATE legal_articles 
                    SET materia_juridica = :materia
                    WHERE ley_o_codigo = :ley
                """),
                params={"materia": materia_str, "ley": ley},
            )
            count += 1
            if count % 100 == 0:
                print(f"  Actualizados {count}/{len(updates)}...")

        await session.commit()
        print(f"\n✅ Actualizados {count} artículos")

        print("\nVerificando distribución de materias...")
        result = await session.exec(
            text("""
            SELECT materia_juridica, COUNT(*) as cnt
            FROM legal_articles 
            WHERE embedding IS NOT NULL
            GROUP BY materia_juridica
            ORDER BY cnt DESC
        """)
        )
        rows = result.all()
        print("\nDistribución de materias:")
        for r in rows:
            print(f"  {r[0][:50]:<50}: {r[1]:>6} artículos")

        multiple = sum(1 for r in rows if "," in r[0])
        print(f"\nTotal: {len(rows)} combinaciones de materias")
        print(f"Artículos con múltiples materias: {multiple}")


async def main():
    print("=" * 60)
    print("ACTUALIZACIÓN DE MATERIAS JURÍDICAS (MÚLTIPLES)")
    print("=" * 60)

    await update_materias()

    print("\n" + "=" * 60)
    print("PROCESO COMPLETADO")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
