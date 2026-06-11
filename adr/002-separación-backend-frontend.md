# ADR 002: Separación de lógica de negocio (Backend) y presentación (Frontend)

**Estado:** Aceptado (Evolutivo)

## Contexto
Se requiere rapidez para validar la funcionalidad del comparador de precios (MVP). Integrar todo en un solo bloque con Streamlit permite una iteración rápida, pero dificulta la escalabilidad y la profesionalización del backend en el futuro.

## Decisión
Se desarrollará el proyecto utilizando un patrón de capas (Servicios independientes). 
1. **Fase 1 (MVP):** Interfaz en Streamlit consumiendo los servicios directamente desde `comparator/services.py`.
2. **Fase 2 (Escalabilidad):** Migración del backend hacia **FastAPI**, donde Streamlit actuará únicamente como cliente de la API REST.

## Consecuencias
### Positivas
* **Time-to-market:** El MVP estará operativo rápidamente.
* **Arquitectura desacoplada:** La lógica de negocio (`services.py`) es agnóstica al framework web.
* **Roadmap claro:** Existe una ruta definida de aprendizaje y mejora técnica sin necesidad de refactorizar desde cero.

### Negativas
* **Esfuerzo extra:** Requiere disciplina para no mezclar lógica de visualización (Streamlit) dentro de los servicios.