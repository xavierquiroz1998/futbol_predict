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

  // Filtros
  const [ligas, setLigas] = useState([])
  const [paises, setPaises] = useState([])
  const [filtroLiga, setFiltroLiga] = useState('')
  const [filtroPais, setFiltroPais] = useState('')
  const [mostrarFiltros, setMostrarFiltros] = useState(false)

  // Cargar ligas disponibles
  useEffect(() => {
    partidosApi.obtenerLigas().then(res => {
      setLigas(res.data.ligas || [])
      setPaises(res.data.paises || [])
    }).catch(() => {})
  }, [])

  const cargar = useCallback(async () => {
    setCargando(true)
    setError(null)
    try {
      const hoy = formatFecha(new Date())
      const liga = filtroLiga || undefined
      const pais = filtroPais || undefined
      let res
      if (fecha === hoy) {
        res = await partidosApi.obtenerHoy(liga, pais)
      } else {
        res = await partidosApi.obtenerPorFecha(fecha, true, liga, pais)
      }
      setPartidos(res.data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Error al cargar partidos')
    } finally {
      setCargando(false)
    }
  }, [fecha, filtroLiga, filtroPais])

  const sincronizarInternacionales = async () => {
    setSincronizando(true)
    try {
      await partidosApi.sincronizar(fecha)
      await cargar()
    } catch (err) {
      // Silenciar
    } finally {
      setSincronizando(false)
    }
  }

  useEffect(() => {
    cargar()
  }, [cargar])

  // Ligas filtradas por país seleccionado
  const ligasFiltradas = filtroPais
    ? ligas.filter(l => l.pais === filtroPais)
    : ligas

  const porLiga = partidos.reduce((acc, item) => {
    const liga = item.partido.liga_nombre
    if (!acc[liga]) acc[liga] = []
    acc[liga].push(item)
    return acc
  }, {})

  const limpiarFiltros = () => {
    setFiltroLiga('')
    setFiltroPais('')
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-2xl font-bold text-gray-100">Partidos</h1>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setMostrarFiltros(!mostrarFiltros)}
            className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
              mostrarFiltros || filtroLiga || filtroPais
                ? 'bg-blue-600 text-white'
                : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
            }`}
          >
            Filtros {(filtroLiga || filtroPais) && '•'}
          </button>
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

      {/* Panel de filtros */}
      {mostrarFiltros && (
        <div className="bg-gray-800 border border-gray-700 rounded-xl p-4 mb-4">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-gray-400 uppercase">Filtrar por</h3>
            {(filtroLiga || filtroPais) && (
              <button onClick={limpiarFiltros} className="text-xs text-red-400 hover:text-red-300">
                Limpiar filtros
              </button>
            )}
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div>
              <label className="block text-xs text-gray-500 mb-1">Pais</label>
              <select
                value={filtroPais}
                onChange={(e) => { setFiltroPais(e.target.value); setFiltroLiga(''); }}
                className="w-full px-3 py-2 bg-gray-900 border border-gray-700 text-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-green-500"
              >
                <option value="">Todos los paises</option>
                {paises.map(p => (
                  <option key={p} value={p}>{p}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-1">Liga</label>
              <select
                value={filtroLiga}
                onChange={(e) => setFiltroLiga(e.target.value)}
                className="w-full px-3 py-2 bg-gray-900 border border-gray-700 text-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-green-500"
              >
                <option value="">Todas las ligas</option>
                {ligasFiltradas.map(l => (
                  <option key={l.nombre} value={l.nombre}>{l.nombre}</option>
                ))}
              </select>
            </div>
          </div>
          {/* Chips rápidos de ligas populares */}
          <div className="flex flex-wrap gap-2 mt-3">
            {['Premier League', 'La Liga', 'Serie A', 'Bundesliga', 'Ligue 1'].map(liga => (
              <button
                key={liga}
                onClick={() => setFiltroLiga(filtroLiga === liga ? '' : liga)}
                className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${
                  filtroLiga === liga
                    ? 'bg-green-600 text-white'
                    : 'bg-gray-700 text-gray-400 hover:bg-gray-600'
                }`}
              >
                {liga}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Filtros activos */}
      {(filtroLiga || filtroPais) && !mostrarFiltros && (
        <div className="flex items-center gap-2 mb-4">
          {filtroPais && (
            <span className="px-2 py-1 bg-blue-900/50 text-blue-300 rounded text-xs font-medium flex items-center gap-1">
              {filtroPais}
              <button onClick={() => setFiltroPais('')} className="text-blue-400 hover:text-white ml-1">×</button>
            </span>
          )}
          {filtroLiga && (
            <span className="px-2 py-1 bg-green-900/50 text-green-300 rounded text-xs font-medium flex items-center gap-1">
              {filtroLiga}
              <button onClick={() => setFiltroLiga('')} className="text-green-400 hover:text-white ml-1">×</button>
            </span>
          )}
        </div>
      )}

      {/* Contenido */}
      {(cargando || sincronizando) && <Loading mensaje={sincronizando ? 'Buscando partidos internacionales...' : 'Cargando partidos...'} />}
      {error && !cargando && <ErrorMsg mensaje={error} onReintentar={cargar} />}

      {!cargando && !sincronizando && !error && partidos.length === 0 && (
        <div className="text-center py-20 text-gray-500">
          <p className="text-lg">No hay partidos para esta fecha</p>
          {(filtroLiga || filtroPais) && (
            <button onClick={limpiarFiltros} className="mt-2 text-sm text-green-400 hover:text-green-300">
              Quitar filtros
            </button>
          )}
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
            <span className="text-xs text-gray-600">({items.length})</span>
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
