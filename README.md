# Línea base de incendios de vegetación en Colombia y evaluación de metas ajustada por El Niño

Visor HTML autocontenido y flujo de procesamiento para tres tareas. La primera es definir la línea base nacional de incendios de vegetación que se entregará al Ministerio de Ambiente y Desarrollo Sostenible como insumo del Plan Nacional de Desarrollo (PND 2027–2030). La segunda es identificar dónde y cómo concentrar las estrategias de reducción. La tercera es evaluar, año a año, si las medidas reducen los incendios una vez descontado el efecto de El Niño.

Elaborado en el marco del trabajo de la Subdirección para el Conocimiento del Riesgo (SCR) de la UNGRD. Este documento describe todo lo construido, las decisiones metodológicas y la forma de usar y modificar la herramienta. Está escrito para que una persona o un asistente de IA pueda retomar el trabajo sin contexto adicional.

**Configuración oficial (versión final de octubre de 2026):** todos los eventos de vegetación, sin filtro de confianza (solo se excluyen fuentes fijas y falsos positivos); periodo base 2022–2025; calibración de enero de 2022 a agosto de 2026 con corrección del cambio de sensores de 2024. **Línea base recomendada: 138.399 eventos/año** (promedio 2022–2025 homogenizado a la constelación actual). Como indicador complementario de calidad se reportan los eventos de confianza media o superior, equivalentes a unos 85.564 eventos/año. La justificación está en la sección 3.4 y los métodos en la sección 8.

**Acceso al visor en línea:** https://jorgealpala.github.io/linea-base-incendios/ (GitHub Pages; sirve `index.html`, que es la versión online del visor con D3 cargado desde cdnjs). La memoria técnica formal está en `Memoria_tecnica_linea_base_incendios.docx` y su versión `.pdf`.

---

## 1. Contenido de la carpeta

La carpeta de trabajo local es `C:\Users\MSI\Downloads\lineabase_incendios`.

| Archivo | Tipo | Función |
|---|---|---|
| `incendios.csv` / `incendios.parquet` | Insumo | Detecciones de incendios (agrupaciones de focos por evento), con municipio y departamento asignados. |
| `municipios_simplificado.geojson` | Insumo | Límites municipales (campos `MpCodigo`, `MpNombre`, `Depto`). |
| `departamentos_simplificado.geojson` | Insumo | Límites departamentales (campos `DeCodigo`, `DeNombre`). |
| `regiones_pluviometricas.csv` | Insumo opcional | Asignación municipio → región pluviométrica (columnas: código de municipio, región). Si existe, reemplaza la regionalización por defecto. |
| `preparar_datos_visor.py` | Script | Depura, agrega y simplifica los insumos; genera `datos_visor.json` y el visor final. |
| `visor_template.html` | Plantilla | Interfaz y lógica del visor (HTML, CSS, JavaScript y la librería D3 v7.8.5 incrustada). Contiene el marcador `__DATA__`. |
| `visor_linea_base_incendios.html` | Producto | Visor final con los datos incrustados (unos 4,5 MB). Funciona sin servidor y sin internet. |
| `datos_visor.json` | Intermedio | Datos agregados que el script inserta en la plantilla. |
| `regiones_pluviometricas_chirps_gee.js` | Script GEE | Regionalización pluviométrica municipal con CHIRPS 1991–2020 por k-medias; exporta `regiones_pluviometricas.csv`. |
| `visor_linea_base_incendios_online.html` | Producto | Misma versión del visor, pero carga D3 desde cdnjs; es la que se publica en línea. |
| `Memoria_tecnica_linea_base_incendios.docx` / `.pdf` | Documentación | Memoria técnica formal: datos, depuración, métodos, resultados, uso del visor y limitaciones. |
| `README.md` | Documentación | Este documento. |

## 2. Cómo ejecutar

```bash
pip install pandas shapely pyproj      # pyarrow solo si se quiere leer el .parquet
cd C:\Users\MSI\Downloads\lineabase_incendios
python preparar_datos_visor.py
```

El script toma los insumos de la carpeta en la que está guardado y escribe `visor_linea_base_incendios.html` en esa misma carpeta. Ese es el archivo que se abre en el navegador. También acepta rutas explícitas:

```bash
python preparar_datos_visor.py <carpeta_insumos> <ruta_salida.html>
```

Abrir `visor_template.html` directamente no funciona, porque es la plantilla sin datos; en ese caso la página muestra un aviso. Lee primero el `.parquet` y, si falla (por ejemplo, porque falta pyarrow), usa el `.csv`.

Para usar la regionalización CHIRPS:

1. Ejecute `regiones_pluviometricas_chirps_gee.js` en Google Earth Engine.
2. Descargue de Drive el archivo `regiones_pluviometricas.csv`.
3. Guárdelo en la carpeta y vuelva a ejecutar el script.

Si los valores de la columna `region` son numéricos, se rotulan como «Región 1», «Región 2», etc. Se pueden reemplazar en el CSV por nombres descriptivos, como «Monomodal Caribe».

## 3. Datos de entrada y depuración

### 3.1 Fuente

Los eventos provienen de agrupaciones de detecciones térmicas satelitales de varias constelaciones: VIIRS (S-NPP, NOAA-20/21), MODIS (Aqua/Terra), geoestacionarios (GOES/EUMETSAT), OroraTech (satélites OT) y Sentinel-2/3 y Landsat. Cada evento trae, entre otros campos:

