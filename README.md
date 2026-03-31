# Prediccion Futbol

Aplicacion web para prediccion de resultados de partidos de futbol usando Machine Learning. Muestra partidos del dia, genera predicciones con probabilidades, cuotas de apuestas y verifica aciertos una vez finalizados.

## Vista previa

### Pantalla principal - Partidos del dia
Lista de partidos agrupados por liga con logos, horarios y prediccion debajo de cada equipo ganador. Filtros por liga y pais.

### Detalle de partido - Prediccion con contexto
Estadisticas comparativas, forma reciente (V/E/D), rachas, head-to-head, cuotas de apuestas (reales o estimadas), probabilidades, marcador predicho, over/under, BTTS y analisis descriptivo con nivel de confianza.

### Historial y Estadisticas
Seguimiento de predicciones pasadas con verificacion automatica de resultados y dashboard de rendimiento.

---

## Stack Tecnologico

| Capa | Tecnologia |
|------|------------|
| **Frontend** | React 19 + Vite 8 + TailwindCSS 4 (Dark Mode) |
| **Backend** | Python 3.10 + FastAPI |
| **ML/Prediccion** | XGBoost + scikit-learn |
| **Base de datos** | PostgreSQL 16 (Docker) |
| **APIs de datos** | Football-Data.org + TheSportsDB + The Odds API |

## Arquitectura

```
Prediccion_fultbol/
├── docker-compose.yml              # PostgreSQL 16 en Docker
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI app + startup sync
│   │   ├── config.py               # Variables de entorno
│   │   ├── database.py             # SQLAlchemy (PostgreSQL/SQLite)
│   │   ├── models/
│   │   │   └── partido.py          # Modelos: Equipo, Partido, Prediccion, Cuota
│   │   ├── schemas/
│   │   │   └── partido.py          # Pydantic schemas
│   │   ├── routes/
│   │   │   ├── partidos.py         # Endpoints de partidos + filtros
│   │   │   └── predicciones.py     # Endpoints de predicciones
│   │   ├── services/
│   │   │   ├── football_api.py     # Cliente Football-Data.org v4
│   │   │   ├── thesportsdb_api.py  # Cliente TheSportsDB (internacionales)
│   │   │   ├── odds_service.py     # Cliente The Odds API (cuotas)
│   │   │   ├── historial_service.py # Busqueda de historial on-demand
│   │   │   ├── partido_service.py  # Logica de sincronizacion
│   │   │   ├── predictor.py        # Motor de prediccion ML
│   │   │   ├── contexto_service.py # Estadisticas comparativas
│   │   │   └── standings_service.py # Clasificaciones de ligas
│   │   ├── ml/
│   │   │   ├── features.py         # Feature engineering (49 features)
│   │   │   ├── train.py            # Entrenamiento XGBoost
│   │   │   ├── model.pkl           # Modelo entrenado
│   │   │   └── label_encoder.pkl   # Encoder de clases
│   │   └── scripts/
│   │       └── recolectar_historicos.py  # Recoleccion de datos
│   ├── requirements.txt
│   ├── .env.example
│   └── .gitignore
├── frontend/
│   ├── src/
│   │   ├── App.jsx                 # Router principal (Dark Mode)
│   │   ├── components/
│   │   │   ├── Navbar.jsx          # Navegacion
│   │   │   ├── PartidoCard.jsx     # Card con prediccion por equipo
│   │   │   ├── Loading.jsx         # Spinner
│   │   │   └── ErrorMsg.jsx        # Mensajes de error
│   │   ├── pages/
│   │   │   ├── Partidos.jsx        # Lista + filtros por liga/pais
│   │   │   ├── DetallePartido.jsx  # Stats + cuotas + prediccion
│   │   │   ├── Historial.jsx       # Historial con verificacion
│   │   │   └── Estadisticas.jsx    # Dashboard de aciertos
│   │   └── services/
│   │       └── api.js              # Cliente HTTP (axios)
│   ├── package.json
│   └── vite.config.js
└── README.md
```

## Flujo de prediccion on-demand

Cuando generas una prediccion, el sistema automaticamente:

