"""
Preprocesamiento de detecciones de incendios para el visor de línea base (PND).
Lee incendios.csv (o .parquet), municipios y departamentos simplificados,
y genera datos_visor.json con un cubo agregado + geometrías livianas.

Uso (desde la carpeta que contiene los insumos y visor_template.html):
    python preparar_datos_visor.py
o indicando rutas:
    python preparar_datos_visor.py <carpeta_entrada> <salida.html>
Genera el visor final (HTML con los datos incrustados) y datos_visor.json.
Requiere: pandas, shapely, pyproj  (pyarrow solo si se usa el .parquet)
"""
import json, sys, os
import numpy as np, pandas as pd
from shapely.geometry import shape, mapping
from pyproj import Geod

HERE = os.path.dirname(os.path.abspath(__file__))
IN = sys.argv[1] if len(sys.argv) > 1 else HERE
OUT_HTML = sys.argv[2] if len(sys.argv) > 2 else os.path.join(IN, "visor_linea_base_incendios.html")
OUT = os.path.join(os.path.dirname(os.path.abspath(OUT_HTML)), "datos_visor.json")
TEMPLATE = os.path.join(HERE, "visor_template.html")
TOL_MUN, TOL_DEP = 0.004, 0.006          # simplificación (grados)
AREA_CAP_Q = 0.999                       # winsorización del área por evento

# Tipos que no corresponden a quema de vegetación (falsos positivos / fuentes fijas)
NO_VEG = {"steel", "industry", "sun", "solar", "falseDetection", "factory", "processing",
          "volcano", "cement", "structure", "hotStone", "flare"}
CONF = ["insufficient_data", "low", "medium", "high", "very_high"]

cols = ["id", "lon", "lat", "area", "fire_confidence", "type_string", "algorithms",
        "oldest_acquisition", "cod_muni", "cod_depto"]
pq = os.path.join(IN, "incendios.parquet")
try:
    df = pd.read_parquet(pq, columns=cols)
except Exception:
    df = pd.read_csv(os.path.join(IN, "incendios.csv"), usecols=cols)

df = df.drop_duplicates("id")
t = pd.to_datetime(df.oldest_acquisition.str[:19], errors="coerce")
df["y"], df["mo"] = t.dt.year, t.dt.month
df = df.dropna(subset=["y"])

alg = df.algorithms.fillna("")
bits = (alg.str.contains("VIIRS").astype(int) * 1 + alg.str.contains("MODIS").astype(int) * 2
        + alg.str.contains("GOES|EUMETSAT").astype(int) * 4 + alg.str.contains("OT-").astype(int) * 8
        + alg.str.contains("SENTINEL|FRP-PIXEL").astype(int) * 16)
df["s"] = bits
df["c"] = df.fire_confidence.map({k: i for i, k in enumerate(CONF)}).fillna(0).astype(int)
df["x"] = df.type_string.isin(NO_VEG).astype(int)
cap = df.area.quantile(AREA_CAP_Q)
df["a"] = df.area.clip(upper=cap)

# --- Geometrías
geod = Geod(ellps="WGS84")
def load(path, code, name, tol, extra=None):
    gj = json.load(open(path, encoding="utf-8"))
    out = []
    for f in gj["features"]:
        g = shape(f["geometry"])
        akm2 = abs(geod.geometry_area_perimeter(g)[0]) / 1e6
        gs = g.simplify(tol, preserve_topology=True)
        geo = json.loads(json.dumps(mapping(gs)), parse_float=lambda v: round(float(v), 4))
        p = {"k": f["properties"][code], "n": f["properties"][name], "km2": round(akm2, 1)}
        if extra: p["d"] = f["properties"][extra]
        out.append({"type": "Feature", "properties": p, "geometry": geo})
    return out