- `id`, `lon`, `lat` y `area` (se asumió que está en hectáreas; **debe confirmarse con el proveedor**).
- `fire_confidence`, `type_string`, `algorithms` y `satellites`.
- `oldest_acquisition` y `newest_detection`.
- `cod_muni`, `municipio`, `cod_depto` y `departamento`.

### 3.2 Depuración aplicada por el script

| Paso | Resultado |
|---|---|
| Registros leídos | 674.252 |
| Eliminación de duplicados por `id` | **666.506 eventos únicos** |
| Periodo cubierto | 7 de diciembre de 2019 a 30 de septiembre de 2026 |
| Fecha de referencia del evento | `oldest_acquisition` (año y mes) |
| Eventos sin municipio asignado | 495 (cuentan en el total nacional, pero no en ninguna unidad ni región) |
| Fuentes fijas y falsos positivos | Tipos `steel, industry, sun, solar, falseDetection, factory, processing, volcano, cement, structure, hotStone, flare` (unos 1.060 eventos), marcados con `x = 1` y excluidos por defecto |
| Área por evento | Acotada al percentil 99,9 (5.340,8 ha), porque existían valores de hasta 10⁶ |
| Sensores | Codificados como máscara de bits: VIIRS = 1, MODIS = 2, geoestacionarios = 4, OroraTech = 8, Sentinel/Landsat = 16 |
| Confianza | Índice 0–4: datos insuficientes, baja, media, alta, muy alta |

### 3.3 Hallazgo crítico: la serie no es homogénea

La capacidad de observación de la fuente cambia durante el periodo:

| Año | Total eventos* | Con VIIRS | Con MODIS | Con GOES | Con OroraTech | Con Sentinel/Landsat |
|---|---|---|---|---|---|---|
| 2021 | 54.282 | 0 | 0 | 26.315 | 31.436 | 2.358 |
| 2022 | 88.712 | 0 | 0 | 15.898 | 71.717 | 2.872 |
| 2023 | 115.117 | 431 | 0 | 14.816 | 99.125 | 3.516 |
| 2024 | 156.384 | 85.698 | 5.252 | 11.870 | 74.990 | 6.181 |
| 2025 | 133.549 | 76.110 | 10.449 | 9.471 | 44.360 | 7.904 |
| 2026 (ene–sep) | 110.756 | 63.552 | 8.380 | 9.107 | 34.370 | 6.127 |

\*Excluye fuentes fijas. Un evento puede tener varios sensores, por lo que las columnas no suman el total.

Este cambio tiene cuatro consecuencias:

- VIIRS y MODIS se incorporan a la fuente en 2024. Antes de 2023, casi todos los eventos tienen confianza «datos insuficientes».
- Ninguna familia de sensores es constante entre 2021 y 2025. Por eso filtrar por un sensor o por confianza **no** produce una serie homogénea.
- El aumento de 2021 a 2024 es en buena parte instrumental. El modelo ENSO incluye un término de cambio de sensores en 2024 por esa razón.
- En 2021 la constelación de OroraTech aún se estaba ampliando. Ese año degrada el pronóstico, así que la calibración del modelo ENSO empieza por defecto en 2022.

### 3.4 Clasificación de confianza y configuración oficial

La confianza de detección no existe de forma estable en toda la serie. Antes de septiembre de 2023 todos los eventos tienen la clase «datos insuficientes». Entre noviembre de 2023 y julio de 2024, la proporción de eventos con confianza media o superior es baja y variable (6 % a 28 %). Desde **agosto de 2024** esa proporción se estabiliza entre 45 % y 73 %.

| Año | Todas las confianzas | Confianza media, alta y muy alta |
|---|---|---|
| 2021 | 54.111 | 0 |
| 2022 | 88.650 | 0 |
| 2023 | 115.050 | 1.697 |
| 2024 | 156.301 | 51.637 |
| 2025 | 133.503 | 82.537 |
| 2026 (ene–sep) | 110.722 | 67.167 |

Valores con municipio asignado y sin fuentes fijas.

Se evaluaron tres alternativas: todos los eventos, excluir solo «datos insuficientes» y conservar solo confianza media o superior. Excluir solo «datos insuficientes» **no** resuelve el problema, porque esa clase significa «no clasificado» y cubre casi todo antes de 2024:

| Año | Sin «datos insuficientes» |
|---|---|
| 2021 | 0 % |
| 2022 | 0 % |
| 2023 | 12 % |
| 2024 | 66 % |
| 2025 | 98 % |

En su mes a mes, esta alternativa solo supera el 90 % de los eventos desde agosto de 2024.

**Decisión final: todos los eventos, periodo base 2022–2025.** Las razones son cuatro:

1. Es la única definición estable en el tiempo.
2. Permite una línea base de cuatro años, con La Niña, El Niño 2023–24 y un año neutro.
3. Permite estimar β dentro de la misma serie, sin dos etapas.
4. En un indicador de reducción importa la consistencia, porque los sesgos de nivel se cancelan en O/E.

**Costo:** el nivel incluye detecciones de baja confianza (36 % en 2025) y depende de la corrección de sensores de 2024. Por eso se interpreta como índice de ocurrencia detectada.

**Verificación cruzada:** la proporción de eventos de confianza media o superior fue 61,8 % en 2025 y 60,7 % en 2026. Aplicada a la línea base oficial equivale a 85.564 eventos/año. Una estimación independiente solo con esa calidad (año neutro calibrado desde agosto de 2024, β en dos etapas) dio 82.733, una diferencia del 3 %.

Si se filtra por confianza, el visor sigue adaptándose automáticamente:

- Recomienda usar 2025 como año base.
- Calibra el modelo desde agosto de 2024.
- Estima β en dos etapas.
- Toma el año neutro como línea base.

