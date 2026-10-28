/*
 * Regionalización pluviométrica municipal de Colombia con CHIRPS (1991–2020)
 * Salida: regiones_pluviometricas.csv (MpCodigo, region) para el visor de línea base de incendios.
 * Colocar el CSV en la carpeta del visor y volver a ejecutar preparar_datos_visor.py.
 *
 * Criterio: cada municipio se describe por la forma de su régimen anual de lluvias
 * (fracción de la precipitación anual que cae en cada mes, que distingue regímenes
 * monomodales y bimodales y la época seca) y por su magnitud (log10 de la lluvia anual).
 * Los municipios se agrupan con k-medias.
 */

// 1. Municipios: subir municipios_simplificado.geojson como asset y ajustar la ruta
var mpios = ee.FeatureCollection('projects/TU_PROYECTO/assets/municipios_simplificado');

// 2. Parámetros
var K = 6;              // número de regiones
var PESO_MAGNITUD = 0.1; // peso relativo de la lluvia anual frente a la forma del régimen

// 3. Climatología mensual CHIRPS 1991–2020 (mm/mes)
var chirps = ee.ImageCollection('UCSB-CHG/CHIRPS/PENTAD').filterDate('1991-01-01', '2021-01-01');
var meses = ee.List.sequence(1, 12);
var nombres = meses.map(function (m) { return ee.String('p').cat(ee.Number(m).format('%02d')); });
var clim = ee.ImageCollection.fromImages(meses.map(function (m) {
  m = ee.Number(m);
  return chirps.filter(ee.Filter.calendarRange(m, m, 'month')).sum().divide(30);
})).toBands().rename(nombres);

var anual = clim.reduce(ee.Reducer.sum()).rename('anual');
var forma = clim.divide(anual);                                   // fracción mensual
var mag = anual.log10().multiply(PESO_MAGNITUD).rename('logP');   // magnitud escalada
var rasgos = forma.addBands(mag).addBands(anual);

// 4. Promedio por municipio
var tabla = rasgos.reduceRegions({
  collection: mpios.select(['MpCodigo', 'MpNombre', 'Depto']),
  reducer: ee.Reducer.mean(),
  scale: 5566,
  tileScale: 4
});
var props = nombres.add('logP');
var validos = tabla.filter(ee.Filter.notNull(props));

// 5. Agrupamiento k-medias
var clusterer = ee.Clusterer.wekaKMeans({nClusters: K, seed: 7}).train(validos, props);
var regiones = validos.cluster(clusterer, 'region');

// 6. Revisión: lluvia anual media y fracción del trimestre DEF por región
print('Municipios por región', regiones.aggregate_histogram('region'));
print('Lluvia anual media por región (mm)',
  regiones.reduceColumns(ee.Reducer.mean().group({groupField: 1, groupName: 'region'}), ['anual', 'region']));

// 7. Mapa
var img = ee.Image().int().paint(regiones, 'region');
Map.setCenter(-73.5, 4.5, 5);
Map.addLayer(img, {min: 0, max: K - 1, palette: ['d9a441', '5e8c61', '3f7ea6', 'c8622a', '2e5e3a', '8e6bb0', 'a0522d', '6b8e9e']}, 'Regiones pluviométricas');
Map.addLayer(anual.clip(mpios.geometry().bounds()), {min: 500, max: 7000, palette: ['f2e6c6', '6fb7cf', '1f5e73']}, 'Lluvia anual CHIRPS', false);

// 8. Exportar (la columna region puede renombrarse luego, p. ej. "Bimodal andina")
Export.table.toDrive({
  collection: regiones.select(['MpCodigo', 'region']),
  description: 'regiones_pluviometricas',
  fileFormat: 'CSV',
  selectors: ['MpCodigo', 'region']
});