1. **Busca historial** de ambos equipos en Football-Data.org y TheSportsDB
2. **Almacena los datos** en PostgreSQL para futuras predicciones
3. **Calcula 49 features** (forma, rachas, tendencias, H2H, diferenciales)
4. **Genera la prediccion** con el modelo XGBoost entrenado
5. **Busca cuotas** de casas de apuestas (The Odds API) o calcula estimadas
6. **Guarda todo** para verificar cuando el partido finalice

Esto funciona para **cualquier equipo del mundo**, no solo ligas europeas.

## Features del modelo ML

El modelo utiliza **49 features** organizados en 7 categorias:

### 1. Forma reciente (ultimos 5 partidos)
- Victorias, empates, derrotas (ratio)
- Goles a favor/contra promedio
- Puntos promedio
- Clean sheets (porteria a cero)

### 2. Forma ampliada (ultimos 10 partidos)
- Puntos, goles a favor/contra promedio a largo plazo

### 3. Rachas
- Racha de victorias consecutivas
- Racha sin perder
- Racha de derrotas consecutivas
- Racha anotando goles

### 4. Tendencia de goles
- Over/Under 2.5 goles (porcentaje)
- BTTS - Ambos anotan (porcentaje)
- Promedio total de goles por partido

### 5. Rendimiento local/visitante
- Win rate jugando de local o visitante
- Goles a favor/contra en esa condicion

### 6. Head-to-head (enfrentamientos directos)
- Victorias de cada equipo en H2H
- Empates en H2H
- Promedio de goles en H2H

### 7. Diferenciales (fuerza relativa)
- Diferencia de puntos (5 y 10 partidos)
- Diferencia de goles a favor/contra
- Diferencia de rachas

## Tipos de prediccion

La app genera 4 predicciones por partido:

| Prediccion | Descripcion |
|------------|-------------|
| **Resultado** | Gana local, empate o gana visitante con probabilidades |
| **Marcador** | Marcador exacto mas probable (ej: 2-1) |
| **Over/Under 2.5** | Si habra mas o menos de 2.5 goles totales |
| **BTTS** | Si ambos equipos anotaran (Both Teams To Score) |

## Cuotas de apuestas

La app muestra cuotas de dos formas:

| Tipo | Fuente | Cuando |
|------|--------|--------|
| **Cuotas reales** | The Odds API (21+ casas de apuestas) | Ligas cubiertas (PL, La Liga, Serie A, etc.) |
| **Cuotas estimadas** | Calculadas del modelo ML | Ligas no cubiertas o sin API key |

Las cuotas reales incluyen: media de todas las casas, probabilidades implicitas, over/under 2.5, y tabla desplegable con detalle por casa (Pinnacle, Bet365, etc.).

## Endpoints API

### Partidos
| Metodo | Ruta | Descripcion |
|--------|------|-------------|
| `GET` | `/api/partidos/ligas` | Ligas y paises disponibles para filtrar |
| `GET` | `/api/partidos/hoy?liga=X&pais=Y` | Partidos de hoy con filtros opcionales |
| `GET` | `/api/partidos/fecha/{fecha}?liga=X&pais=Y` | Partidos por fecha con filtros |
| `POST` | `/api/partidos/sincronizar/{fecha}` | Sincronizar partidos internacionales (TheSportsDB) |
| `GET` | `/api/partidos/{api_id}` | Detalle con estadisticas, contexto y cuotas |
| `GET` | `/api/partidos/{api_id}/resultado` | Resultado de partido finalizado |

### Predicciones
| Metodo | Ruta | Descripcion |
|--------|------|-------------|
| `POST` | `/api/predicciones/{partido_api_id}` | Generar prediccion (busca historial on-demand) |
| `POST` | `/api/predicciones/{partido_api_id}/verificar` | Verificar prediccion vs resultado real |
| `POST` | `/api/predicciones/actualizar-resultados` | Actualizar todos los resultados pendientes |
| `GET` | `/api/predicciones/historial` | Historial con datos completos de partidos |
| `GET` | `/api/predicciones/estadisticas` | Estadisticas de acierto del modelo |

## Instalacion