## 4. Preprocesamiento (`preparar_datos_visor.py`)

El script ejecuta los pasos en este orden:

1. Lee los campos necesarios del parquet o del CSV y elimina duplicados por `id`.
2. Deriva el año, el mes, la máscara de sensores `s`, la clase de confianza `c`, la marca de no vegetación `x` y el área acotada `a`.
3. Simplifica las geometrías: tolerancia de 0,004° en municipios y 0,006° en departamentos, coordenadas a 4 decimales. Calcula el área geodésica de cada polígono en km² con `pyproj.Geod`.
4. Asigna a cada municipio su región pluviométrica en la propiedad `r` (ver sección 7).
5. Construye un **cubo agregado** con 114.596 filas, una por cada combinación de municipio (`m`, índice en el GeoJSON; −1 si no tiene municipio), año (`y`), mes (`mo`), confianza (`c`), máscara de sensores (`s`) y marca de no vegetación (`x`). Cada fila guarda dos medidas: `n` (número de eventos) y `a` (suma del área acotada).
6. Escribe `datos_visor.json` con cuatro bloques: `meta` (fechas, conteos, umbral de área, tipos excluidos, fuente de las regiones), `cube` (arreglos columnares), `mun` y `dep` (GeoJSON simplificados).
7. Inserta el JSON en `visor_template.html`, en lugar del marcador `__DATA__`, escapando `</`. Escribe el visor final.

Todo el filtrado posterior (confianza, sensores, no vegetación, ámbito) se hace en el navegador sobre el cubo. Por eso cualquier combinación de filtros recalcula todo de forma inmediata.

## 5. El visor: secciones y funciones

### 5.1 Panel lateral (afecta a todo el visor)

- **Ámbito:** Colombia o un departamento. Con un departamento, la unidad pasa a municipio y todos los cálculos se restringen a él.
- **Unidad de análisis:** departamento o municipio.
- **Variable:** eventos o área en hectáreas. El módulo ENSO usa siempre eventos.
- **Periodo de línea base:** solo años completos de 2021 a 2025; por defecto, 2022–2025 (configuración oficial).
- **Estadístico:** media o mediana.
- **Año horizonte de la meta:** 2028, 2030 o 2032.
- **Filtros:** clases de confianza (por defecto, todas), familias de sensores y exclusión de fuentes fijas.
- **Umbral de alta concentración:** porcentaje acumulado de Pareto, 60 % por defecto.
- **Umbral de tendencia creciente:** 5 % por año por defecto. Se aplica a la **tendencia relativa** (tendencia de la unidad menos la del ámbito), para no confundir el aumento instrumental común con un crecimiento local.

### 5.2 Ficha y advertencias

La ficha resume cuatro valores del ámbito o de la unidad seleccionada:

- La línea base, con su rango.
- La tendencia del periodo base.
- La comparación de 2026 (enero a septiembre) contra el mismo periodo de la línea base.
- La meta del escenario por tipología.

Debajo aparecen advertencias automáticas en tres casos: si el periodo base incluye años anteriores a 2024, si se excluye la clase «datos insuficientes», o si hay menos de tres años base.

### 5.3 Distribución espacial

Mapa coroplético que puede mostrar cinco variables: línea base por 1.000 km², línea base total, tendencia, tipología de intervención o región pluviométrica. Al hacer clic en una unidad se abre su ficha, su serie y su estrategia. San Andrés se dibuja en un recuadro aparte.

### 5.4 Serie anual, línea base y meta

Muestra en barras los años 2021 a 2026 (2026 es parcial y va rayado), sobre una banda con el rango del periodo base. Encima se trazan la línea base, un escenario tendencial (pendiente de Sen proyectada al horizonte) y la trayectoria hasta la meta.

### 5.5 Estacionalidad

Muestra la distribución mensual dentro del periodo base, destacando los tres meses pico. Sugiere una **ventana de prevención**: los dos meses anteriores al inicio de la temporada alta. La temporada alta se define como el bloque de meses contiguo al pico con una participación superior a 1,2/12.

### 5.6 Escenario de meta por tipología

Cada unidad recibe una de cuatro tipologías:

| Tipología | Regla | Enfoque |
|---|---|---|
| Crítico | Dentro del umbral de Pareto **y** tendencia mayor que el umbral | Intervención integral prioritaria |
| Persistente | Dentro del umbral de Pareto, tendencia no creciente | Consolidación y sostenibilidad |
| Emergente | Fuera del umbral de Pareto, tendencia mayor que el umbral y línea base mayor o igual a la mediana de las unidades con registros | Prevención temprana |
| Vigilancia | Resto | Monitoreo y preparación |

El usuario asigna una reducción por tipología; por defecto, 35 %, 25 %, 30 % y 5 %. La meta del ámbito es:

Meta = LB × Σ LBᵢ(1 − rᵢ) / Σ LBᵢ

La sección incluye la curva de Pareto, el aporte de cada tipología a la reducción y fichas con las líneas de acción de cada una.

### 5.7 Priorización de unidades

Tabla ordenable con estas columnas: rango, línea base, participación y acumulado, densidad, tendencia, cambio de 2026, meses pico, tipología, meta y reducción absoluta. Se puede copiar como texto separado por tabulaciones.

### 5.8 Calidad y homogeneidad

Gráfico de la participación anual de cada familia de sensores, con las notas metodológicas de depuración.

### 5.9 Eventos por año, El Niño y regiones pluviométricas

Esta sección agrupa siete elementos:

- **Controles:** región, rezago del ONI (automático o fijo de 0 a 3 meses), inicio de la calibración y fuente de la sensibilidad al ONI («Serie completa 2022–2026», por defecto, o «Serie filtrada»), además de la corrección del cambio de sensores de 2024. El inicio de la calibración puede ser automático (por defecto), enero de 2021, 2022 o 2023, o agosto de 2024. En modo automático empieza en agosto de 2024 si se excluye «datos insuficientes» y en enero de 2022 en caso contrario.
- **Serie mensual 2021–2026:** franjas de meses El Niño o La Niña, barras observadas, ajuste del modelo y ONI en el eje derecho.
- **Mapa de regiones pluviométricas:** al hacer clic en una región se filtran la serie mensual y la tabla anual.
- **Panel «Cómo entra cada región en el cálculo»:** para la región y el año de cálculo elegidos, muestra la cadena completa con los valores (serie propia, régimen estacional α, respuesta β con su rezago, factor de sensores, esperado del año y aporte al total). Incluye un gráfico mes a mes que compara el año neutro con el año con su ONI, y barras apiladas con el aporte de cada región a la línea base y al esperado.
- **Tabla de eventos por año y fase ENSO:** meses El Niño, eventos en esos meses y medias mensuales. Es descriptiva y no controla la estacionalidad.
- **Línea base para el PND:** el valor recomendado y los complementarios de la sección 8.3, en total y por región, más el indicador complementario de confianza media o superior. La ficha superior muestra también la línea base recomendada cuando no hay unidad seleccionada.
- **Tabla de sensibilidad al ONI por región:** efecto por grado con su intervalo de confianza del 95 %, factor de sensores, dispersión y error anual de validación cruzada.

### 5.10 Formulario de evaluación de metas ajustado por El Niño

El formulario tiene tres partes:

1. **ONI mensual** de 2020 al año horizonte. Los años 2020–2025 vienen precargados con valores NOAA. En 2026 y los años siguientes hay dos formas de ingreso: «ONI mensual», o «Meses Niño» con casillas por mes e intensidad débil (0,7), moderada (1,2), fuerte (1,7) o muy fuerte (2,2). Las celdas se colorean según la fase.
2. **Eventos observados por año:** total del ámbito y, de forma opcional, por región.
3. **Resultados:** esperado sin medidas, banda del 90 %, meta ajustada, observado, cambio frente a lo esperado, efecto ENSO y cambio total frente a la línea base, cambio frente al año anterior (observado y ajustado por ENSO, con ● si es significativo), veredicto y cumplimiento de la meta, por año y acumulado para el periodo del PND. Incluye el detalle regional y la exportación a CSV (separador `;`, UTF-8) o al portapapeles.

Los valores se guardan en el `localStorage` del navegador (clave `lb_incendios_form_v3`; el cambio de clave restablece los valores por defecto de la configuración oficial). «Restablecer formulario» los borra. La descarga en CSV funciona en la versión local; en la versión en línea se usa «Copiar resultados».

## 6. ONI utilizado

Son los valores del ONI de NOAA CPC (ERSSTv5) suministrados por el usuario. Cada trimestre móvil se asigna a su mes central: DEF → enero, EFM → febrero, …, NDE → diciembre.

| Año | DEF | EFM | FMA | MAM | AMJ | MJJ | JJA | JAS | ASO | SON | OND | NDE |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2020 | 0,7 | 0,7 | 0,6 | 0,3 | 0,0 | −0,2 | −0,3 | −0,4 | −0,8 | −1,0 | −1,1 | −1,1 |
| 2021 | −1,0 | −0,9 | −0,7 | −0,6 | −0,4 | −0,3 | −0,3 | −0,5 | −0,6 | −0,8 | −0,9 | −0,8 |
| 2022 | −0,8 | −0,7 | −0,8 | −0,9 | −0,8 | −0,7 | −0,7 | −0,8 | −0,9 | −0,9 | −0,8 | −0,7 |
| 2023 | −0,5 | −0,3 | −0,1 | 0,2 | 0,5 | 0,7 | 1,0 | 1,3 | 1,5 | 1,7 | 1,9 | 2,0 |
| 2024 | 1,8 | 1,5 | 1,2 | 0,8 | 0,4 | 0,2 | 0,1 | 0,0 | −0,1 | −0,2 | −0,3 | −0,4 |
| 2025 | −0,5 | −0,2 | −0,1 | 0,0 | 0,0 | 0,0 | −0,1 | −0,3 | −0,4 | −0,6 | −0,6 | −0,6 |
| 2026 | −0,4 | −0,2 | 0,1 | 0,5 | 0,9 | 1,4 | 1,8 | 2,2 | — | — | — | — |

Clasificación de fases (regla operativa de NOAA): un mes es El Niño si su ONI es mayor o igual a +0,5 y forma parte de una racha de al menos cinco valores consecutivos con esa condición. La Niña sigue la misma regla con ONI menor o igual a −0,5. Con estos datos, El Niño ocurre de mayo de 2023 a abril de 2024 y desde abril de 2026. **Septiembre a diciembre de 2026 deben completarse** con valores oficiales: entran en la calibración y, con rezago, en la evaluación de 2027. Un mes sin ONI se excluye de la calibración y se asume neutro (0) en la evaluación, con una advertencia.

## 7. Regiones pluviométricas

**Regionalización por defecto.** Es una aproximación municipal por regiones naturales y régimen de lluvias del IDEAM, definida en `region_default()`:

