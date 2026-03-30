import { useEffect, useState } from 'react'
import { prediccionesApi } from '../services/api'
import Loading from '../components/Loading'
import ErrorMsg from '../components/ErrorMsg'

function StatCard({ titulo, valor, subtitulo, color }) {
  return (
    <div className="bg-gray-800 rounded-xl shadow-sm border border-gray-700 p-6">
      <p className="text-sm text-gray-400 font-medium">{titulo}</p>
      <p className={`text-3xl font-black mt-2 ${color}`}>{valor}</p>
      {subtitulo && <p className="text-xs text-gray-500 mt-1">{subtitulo}</p>}
    </div>
  )
}

export default function Estadisticas() {
  const [stats, setStats] = useState(null)
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState(null)

  const cargar = async () => {
    setCargando(true)
    setError(null)
    try {
      const res = await prediccionesApi.estadisticas()
      setStats(res.data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Error al cargar estadisticas')
    } finally {
      setCargando(false)
    }
  }

  useEffect(() => {
    cargar()
  }, [])

  if (cargando) return <Loading mensaje="Cargando estadisticas..." />
  if (error) return <ErrorMsg mensaje={error} onReintentar={cargar} />
  if (!stats) return null

  const pctColor = stats.porcentaje_acierto >= 60 ? 'text-green-400' :
                   stats.porcentaje_acierto >= 40 ? 'text-yellow-400' : 'text-red-400'

  return (
    <div className="max-w-4xl mx-auto px-4 py-6">
      <h1 className="text-2xl font-bold text-gray-100 mb-6">Estadisticas del Modelo</h1>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <StatCard
          titulo="Total predicciones"
          valor={stats.total_predicciones}
          color="text-gray-100"
        />
        <StatCard
          titulo="Verificadas"
          valor={stats.verificadas}
          subtitulo={`de ${stats.total_predicciones} totales`}
          color="text-blue-400"
        />
        <StatCard
          titulo="Acertadas"
          valor={stats.acertadas}
          subtitulo={`de ${stats.verificadas} verificadas`}
          color="text-green-400"
        />
        <StatCard
          titulo="% Acierto"
          valor={`${stats.porcentaje_acierto}%`}
          color={pctColor}
        />
      </div>

      {stats.verificadas > 0 && (
        <div className="bg-gray-800 rounded-xl shadow-sm border border-gray-700 p-6">
          <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wide mb-4">
            Rendimiento
          </h2>
          <div className="w-full bg-gray-700 rounded-full h-8 overflow-hidden flex">
            {stats.acertadas > 0 && (
              <div
                className="bg-green-500 h-8 flex items-center justify-center text-white text-xs font-bold transition-all duration-500"
                style={{ width: `${stats.porcentaje_acierto}%` }}
              >
                {stats.acertadas} acertadas
              </div>
            )}
            {stats.falladas > 0 && (
              <div
                className="bg-red-500/70 h-8 flex items-center justify-center text-white text-xs font-bold transition-all duration-500"
                style={{ width: `${100 - stats.porcentaje_acierto}%` }}
              >
                {stats.falladas} fallidas
              </div>
            )}
          </div>
        </div>
      )}

      {stats.verificadas === 0 && (
        <div className="text-center py-10 text-gray-500">
          <p>Aun no hay predicciones verificadas.</p>
          <p className="text-sm mt-1">Genera predicciones y verificalas cuando los partidos finalicen.</p>
        </div>
      )}
    </div>
  )
}
