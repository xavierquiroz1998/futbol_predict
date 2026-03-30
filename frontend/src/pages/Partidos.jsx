import { useEffect, useState, useCallback } from 'react'
import { partidosApi } from '../services/api'
import PartidoCard from '../components/PartidoCard'
import Loading from '../components/Loading'
import ErrorMsg from '../components/ErrorMsg'

function formatFecha(date) {
  return date.toISOString().split('T')[0]
}

export default function Partidos() {
  const [partidos, setPartidos] = useState([])
  const [fecha, setFecha] = useState(formatFecha(new Date()))
  const [cargando, setCargando] = useState(true)
  const [sincronizando, setSincronizando] = useState(false)
  const [error, setError] = useState(null)

  const cargar = useCallback(async () => {
    setCargando(true)
    setError(null)
    try {
      const hoy = formatFecha(new Date())
      let res
      if (fecha === hoy) {
        res = await partidosApi.obtenerHoy()
      } else {
        res = await partidosApi.obtenerPorFecha(fecha, true)
      }
      setPartidos(res.data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Error al cargar partidos')
    } finally {
      setCargando(false)
    }
  }, [fecha])

  const sincronizarInternacionales = async () => {
    setSincronizando(true)
    try {
      await partidosApi.sincronizar(fecha)
      await cargar()
    } catch (err) {
      // Silenciar errores de sincronización
    } finally {
      setSincronizando(false)
    }
  }

  useEffect(() => {
    cargar()
  }, [cargar])

  const porLiga = partidos.reduce((acc, item) => {
    const liga = item.partido.liga_nombre
    if (!acc[liga]) acc[liga] = []
    acc[liga].push(item)
    return acc
  }, {})

  return (
    <div className="max-w-4xl mx-auto px-4 py-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-100">Partidos</h1>
        <div className="flex items-center gap-2">
          <button
            onClick={sincronizarInternacionales}
            disabled={sincronizando}
            className="px-3 py-2 bg-green-600 text-white rounded-lg text-sm font-medium hover:bg-green-700 disabled:opacity-50 transition-colors"
          >
            {sincronizando ? 'Sincronizando...' : 'Actualizar'}
          </button>
          <input
            type="date"
            value={fecha}
            onChange={(e) => setFecha(e.target.value)}
            className="px-3 py-2 bg-gray-800 border border-gray-700 text-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-green-500 focus:border-transparent"
          />
        </div>
      </div>

      {(cargando || sincronizando) && <Loading mensaje={sincronizando ? 'Buscando partidos internacionales...' : 'Cargando partidos...'} />}
      {error && !cargando && <ErrorMsg mensaje={error} onReintentar={cargar} />}

      {!cargando && !sincronizando && !error && partidos.length === 0 && (
        <div className="text-center py-20 text-gray-500">
          <p className="text-lg">No hay partidos para esta fecha</p>
        </div>
      )}

      {!cargando && !error && Object.entries(porLiga).map(([liga, items]) => (
        <div key={liga} className="mb-8">
          <div className="flex items-center gap-2 mb-3">
            {items[0].partido.liga_logo_url && (
              <img src={items[0].partido.liga_logo_url} alt="" className="w-5 h-5 object-contain" />
            )}
            <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wide">
              {liga} {items[0].partido.liga_pais && `- ${items[0].partido.liga_pais}`}
            </h2>
          </div>
          <div className="grid gap-3">
            {items.map((item) => (
              <PartidoCard
                key={item.partido.api_id}
                partido={item.partido}
                prediccion={item.prediccion}
              />
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}
