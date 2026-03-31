import asyncio
import httpx
import json
from app.main import app

AUDIT_CASES = [
    ("Direct disfrazado", "¿Qué dice el artículo 12 del Código Civil Federal?"),
    ("Direct con ruido", "oye bro puedes decirme el art 14 del codigo civil federal pls"),
    ("Caso Crítico User", "¿Qué establece el artículo 1 del Código Civil Federal?"),
    ("Multi-artículo", "artículos 12, 13 y 14 del código civil federal"),
    ("Hybrid fuerte", "responsabilidad civil artículo 1910 código civil federal"),
    ("Hybrid lenguaje natural", "divorcio artículo 266 y cómo aplica"),
    ("Semántico puro", "cómo funciona la responsabilidad civil en méxico"),
    ("Fallback inexistente", "artículo 99999 del código civil federal"),
    ("Ambiguo", "artículo 1"),
    ("Error humano", "articulo uno del codigo civil federal"),
    ("Borderline", "explicación del artículo 14 del código civil federal"),
    ("Bonus Pro", "oye necesito saber sobre divorcio pero también el artículo 266 del código civil federal explícame"),
]

async def run_audit():
    print("\n" + "="*80)
    print("🚀 LEGAL RAG SENIOR AUDIT RESULTS (ASYNC)")
    print("="*80)
    
    # Usamos AsyncClient para evitar colisiones de pool de asyncpg en tests
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://testserver") as client:
        for label, query in AUDIT_CASES:
            print(f"\nQUERY: [{label}] -> \"{query}\"")
            
            # Sin sleep, el AsyncClient maneja correctamente la secuencialidad
            response = await client.post("/api/v1/legal/search", json={"consulta": query, "limite": 5})
            
            if response.status_code != 200:
                print(f"❌ ERROR: status {response.status_code}")
                print(response.text)
                continue
                
            results = response.json()
            if not results:
                print("⚠️ SIN RESULTADOS")
                continue
                
            top = results[0]
            count = len(results)
            
            print(f"   ├─ Top 1: {top.get('ley_o_codigo', 'N/A')} | {top.get('numero_articulo', 'N/A')}")
            print(f"   ├─ Score: {top.get('similitud', 0):.4f}")
            print(f"   ├─ Num Results: {count}")
            
            arts = [r.get("numero_articulo") for r in results]
            print(f"   └─ Article List: {', '.join(arts)}")

    print("\n" + "="*80)
    print("🏁 AUDIT COMPLETE")
    print("="*80)

if __name__ == "__main__":
    asyncio.run(run_audit())
