import requests
import json
import re
from datetime import datetime

# Datos base (fallback si la API falla)
NACIONAL = {
    "keiko": 8765590, "sanchez": 8750503,
    "actasCont": 86650, "actasJEE": 1513, "actasPend": 4603,
    "actasTotal": 92766, "pctActas": 93.407
}

REGION_DATA = [
    {"region":"AMAZONAS",     "keiko":53.2, "sanchez":46.8, "actas":99.1},
    {"region":"ANCASH",       "keiko":55.8, "sanchez":44.2, "actas":99.3},
    {"region":"APURIMAC",     "keiko":40.1, "sanchez":59.9, "actas":98.7},
    {"region":"AREQUIPA",     "keiko":47.3, "sanchez":52.7, "actas":99.5},
    {"region":"AYACUCHO",     "keiko":38.4, "sanchez":61.6, "actas":98.2},
    {"region":"CAJAMARCA",    "keiko":55.1, "sanchez":44.9, "actas":99.4},
    {"region":"CALLAO",       "keiko":51.9, "sanchez":48.1, "actas":99.8},
    {"region":"CUSCO",        "keiko":43.2, "sanchez":56.8, "actas":99.1},
    {"region":"HUANCAVELICA", "keiko":41.5, "sanchez":58.5, "actas":98.6},
    {"region":"HUANUCO",      "keiko":50.3, "sanchez":49.7, "actas":99.0},
    {"region":"ICA",          "keiko":54.8, "sanchez":45.2, "actas":99.6},
    {"region":"JUNIN",        "keiko":49.8, "sanchez":50.2, "actas":99.2},
    {"region":"LA LIBERTAD",  "keiko":57.5, "sanchez":42.5, "actas":99.3},
    {"region":"LAMBAYEQUE",   "keiko":58.2, "sanchez":41.8, "actas":99.4},
    {"region":"LIMA",         "keiko":50.4, "sanchez":49.6, "actas":93.5},
    {"region":"LIMA REGION",  "keiko":52.4, "sanchez":47.6, "actas":98.9},
    {"region":"LORETO",       "keiko":52.8, "sanchez":47.2, "actas":98.5},
    {"region":"MADRE DE DIOS","keiko":46.1, "sanchez":53.9, "actas":98.8},
    {"region":"MOQUEGUA",     "keiko":46.8, "sanchez":53.2, "actas":99.1},
    {"region":"PASCO",        "keiko":41.9, "sanchez":58.1, "actas":98.9},
    {"region":"PIURA",        "keiko":63.1, "sanchez":36.9, "actas":99.5},
    {"region":"PUNO",         "keiko":34.2, "sanchez":65.8, "actas":99.2},
    {"region":"SAN MARTIN",   "keiko":49.5, "sanchez":50.5, "actas":99.3},
    {"region":"TACNA",        "keiko":48.1, "sanchez":51.9, "actas":99.4},
    {"region":"TUMBES",       "keiko":60.3, "sanchez":39.7, "actas":99.6},
    {"region":"UCAYALI",      "keiko":57.8, "sanchez":42.2, "actas":99.1},
    {"region":"EXTERIOR",     "keiko":36.2, "sanchez":63.8, "actas":68.4}
]

ENDPOINTS = [
    "https://resultadosegundavuelta.onpe.gob.pe/api/elecciones/2026/resultados/departamentos",
    "https://resultadosegundavuelta.onpe.gob.pe/api/resultados/departamentos",
    "https://resultadosegundavuelta.onpe.gob.pe/api/elecciones/resultados/ubigeo/00",
]

HEADERS = {
    "Accept": "application/json",
    "Referer": "https://resultadosegundavuelta.onpe.gob.pe/",
    "Origin": "https://resultadosegundavuelta.onpe.gob.pe",
    "User-Agent": "Mozilla/5.0"
}

fetched_live = False

for url in ENDPOINTS:
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        if r.status_code == 200:
            data = r.json()
            rows = data.get("departamentos") or data.get("regiones") or data.get("data") or []
            if len(rows) >= 5:
                # Update regional
                for row in rows:
                    nm = (row.get("departamento") or row.get("nombre") or "").upper()
                    idx = next((i for i,x in enumerate(REGION_DATA) if x["region"]==nm), -1)
                    if idx >= 0:
                        cands = row.get("candidatos") or []
                        k = next((c for c in cands if "keiko" in (c.get("nombre","")).lower()), None)
                        s = next((c for c in cands if "sanchez" in (c.get("nombre","")).lower() or "sánchez" in (c.get("nombre","")).lower()), None)
                        if k and s:
                            REGION_DATA[idx]["keiko"] = float(k.get("porcentaje", REGION_DATA[idx]["keiko"]))
                            REGION_DATA[idx]["sanchez"] = float(s.get("porcentaje", REGION_DATA[idx]["sanchez"]))
                            REGION_DATA[idx]["actas"] = float(row.get("actasProcesadas", REGION_DATA[idx]["actas"]))
                # Update national
                n = data.get("nacional") or data.get("resumen")
                if n:
                    cands = n.get("candidatos", [])
                    k = next((c for c in cands if "keiko" in (c.get("nombre","")).lower()), None)
                    s = next((c for c in cands if "sanchez" in (c.get("nombre","")).lower()), None)
                    if k and s:
                        NACIONAL["keiko"] = int(k.get("votos", NACIONAL["keiko"]))
                        NACIONAL["sanchez"] = int(s.get("votos", NACIONAL["sanchez"]))
                        NACIONAL["pctActas"] = float(n.get("actasProcesadas", NACIONAL["pctActas"]))
                fetched_live = True
                print(f"✅ Datos obtenidos en vivo desde: {url}")
                break
    except Exception as e:
        print(f"❌ Error en {url}: {e}")

if not fetched_live:
    print("⚠️  Usando datos de respaldo (ONPE API no accesible)")

# Write JSON data file that the HTML will load
output = {
    "ts": datetime.utcnow().strftime("%d/%m/%Y %H:%M UTC"),
    "live": fetched_live,
    "nacional": NACIONAL,
    "regiones": REGION_DATA
}

with open("data.json", "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False)

print(f"📊 Nacional: Keiko {NACIONAL['keiko']:,} | Sánchez {NACIONAL['sanchez']:,} | Actas {NACIONAL['pctActas']}%")