### Requisitos
- Python 3.10+
- Node.js 18+
- Docker (para PostgreSQL)
- API key de [Football-Data.org](https://www.football-data.org/) (gratis, solo email)
- Opcional: API key de [The Odds API](https://the-odds-api.com/) (gratis, 500 req/mes)

### 1. Base de datos (PostgreSQL con Docker)

```bash
docker compose up -d
```

Esto levanta PostgreSQL 16 en el puerto 5433 con la BD `prediccion_futbol`.

### 2. Backend

```bash
cd backend

# Crear entorno virtual
python -m venv venv
source venv/Scripts/activate  # Windows
# source venv/bin/activate    # Linux/Mac

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus API keys

# Entrenar modelo (usa datos historicos precargados)
python -m app.scripts.recolectar_historicos --todas --temporada 2023
python -m app.scripts.recolectar_historicos --todas --temporada 2024
python -m app.ml.train

# Iniciar servidor
uvicorn app.main:app --reload --port 8001
```

### 3. Frontend

```bash
cd frontend

# Instalar dependencias
npm install

# Iniciar servidor de desarrollo
npx vite --port 5174
```

### 4. Acceder
- **Frontend**: http://localhost:5174
- **Backend API**: http://localhost:8001
- **Documentacion API**: http://localhost:8001/docs
- **PostgreSQL**: localhost:5433 (user: futbol_user, db: prediccion_futbol)

## Fuentes de datos

### Football-Data.org (ligas oficiales)
- Plan gratuito: 10 req/min, 12 competiciones
- Competiciones: Premier League, La Liga, Serie A, Bundesliga, Ligue 1, Champions League y mas
- Datos: partidos, resultados, historial por equipo

### TheSportsDB (internacionales y complementaria)
- Gratis sin registro (key compartida: 123)
- Cubre amistosos internacionales, selecciones y ligas de todo el mundo
- Se usa para buscar historial on-demand de equipos no cubiertos por Football-Data.org

### The Odds API (cuotas de apuestas)
- Plan gratuito: 500 req/mes (registro por email)
- Cuotas 1X2 y Over/Under de 21+ casas de apuestas
- Cobertura: Premier League, La Liga, Serie A, Bundesliga, Ligue 1, Champions League, Liga MX, Brasileirao, Copa Libertadores y mas

## Rendimiento del modelo

| Metrica | Valor |
|---------|-------|
| Accuracy | ~47% |
| CV Mean (5-fold) | ~47% |
| Datos de entrenamiento | 3,317 partidos |
| Features | 49 |
| Algoritmo | XGBoost (clases balanceadas) |

> Nota: El azar en prediccion de 3 clases (local/empate/visitante) es ~33%. Un 47% es un rendimiento razonable para un modelo basado en datos historicos de resultados.

## Uso

1. **Ver partidos**: La pagina principal muestra los partidos del dia con prediccion debajo de cada equipo
2. **Filtrar**: Boton "Filtros" para buscar por pais o liga, chips rapidos de ligas principales
3. **Seleccionar fecha**: Selector de fecha para ver partidos de otros dias
4. **Generar prediccion**: Click en un partido y pulsa "Generar prediccion" (busca historial automaticamente)
5. **Ver analisis**: Estadisticas comparativas, forma reciente (V/E/D), rachas, H2H, cuotas, marcador predicho, over/under y BTTS
6. **Verificar resultados**: En historial, "Actualizar resultados" para verificar predicciones pendientes
7. **Estadisticas**: Dashboard con porcentaje de acierto global

## Mejoras futuras

- [x] ~~Prediccion de marcador exacto y over/under~~
- [x] ~~Filtros por liga y pais~~
- [x] ~~Cuotas de apuestas (reales + estimadas)~~
- [x] ~~Historial on-demand (cualquier equipo del mundo)~~
- [x] ~~PostgreSQL con Docker~~
- [x] ~~Dark mode~~
- [ ] Notificaciones de partidos proximos
- [ ] Deploy en Railway/Render (backend) + Vercel (frontend)
- [ ] Datos de alineaciones y lesiones en tiempo real

## Autor

Desarrollado como proyecto de portafolio.