mun = load(os.path.join(IN, "municipios_simplificado.geojson"), "MpCodigo", "MpNombre", TOL_MUN, "Depto")
dep = load(os.path.join(IN, "departamentos_simplificado.geojson"), "DeCodigo", "DeNombre", TOL_DEP)
# --- Regiones pluviométricas
# Por defecto: aproximación por regiones naturales y régimen de lluvias (IDEAM).
# Si existe regiones_pluviometricas.csv (columnas: codigo municipio, region),
# por ejemplo la exportada desde GEE con CHIRPS, esa asignación tiene prioridad.
CARIBE = {"08", "13", "20", "23", "44", "47", "70", "88"}
ORINOQUIA = {"50", "81", "85", "99"}
AMAZONIA = {"18", "86", "91", "94", "95", "97"}
URABA = {"05837", "05490", "05051", "05659", "05045", "05147", "05172", "05665", "05480"}
PACIFICO_LITORAL = {"76109", "19318", "19418", "19809", "52835", "52079", "52250", "52390",
                    "52427", "52473", "52490", "52520", "52621", "52696"}
def region_default(k):
    d = k[:2]
    if k in URABA or d in CARIBE: return "Caribe"
    if d == "27" or k in PACIFICO_LITORAL: return "Pacífica"
    if d in ORINOQUIA: return "Orinoquía"
    if d in AMAZONIA: return "Amazonía"
    return "Andina"
REG_CSV = os.path.join(IN, "regiones_pluviometricas.csv")
override = {}
if os.path.exists(REG_CSV):
    rc = pd.read_csv(REG_CSV, dtype=str, sep=None, engine="python")
    def lab(v):
        v = str(v).strip()
        return f"Región {int(float(v)) + 1}" if v.replace(".", "", 1).isdigit() else v
    override = {str(c).strip().split(".")[0].zfill(5): lab(r) for c, r in zip(rc.iloc[:, 0], rc.iloc[:, 1])}
for f in mun:
    k = f["properties"]["k"]
    f["properties"]["r"] = override.get(k, region_default(k))
REG_FUENTE = ("Asignación municipal leída de regiones_pluviometricas.csv (regionalización CHIRPS)."
              if override else
              "Aproximación municipal por regiones naturales y régimen de lluvias (IDEAM): Caribe incluye Urabá; "
              "Pacífica incluye Chocó y el litoral de Valle, Cauca y Nariño; Orinoquía: Meta, Arauca, Casanare y Vichada; "
              "Amazonía: Caquetá, Putumayo, Guaviare, Guainía, Vaupés y Amazonas; el resto, Andina.")

idx = {f["properties"]["k"]: i for i, f in enumerate(mun)}
df["m"] = df.cod_muni.apply(lambda v: idx.get(str(int(v)).zfill(5), -1) if pd.notna(v) else -1)

g = (df.groupby(["m", "y", "mo", "c", "s", "x"])
       .agg(n=("id", "size"), a=("a", "sum")).reset_index())
cube = {k: g[k].astype(int).tolist() for k in ["m", "y", "mo", "c", "s", "x", "n"]}
cube["a"] = g["a"].round(0).astype(int).tolist()

meta = {
    "fecha_min": str(t.min())[:10], "fecha_max": str(t.max())[:10],
    "eventos": int(len(df)), "sin_municipio": int((df.m < 0).sum()),
    "area_cap_ha": round(float(cap), 1),
    "regiones": REG_FUENTE, "no_veg": sorted(NO_VEG), "conf": CONF,
}
json.dump({"meta": meta, "cube": cube, "mun": mun, "dep": dep},
          open(OUT, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
# --- Insertar los datos en la plantilla y escribir el visor final
tpl = open(TEMPLATE, encoding="utf-8").read()
assert "__DATA__" in tpl, "La plantilla no contiene el marcador __DATA__"
data_txt = open(OUT, encoding="utf-8").read().replace("</", "<\\/")
open(OUT_HTML, "w", encoding="utf-8").write(tpl.replace("__DATA__", data_txt))
print("Eventos:", meta["eventos"], "| filas del cubo:", len(g))
print("Visor generado:", OUT_HTML, f"({os.path.getsize(OUT_HTML)/1e6:.1f} MB)")