| Región | Asignación |
|---|---|
| Caribe | Atlántico, Bolívar, Cesar, Córdoba, La Guajira, Magdalena, Sucre, San Andrés y municipios de Urabá (Turbo, Necoclí, Arboletes, San Juan de Urabá, Apartadó, Carepa, Chigorodó, San Pedro de Urabá, Mutatá) |
| Pacífica | Chocó y el litoral de Valle (Buenaventura), Cauca (Guapi, López de Micay, Timbiquí) y Nariño (Tumaco, Barbacoas, El Charco, La Tola, Magüí, Mosquera, Olaya Herrera, Francisco Pizarro, Roberto Payán, Santa Bárbara) |
| Orinoquía | Meta, Arauca, Casanare, Vichada |
| Amazonía | Caquetá, Putumayo, Guaviare, Guainía, Vaupés, Amazonas |
| Andina | Resto de municipios |

**Regionalización CHIRPS (`regiones_pluviometricas_chirps_gee.js`).** El script describe cada municipio con dos tipos de rasgos. Los primeros son las doce fracciones mensuales de la lluvia anual de la climatología CHIRPS PENTAD 1991–2020; describen la forma del régimen: monomodal o bimodal y la ubicación de la época seca. El segundo es la magnitud de la lluvia, como `log10(lluvia anual) × 0,1`. Los municipios se agrupan con `ee.Clusterer.wekaKMeans` (K = 6, semilla 7). El resultado se exporta a `regiones_pluviometricas.csv` (MpCodigo, region). Los parámetros `K` y `PESO_MAGNITUD` se pueden ajustar. Al cambiar la regionalización cambian todos los coeficientes del modelo, así que hay que revisar de nuevo la tabla de sensibilidad.

**Cómo se usan en el cálculo.** Cada región se modela por separado, con su propio régimen estacional, su sensibilidad al ONI, su rezago y su factor de sensores. El esperado nacional o del ámbito es la suma de los esperados regionales, y las varianzas regionales se suman para formar la banda total. El visor muestra esta cadena con valores en el panel de la sección 5.9.

## 8. Métodos

### 8.1 Línea base simple y tendencia

La línea base de cada unidad es la media (o mediana) de los totales anuales del periodo base. La tendencia es la pendiente de Theil-Sen (mediana de las pendientes entre pares de años), expresada como porcentaje de la línea base por año; se requieren al menos tres años. El escenario tendencial proyecta esa pendiente, con intercepto robusto, hasta el año horizonte. Por el sesgo instrumental de la sección 3.3, este escenario está inflado y **no debe usarse como referencia de meta**.

### 8.2 Modelo de respuesta a El Niño

Para cada región r se ajusta un modelo lineal generalizado de Poisson sobre los eventos mensuales, con una función de enlace logarítmica:

```
ln μ(r,t) = α(r, mes(t)) + γ(r)·D(t) + β(r)·ONI(t − L(r))
```

Los términos son:

- **α(r, mes):** doce niveles mensuales que representan el régimen estacional de la región. Los meses sin eventos se excluyen.
- **D(t):** vale 1 desde enero de 2024 (incorporación de VIIRS y MODIS) y 0 antes. Es opcional.
- **β(r):** sensibilidad a El Niño. El efecto porcentual por cada grado de ONI es exp(β) − 1.
- **L(r):** rezago de 0 a 3 meses. Se elige el de menor devianza sobre una muestra común de meses.
- **Muestra de calibración:** desde el inicio elegido (automático: agosto de 2024 con el filtro de confianza, enero de 2022 sin él) hasta el último mes con datos y ONI disponible.

**Estimación en dos etapas (configuración oficial).** La serie filtrada por confianza es corta y contiene apenas el inicio de El Niño 2026. Estimar β con ella da valores inestables: más de +100 % por grado en el Caribe, con intervalos de +2 % a +309 %. Por eso la estimación se hace en dos pasos:

1. β y L se estiman con la serie de todas las confianzas desde enero de 2022, con el término D, que incluye El Niño 2023–24 completo.
2. Los α se reestiman con la serie filtrada, tratando β·ONI como offset fijo en el GLM. Var(β) se toma de la primera etapa.

El supuesto es que la respuesta relativa a El Niño es igual para todas las clases de confianza. Se controla con `F.betaSrc` (`'full'` o `'self'`).

**Acotamiento del ONI.** En los pronósticos, el ONI se limita al rango observado en la calibración (−0,9 a 2,2 °C) para no extrapolar el modelo exponencial (`ONIR`, `oniC()`).

La estimación usa mínimos cuadrados iterativamente reponderados (IRLS) implementados en JavaScript. La sobredispersión se trata como cuasi-Poisson: φ = χ² de Pearson / (n − p), con mínimo 1, y los errores estándar se escalan por √φ.

El error interanual s(r) se estima con **validación cruzada dejando un año fuera**: para cada año completo de la calibración se reajusta el modelo sin ese año, se pronostica su total y se calcula ln(observado / pronosticado); s(r) es la raíz del promedio de esos cuadrados, con un piso de 0,10.

### 8.3 Líneas base

- **Observado:** media de los totales anuales del periodo base, sin ajuste.
- **Ajustado por el modelo (LB_hom):** media, sobre los años base, del total esperado con la constelación actual (D = 1) y el ONI real de cada año:
  `LB_hom = media_y Σ_r Σ_m exp(α_rm + γ_r + β_r·ONI_{y,m−L_r})`
- **Año neutro (LB_ref):** `LB_ref = Σ_r Σ_m exp(α_rm + γ_r)`, con ONI = 0 y la constelación actual.

Cuál se recomienda depende de la calibración:

- **Calibración desde agosto de 2024 (si se filtra por confianza):** se recomienda LB_ref, porque usa todos los meses consistentes y no depende del ENSO del año base. En el código es `E_.useRef = true`.
- **Calibración desde 2022 con todas las confianzas (configuración oficial):** se recomienda LB_hom.

El valor recomendado queda en `E_.LBrec` y por región en `E_.lbRec`. Es el que usan el formulario, el gráfico y la descomposición.

### 8.4 Evaluación de un año y del periodo

Para cada año evaluado y se calculan los siguientes valores:

- **Esperado sin medidas:**
  `E_y = Σ_r E_ry`, con `E_ry = Σ_m exp(α_rm + γ_r + β_r·ONI_{y,m−L_r})`
- **Varianza logarítmica regional:**
  `σ²_ry = φ_r/E_ry + s_r² + (∂lnE_ry/∂β_r)²·Var(β_r)`, donde `∂lnE/∂β = Σ μ_m·ONI_m / E`
- **Varianza total:** `Var(E_y) = Σ_r (E_ry·σ_ry)²`, con `σ_y = √Var / E_y`
- **Banda del 90 %:** `[E_y·e^(−1,645σ_y), E_y·e^(+1,645σ_y)]`
- **Meta ajustada:** `(1 − p)·E_y`, donde p es la reducción objetivo ingresada.

El veredicto se asigna así:

- Observado por debajo de la banda: **reducción significativa**, no explicable por la variabilidad climática (confianza unilateral del 95 %).
- Observado dentro de la banda: **dentro de la variabilidad esperada**.
- Observado por encima de la banda: **aumento no explicado por El Niño**.

**Comparación con el año anterior:** `Δ_aj = (O_t/E_t)/(O_{t−1}/E_{t−1}) − 1`. Es significativa si `|ln(1+Δ_aj)| > 1,645·√(σ_t² + σ_{t−1}²)`. Para el primer año, el año anterior es el último año completo observado de la serie.

La descomposición multiplicativa es `O/LB = (E_y/LB) × (O/E_y)`, con LB el valor recomendado. El primer factor es el efecto ENSO; el segundo, el efecto de gestión. Para el periodo del PND se suman los observados, los esperados y las varianzas de los años diligenciados, y se aplica la misma regla de veredicto.

## 9. Resultados de referencia (configuración oficial)

Configuración: todos los eventos de vegetación; todas las familias de sensores; exclusión de fuentes fijas; periodo base 2022–2025; calibración de enero de 2022 a agosto de 2026 con corrección de sensores; rezago automático; regionalización aproximada del IDEAM. **Con la regionalización CHIRPS los valores regionales cambian.**

**Línea base:**

| Concepto | Valor (eventos/año) |
|---|---|
| **Línea base 2022–2025 homogenizada (recomendada)** | **138.399** |
| Media observada 2022–2025 sin ajuste | 123.376 (123.441 en total nacional) |
| Año climatológicamente neutro | 136.268 |
| Banda del 90 % de un año neutro | 116.497 – 159.395 (−15 % / +17 %) |
| Equivalente en confianza media o superior (61,8 %) | ≈ 85.564 |

**Por región:**

| Región | Media observada | LB homogenizada | Año neutro | Efecto por +1 °C de ONI (IC 95 %) | Rezago | Factor sensores | Error anual |
|---|---|---|---|---|---|---|---|
| Caribe | 30.490 | 32.632 | 31.601 | +29,1 % (+15,2 a +44,6) | 0 | ×1,20 | ±26,2 % |
| Andina | 35.013 | 36.131 | 35.066 | +26,1 % (+14,8 a +38,5) | 1 | ×1,13 | ±15,9 % |
| Pacífica | 796 | 666 | 615 | +48,8 % (+29,3 a +71,3) | 1 | ×0,67 | ±24,8 % |
| Orinoquía | 44.099 | 52.895 | 52.907 | −2,3 % (no significativo) | 2 | ×1,54 | ±10,0 % |
| Amazonía | 12.979 | 16.075 | 16.078 | −10,0 % (no significativo) | 0 | ×1,56 | ±16,0 % |

**Distribución y estacionalidad (media 2022–2025):**

- **Departamentos:** 7 de 32 concentran el 50 % y 15 el 80 %. Los principales son Vichada 16.301 (13,2 %), Meta 15.008 (12,2 %), Casanare 8.879, Bolívar 7.381, Antioquia 6.240, Cesar 6.200 y Magdalena 6.096.
- **Municipios:** 54 de 1.117 concentran el 50 % y 248 el 80 %. Los principales son Cumaribo, Puerto Gaitán, La Primavera, Paz de Ariporo y San Vicente del Caguán. Bogotá D.C. (1.546/año) sugiere fuentes térmicas urbanas residuales.
- **Estacionalidad:** enero a marzo concentra el 46,8 % y agosto–septiembre el 17,2 %. La ventana de prevención es noviembre–diciembre.

**Ejemplo ilustrativo** (ONI hipotético: El Niño fuerte a fines de 2026 que decae en 2027, y 2028 neutro; meta del 15 %):

| Año | Esperado | Banda 90 % | Observado | Resultado |
|---|---|---|---|---|
| 2026 | 151.587 | 128.335 – 179.052 | 148.000 | Dentro de la variabilidad |
| 2027 | 151.366 | 127.368 – 179.885 | 160.000 | Dentro de la variabilidad; +15,6 % frente a la LB, atribuible a El Niño |
| 2028 | 136.268 | 116.497 – 159.395 | 112.000 | Reducción significativa; −22,2 % ajustado frente a 2027 (significativo) |

**Configuración alternativa con confianza media o superior**, solo como referencia:

