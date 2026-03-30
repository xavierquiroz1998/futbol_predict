import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { prediccionesApi } from '../services/api'
import Loading from '../components/Loading'
import ErrorMsg from '../components/ErrorMsg'

function formatFecha(fechaStr) {
  const fecha = new Date(fechaStr)
  return fecha.toLocaleDateString('es', { day: '2-digit', month: '2-digit', year: 'numeric' })
}

function formatHora(fechaStr) {
  const fecha = new Date(fechaStr)
  return fecha.toLocaleTimeString('es', { hour: '2-digit', minute: '2-digit' })
}

export default function Historial() {
  const [items, setItems] = useState([])
  const [soloVerificadas, setSoloVerificadas] = useState(false)
  const [cargando, setCargando] = useState(true)
  const [actualizando, setActualizando] = useState(false)
  const [error, setError] = useState(null)

  const cargar = async () => {
    setCargando(true)
    setError(null)
    try {
      const res = await prediccionesApi.historial(soloVerificadas)
      setItems(res.data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Error al cargar historial')
    } finally {
      setCargando(false)
    }
  }

  const actualizarResultados = async () => {
    setActualizando(true)
    try {
      await prediccionesApi.actualizarResultados()
      await cargar()
    } catch (err) {
      // silenciar
    } finally {
      setActualizando(false)
    }
  }

  useEffect(() => {
    cargar()
  }, [soloVerificadas])

  const labelMap = {
    local: 'Gana Local',
    empate: 'Empate',
    visitante: 'Gana Visitante',
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-100">Historial de Predicciones</h1>
        <div className="flex items-center gap-3">
          <button
            onClick={actualizarResultados}
            disabled={actualizando}
            className="px-3 py-2 bg-purple-600 text-white rounded-lg text-sm font-medium hover:bg-purple-700 disabled:opacity-50 transition-colors"
          >
            {actualizando ? 'Actualizando...' : 'Actualizar resultados'}
          </button>
        <label className="flex items-center gap-2 text-sm text-gray-400 cursor-pointer">
          <input
            type="checkbox"
            checked={soloVerificadas}
            onChange={(e) => setSoloVerificadas(e.target.checked)}
            className="w-4 h-4 rounded border-gray-600 bg-gray-700 text-green-600 focus:ring-green-500"
          />
          Solo verificadas
        </label>
        </div>
      </div>

      {cargando && <Loading mensaje="Cargando historial..." />}
      {error && <ErrorMsg mensaje={error} onReintentar={cargar} />}

      {!cargando && !error && items.length === 0 && (
        <div className="text-center py-20 text-gray-500">
          <p className="text-lg">No hay predicciones aun</p>
          <p className="text-sm mt-1">Genera predicciones desde la pagina de partidos</p>
        </div>
      )}

      {!cargando && !error && items.length > 0 && (
        <div className="space-y-3">
          {items.map((item) => {
            const p = item.partido
            const pred = item.prediccion
            return (
              <Link
                key={pred.partido_api_id}
                to={`/partido/${p.api_id}`}
                className="block bg-gray-800 rounded-xl border border-gray-700 p-4 hover:border-gray-600 transition-all"
              >
                {/* Header */}
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    {p.liga_logo_url && <img src={p.liga_logo_url} alt="" className="w-4 h-4 object-contain" />}
                    <span className="text-xs text-gray-500">{p.liga_nombre}</span>
                  </div>
                  <span className="text-xs text-gray-500">{formatFecha(p.fecha)} - {formatHora(p.fecha)}</span>
                </div>

                {/* Equipos y marcador */}
                <div className="flex items-center justify-between gap-3 mb-3">
                  <div className="flex items-center gap-2 flex-1 justify-end">
                    <span className="text-sm font-semibold text-gray-200 text-right">{p.equipo_local_nombre}</span>
                    {p.equipo_local_logo && <img src={p.equipo_local_logo} alt="" className="w-7 h-7 object-contain" />}
                  </div>

                  <div className="text-center min-w-[50px]">
                    {p.finalizado || p.goles_local !== null ? (
                      <span className="text-lg font-bold text-gray-100">{p.goles_local} - {p.goles_visitante}</span>
                    ) : (
                      <span className="text-sm text-gray-500">vs</span>
                    )}
                  </div>

                  <div className="flex items-center gap-2 flex-1">
                    {p.equipo_visitante_logo && <img src={p.equipo_visitante_logo} alt="" className="w-7 h-7 object-contain" />}
                    <span className="text-sm font-semibold text-gray-200">{p.equipo_visitante_nombre}</span>
                  </div>
                </div>

                {/* Prediccion */}
                <div className="flex items-center justify-between pt-3 border-t border-gray-700">
                  <div className="flex items-center gap-2">
                    <span className={`px-2 py-1 text-xs font-semibold rounded ${
                      pred.prediccion === 'local' ? 'bg-green-900/50 text-green-300' :
                      pred.prediccion === 'empate' ? 'bg-yellow-900/50 text-yellow-300' :
                      'bg-blue-900/50 text-blue-300'
                    }`}>
                      {labelMap[pred.prediccion]}
                    </span>
                    <span className="text-xs text-gray-500">
                      L:{(pred.prob_local * 100).toFixed(0)}% E:{(pred.prob_empate * 100).toFixed(0)}% V:{(pred.prob_visitante * 100).toFixed(0)}%
                    </span>
                  </div>

                  <div>
                    {pred.acertada === null ? (
                      <span className="text-xs text-gray-600">Pendiente</span>
                    ) : pred.acertada ? (
                      <span className="px-2 py-1 rounded text-xs font-bold bg-green-500 text-white">Acerto</span>
                    ) : (
                      <span className="px-2 py-1 rounded text-xs font-bold bg-red-500 text-white">Fallo</span>
                    )}
                  </div>
                </div>
              </Link>
            )
          })}
        </div>
      )}
    </div>
  )
}
