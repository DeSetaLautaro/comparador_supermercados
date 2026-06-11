# ADR 001: Selección de DuckDB como motor de base de datos

**Estado:** Aceptado

## Contexto
El proyecto necesita procesar grandes volúmenes de datos provenientes de archivos CSV de Precios Claros diariamente. Se requiere eficiencia en cálculos estadísticos 
(precios mínimos, promedios) y facilidad de despliegue.

## Decisión
Se decidió utilizar **DuckDB** como motor de análisis de datos.

## Consecuencias
### Positivas
* **Eficiencia Columnar:** Velocidad extrema para realizar consultas analíticas sobre grandes datasets.
* **Consumo de memoria:** Permite procesar datos que superan la capacidad de la memoria RAM disponible.
* **Simplicidad:** No requiere un servidor, funciona como un archivo único embebido en la aplicación.

### Negativas
* **Nicho:** No es apto para sistemas de usuarios transaccionales (alta concurrencia de escrituras), aunque para este proyecto no es una necesidad actual.