- Año neutro: 82.733.
- Observado 2025: 82.537.

## 10. Uso del formulario (procedimiento para Minambiente)

1. Al cierre de cada año, obtener el número de eventos con la **misma fuente, la misma deduplicación y los mismos filtros** de la línea base. Una forma es actualizar el insumo y regenerar el visor.
2. Completar el ONI oficial de NOAA para todos los meses del año evaluado y para los meses previos que exija el rezago. Si solo se conocen los meses con El Niño, usar el modo «Meses Niño» con la intensidad correspondiente.
3. Ingresar el total observado y, de forma opcional, el desagregado regional. Si se llena el total, ese valor manda; si queda vacío y todas las regiones están llenas, se usa su suma.
4. Leer el veredicto anual, la comparación con el año anterior ajustada por ENSO y el acumulado del periodo, y exportar el CSV o copiar los resultados como soporte.

Con la configuración oficial y un año neutro (esperado 136.268, banda 116.497–159.395, meta ajustada del 15 %: 115.828), los veredictos serían estos:

- **112.000 observados:** reducción significativa; la meta se cumple.
- **125.000 observados:** dentro de la variabilidad esperada; la meta no se cumple.
- **165.000 observados:** aumento no explicado por El Niño.

La fila de 2026 sirve de prueba cuando el año esté completo.

**Actualización anual:**

1. Incorporar el nuevo año de detecciones a `incendios.csv` o `incendios.parquet`.
2. Ejecutar el script.
3. Completar el ONI en `ONI0` (plantilla) o en el formulario.
4. Publicar la nueva versión en línea (`visor_linea_base_incendios_online.html`).

No debe recalibrarse con años del plan (sección 11).

## 11. Limitaciones y recomendaciones

- **Homogeneidad instrumental.** La fuente cambia de constelación (sección 3.3). El término de sensores de 2024 corrige el salto principal, pero no toda la expansión gradual. Para la magnitud oficial de la meta conviene contrastar con una serie homogénea independiente, como VIIRS S-NPP de NASA FIRMS (desde 2012) o el área quemada MODIS MCD64A1, calculadas en Google Earth Engine. Esta fuente sirve sobre todo para la focalización territorial y estacional.
- **El modelo no debe recalibrarse con años del plan**, porque absorbería el efecto de las medidas. Si la fuente incorpora nuevos satélites, se debe reestimar el factor de sensores antes de evaluar.
- **Detecciones de baja confianza.** La serie oficial incluye la clase baja (36 % en 2025). Debe leerse como índice de ocurrencia detectada, y conviene seguir el indicador complementario de confianza media o superior.
- **Corrección de sensores.** La comparabilidad 2022–2023 frente a 2024+ depende del factor γ (entre ×1,13 y ×1,56 según la región). Hacia 2028, con tres o cuatro años completos de clasificación estable, conviene contrastar con la serie de confianza media o superior.
- **Fuentes térmicas residuales.** Algunos municipios urbanos (Bogotá D.C.) registran eventos posiblemente industriales; conviene depurarlos con el proveedor.
- **Serie consistente corta (si se filtra por confianza).** Con el filtro de confianza hay 26 meses comparables (agosto 2024–septiembre 2026) y un solo año completo. β se toma de la serie completa 2022–2026, con un El Niño completo (2023–24) y otro en curso (2026). El supuesto de β igual entre clases de confianza debe verificarse cuando la serie filtrada incluya un El Niño completo.
- **Ampliación futura de la línea base.** Con 2026 y los años siguientes completos se podrá pasar a un promedio plurianual y estimar β directamente en la serie filtrada (`F.betaSrc = 'self'`).
- **Unidad del área.** No está confirmada; el área se acotó en el percentil 99,9.
- **Regionalización por defecto.** Es una aproximación por departamento con ajustes municipales; la versión CHIRPS es preferible.
- **El ONI de NOAA se revisa periódicamente.** Conviene actualizar la tabla con la versión vigente antes de cada evaluación.
- **El formulario guarda los datos solo en el navegador.** Los resultados deben exportarse para archivarlos.

## 12. Guía técnica para modificar el visor (para personas o IA)

Toda la lógica está en `visor_template.html`, dentro de un único bloque `<script>` posterior a D3. Estado y estructuras principales:

| Objeto | Contenido |
|---|---|
| `D` | Datos incrustados: `meta`, `cube` (arreglos `m, y, mo, c, s, x, n, a`), `mun`, `dep`. |
| `S` | Estado del panel lateral: `scope, level, metric, b0, b1, stat, horizon, conf[], sens, noveg, pareto, thr, red{C,P,E,V}, mapvar, sel`. |
| `A` | Resultado de `aggregate()`: unidades con su serie anual y mensual, línea base, tendencia, tipología, meta; totales del ámbito; composición de sensores. |
| `F` | Estado del formulario ENSO, persistido en `localStorage` (`lb_incendios_form_v3`): `oni{año:[12]}, mode{}, nino{}, inten{}, obs{}, obsReg{}, meta, lag, era, reg, cal ('auto', '2021', '2022', '2023' o '2024-08'), betaSrc ('full' o 'self'), ryear`. |
| `E_` | Resultado de `ensoFit()`: series mensuales por región; modelos regionales (`alpha, gamma, beta, seBeta, L, phi, s, sRaw, fitted, back, fixed, full`); líneas base observada, ajustada y neutra; `useRef`, `LBrec`/`lbRec` (valor recomendado), `twoStage` y `oniRange`. |
| `EV` | Resultado de `drawEval()`: filas evaluadas y acumulado del PND. |

Funciones clave:

| Función | Qué hace |
|---|---|
| `pass(i)` | Aplica los filtros a una fila del cubo. |
| `aggregate()`, `computeMeta()` | Línea base, tendencia (absoluta `trend` y relativa al ámbito `trendRel`), tipologías y escenario. |
| `monthlyReg()` | Series mensuales por región. |
| `glm(X, y, off)` | Poisson por IRLS con offset opcional, dispersión y covarianza. |
| `fitRegion(series, cm, fixed)` | Selección de rezago y validación cruzada; con `fixed` estima solo α con β·ONI como offset. |
| `calStart()`, `calLabel()`, `CONF_STABLE` | Inicio de la calibración (automático según el filtro de confianza). |
| `oniC()`, `ONIR` | Acotamiento del ONI al rango de calibración. |
| `yoy()`, `obsSeriesYear()` | Comparación con el año anterior ajustada por ENSO. |
| `predictYear()`, `refNeutral()` | Esperado anual y año neutro. |
| `ensoFit()` | Ajusta todos los modelos regionales. |
| `ensoPhase()` | Clasificación NOAA de los meses. |
| `buildForm()`, `onForm()` | Construcción y eventos del formulario. |
| `evalYear()`, `verdict()`, `drawEval()` | Evaluación anual y acumulada. |
| `drawRegMap()`, `drawRegPanel()` | Mapa de regiones y cadena de cálculo. |
| `run()` → `renderAll()` | Ciclo de recálculo y dibujo completo. |

Constantes editables: `ONI0` (ONI precargado), `TYP` (tipologías y textos de estrategia), `INTENS` (intensidades del modo «Meses Niño»), `REGORD` y `REGPAL` (orden y colores de las regiones), `Z90` (1,645).

Para cambiar el ONI precargado, edite `ONI0` en la plantilla y regenere. Para cambiar la regionalización, edite `region_default()` en el script o suministre `regiones_pluviometricas.csv`.

**Reglas al modificar:**

- No edite el HTML final. Edite `visor_template.html` y regenere con el script.
- La plantilla debe contener exactamente una aparición de `__DATA__`. El código que la busca la compone como `'__DA'+'TA__'` para que el reemplazo no la altere.
- Los colores se definen como variables CSS en `:root`, con modo oscuro.

## 13. Historial de lo realizado

1. **Primera versión del visor:** línea base configurable, mapa coroplético, serie anual con meta y escenario tendencial, estacionalidad con ventana de prevención, tipologías por Pareto y tendencia de Sen, escenario de reducción por tipología, tabla de priorización y sección de calidad. Se publicó también como página en claude.ai.
2. **Hallazgo de heterogeneidad:** VIIRS y MODIS solo existen en la fuente desde 2024, y la confianza solo desde 2023. Se añadieron advertencias automáticas y notas.
3. **Corrección de ejecución local:** el visor cargaba en blanco porque se abría la plantilla. El script pasó a generar directamente el HTML final, y la plantilla muestra un aviso si se abre sin datos.
4. **Módulo ENSO:** se añadieron el ONI 2020–2026, las regiones pluviométricas, el modelo cuasi-Poisson por región con rezago y factor de sensores, la validación cruzada, las tres líneas base y el formulario de evaluación con veredictos, descomposición clima/gestión, persistencia y exportación. D3 quedó incrustado para uso sin conexión. La calibración se fijó por defecto desde 2022, porque incluir 2021 casi duplicaba el error.
5. **Regionalización CHIRPS:** script de Earth Engine, lectura opcional del CSV en el preprocesamiento y aclaración del uso del formulario.
6. **Mapa de regiones y cadena de cálculo:** mapa interactivo de regiones pluviométricas y un panel que muestra, con valores, cómo cada región entra en el esperado del año.
7. **Configuración oficial con confianza media o superior:** se detectó que, con ese filtro, el modelo producía resultados espurios (línea base de 78.666 con factores de sensores de ×66 a ×840), porque la clasificación de confianza solo existe de forma estable desde agosto de 2024. Se implementaron los siguientes cambios:
   - Año base 2025 por defecto.
   - Calibración automática desde agosto de 2024.
   - Modelo en dos etapas para β.
   - Acotamiento del ONI y piso de 10 % del error anual.
   - Línea base recomendada como año neutro (82.733).
   - Comparación con el año anterior ajustada por ENSO.
   - Nueva clave de almacenamiento.
8. **Publicación en línea y memoria técnica:** actualización del visor publicado y elaboración de la memoria técnica en Word y PDF.
9. **Decisión final de la serie oficial:** tras comparar las tres alternativas de filtro de confianza, se adoptó la de todos los eventos con base 2022–2025 (sección 3.4). Se implementaron los siguientes cambios:
   - Valores por defecto del visor actualizados.
   - Tipologías basadas en la tendencia relativa al ámbito.
   - Línea base recomendada visible en la ficha.
   - Indicador complementario de confianza media o superior.
   - Clave de almacenamiento `v3`.
   - Memoria técnica, README y versión en línea actualizados.

## 14. Posibles mejoras pendientes

- Precargar automáticamente en el formulario los observados de los años nuevos cuando se actualice el insumo y se regenere el visor. Esto garantizaría el mismo criterio de conteo.
- Incorporar una serie homogénea de largo plazo (FIRMS VIIRS S-NPP o MCD64A1) para recalibrar β con más episodios ENSO.
- Añadir otras covariables climáticas regionales, como anomalías de precipitación CHIRPS o déficit hídrico, junto con el ONI.
- Evaluar la meta también en área quemada, cuando se confirme la unidad del campo `area`.
