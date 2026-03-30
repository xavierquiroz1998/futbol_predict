# Prediccion Futbol

Aplicacion web para prediccion de resultados de partidos de futbol usando Machine Learning. Muestra partidos del dia, genera predicciones con probabilidades y verifica aciertos una vez finalizados.

## Vista previa

### Pantalla principal - Partidos del dia
Lista de partidos agrupados por liga con logos, horarios y predicciones.

### Detalle de partido - Prediccion con contexto
Estadisticas comparativas, forma reciente (V/E/D), rachas, head-to-head, probabilidades y analisis descriptivo con nivel de confianza.

### Historial y Estadisticas
Seguimiento de predicciones pasadas con verificacion automatica de resultados.

---

## Stack Tecnologico

| Capa | Tecnologia |
|------|------------|
| **Frontend** | React 19 + Vite 8 + TailwindCSS 4 |
| **Backend** | Python 3.10 + FastAPI |
| **ML/Prediccion** | XGBoost + scikit-learn |
| **Base de datos** | SQLite |
| **APIs de datos** | Football-Data.org (ligas) + TheSportsDB (internacionales) |

## Arquitectura

```
Prediccion_fultbol/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI app + startup sync
│   │   ├── config.py               # Variables de entorno
│   │   ├── database.py             # SQLAlchemy engine
│   │   ├── models/
│   │   │   └── partido.py          # Modelos: Equipo, Partido, Prediccion
│   │   ├── schemas/
│   │   │   └── partido.py          # Pydantic schemas (respuestas API)
│   │   ├── routes/
│   │   │   ├── partidos.py         # Endpoints de partidos
│   │   │   └── predicciones.py     # Endpoints de predicciones
│   │   ├── services/
│   │   │   ├── football_api.py     # Cliente Football-Data.org v4
│   │   │   ├── thesportsdb_api.py  # Cliente TheSportsDB (amistosos)
│   │   │   ├── partido_service.py  # Logica de sincronizacion
│   │   │   ├── predictor.py        # Motor de prediccion ML
│   │   │   ├── contexto_service.py # Estadisticas comparativas
│   │   │   └── actualizar_resultados.py  # Verificacion de resultados
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
│   │   ├── App.jsx                 # Router principal
│   │   ├── components/
│   │   │   ├── Navbar.jsx          # Navegacion
│   │   │   ├── PartidoCard.jsx     # Card de partido
│   │   │   ├── Loading.jsx         # Spinner
│   │   │   └── ErrorMsg.jsx        # Mensajes de error
│   │   ├── pages/
│   │   │   ├── Partidos.jsx        # Lista de partidos del dia
│   │   │   ├── DetallePartido.jsx  # Detalle + prediccion + stats
│   │   │   ├── Historial.jsx       # Historial de predicciones
│   │   │   └── Estadisticas.jsx    # Dashboard de aciertos
│   │   └── services/
│   │       └── api.js              # Cliente HTTP (axios)
│   ├── package.json
│   └── vite.config.js
└── README.md
```

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

## Endpoints API

### Partidos
| Metodo | Ruta | Descripcion |
|--------|------|-------------|
| `GET` | `/api/partidos/hoy` | Partidos de hoy (Football-Data.org + BD) |
| `GET` | `/api/partidos/fecha/{fecha}` | Partidos por fecha |
| `POST` | `/api/partidos/sincronizar/{fecha}` | Sincronizar partidos internacionales (TheSportsDB) |
| `GET` | `/api/partidos/{api_id}` | Detalle de partido con estadisticas |
| `GET` | `/api/partidos/{api_id}/resultado` | Resultado de partido finalizado |

### Predicciones
| Metodo | Ruta | Descripcion |
|--------|------|-------------|
| `POST` | `/api/predicciones/{partido_api_id}` | Generar prediccion |
| `POST` | `/api/predicciones/{partido_api_id}/verificar` | Verificar prediccion |
| `POST` | `/api/predicciones/actualizar-resultados` | Actualizar resultados y verificar pendientes |
| `GET` | `/api/predicciones/historial` | Historial de predicciones |
| `GET` | `/api/predicciones/estadisticas` | Estadisticas de acierto |

## Instalacion

### Requisitos
- Python 3.10+
- Node.js 18+
- API key de [Football-Data.org](https://www.football-data.org/) (gratis, solo email)

### Backend

```bash
cd backend

# Crear entorno virtual
python -m venv venv
source venv/Scripts/activate  # Windows
# source venv/bin/activate    # Linux/Mac

# Instalar dependencias
pip install -r requirements.txt

# Configurar API key
cp .env.example .env
# Editar .env con tu FOOTBALL_DATA_API_KEY

# Recolectar datos historicos (necesario para el modelo)
python -m app.scripts.recolectar_historicos --todas --temporada 2023
python -m app.scripts.recolectar_historicos --todas --temporada 2024

# Entrenar modelo
python -m app.ml.train

# Iniciar servidor
uvicorn app.main:app --reload --port 8001
```

### Frontend

```bash
cd frontend

# Instalar dependencias
npm install

# Iniciar servidor de desarrollo
npx vite --port 5174
```

### Acceder
- **Frontend**: http://localhost:5174
- **Backend API**: http://localhost:8001
- **Documentacion API**: http://localhost:8001/docs

## Fuentes de datos

### Football-Data.org (principal)
- Plan gratuito: 10 req/min, 12 competiciones
- Competiciones: Premier League, La Liga, Serie A, Bundesliga, Ligue 1, Champions League y mas
- Datos: partidos, resultados, clasificaciones

### TheSportsDB (complementaria)
- Gratis sin registro (key compartida: 123)
- Cubre amistosos internacionales y selecciones
- Se sincroniza al iniciar la app y con boton manual

## Rendimiento del modelo

| Metrica | Valor |
|---------|-------|
| Accuracy | ~47% |
| CV Mean (5-fold) | ~46.5% |
| Datos de entrenamiento | 3,317 partidos |
| Features | 49 |
| Algoritmo | XGBoost (clases balanceadas) |

> Nota: El azar en prediccion de 3 clases (local/empate/visitante) es ~33%. Un 47% es un rendimiento razonable para un modelo basado solo en datos historicos de resultados sin datos adicionales como alineaciones, lesiones o mercado de apuestas.

## Uso

1. **Ver partidos**: La pagina principal muestra los partidos del dia
2. **Seleccionar fecha**: Usa el selector de fecha para ver partidos de otros dias
3. **Generar prediccion**: Click en un partido y pulsa "Generar prediccion"
4. **Ver analisis**: Estadisticas comparativas, forma reciente, rachas, H2H y nivel de confianza
5. **Verificar resultados**: En el historial, pulsa "Actualizar resultados" para verificar predicciones pendientes
6. **Estadisticas**: Dashboard con porcentaje de acierto global

## Mejoras futuras

- [ ] Agregar datos de alineaciones y lesiones
- [ ] Prediccion de marcador exacto y over/under
- [ ] Notificaciones de partidos proximos
- [ ] Filtros por liga y pais
- [ ] Docker Compose para deploy
- [ ] Deploy en Railway/Render (backend) + Vercel (frontend)
- [ ] Datos de cuotas de apuestas como feature adicional

## Autor

Desarrollado como proyecto de portafolio.
