import { Link } from 'react-router-dom'

function formatHora(fechaStr) {
  const fecha = new Date(fechaStr)
  return fecha.toLocaleTimeString('es', { hour: '2-digit', minute: '2-digit' })
}

function EstadoBadge({ estado, finalizado }) {
  if (finalizado) {
    return <span className="px-2 py-1 text-xs font-semibold rounded bg-gray-600 text-gray-200">FT</span>
  }
  if (estado === 'NS') {
    return <span className="px-2 py-1 text-xs font-semibold rounded bg-blue-900 text-blue-300">Pendiente</span>
  }
  return <span className="px-2 py-1 text-xs font-semibold rounded bg-yellow-900 text-yellow-300">En vivo</span>
}

function PrediccionBadge({ prediccion }) {
  if (!prediccion) return null

  const colorMap = {
    local: 'bg-green-900/50 text-green-300 border-green-700',
    empate: 'bg-yellow-900/50 text-yellow-300 border-yellow-700',
    visitante: 'bg-blue-900/50 text-blue-300 border-blue-700',
  }

  const labelMap = {
    local: 'Gana Local',
    empate: 'Empate',
    visitante: 'Gana Visitante',
  }

  return (
    <div className="mt-3 pt-3 border-t border-gray-700">
      <div className="flex items-center justify-between">
        <span className={`px-2 py-1 text-xs font-semibold rounded border ${colorMap[prediccion.prediccion]}`}>
          {labelMap[prediccion.prediccion]}
        </span>
        {prediccion.acertada !== null && (
          <span className={`px-2 py-1 text-xs font-bold rounded ${
            prediccion.acertada ? 'bg-green-500 text-white' : 'bg-red-500 text-white'
          }`}>
            {prediccion.acertada ? 'Acerto' : 'Fallo'}
          </span>
        )}
      </div>
      <div className="flex justify-between mt-2 text-xs text-gray-500">
        <span>L: {(prediccion.prob_local * 100).toFixed(0)}%</span>
        <span>E: {(prediccion.prob_empate * 100).toFixed(0)}%</span>
        <span>V: {(prediccion.prob_visitante * 100).toFixed(0)}%</span>
      </div>
    </div>
  )
}

export default function PartidoCard({ partido, prediccion }) {
  const p = partido

  return (
    <Link
      to={`/partido/${p.api_id}`}
      className="block bg-gray-800 rounded-xl shadow-sm border border-gray-700 p-4 hover:border-gray-600 hover:shadow-md transition-all"
    >
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs text-gray-400 font-medium">{p.liga_nombre}</span>
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-500">{formatHora(p.fecha)}</span>
          <EstadoBadge estado={p.estado} finalizado={p.finalizado} />
        </div>
      </div>

      <div className="flex items-center justify-between gap-4">
        <div className="flex-1 text-right">
          <div className="flex items-center justify-end gap-2">
            <span className="font-semibold text-gray-200 text-sm">{p.equipo_local_nombre}</span>
            {p.equipo_local_logo && (
              <img src={p.equipo_local_logo} alt="" className="w-8 h-8 object-contain" />
            )}
          </div>
        </div>

        <div className="flex-shrink-0 text-center min-w-[60px]">
          {p.finalizado || p.goles_local !== null ? (
            <span className="text-2xl font-bold text-gray-100">
              {p.goles_local} - {p.goles_visitante}
            </span>
          ) : (
            <span className="text-lg font-medium text-gray-500">vs</span>
          )}
        </div>

        <div className="flex-1 text-left">
          <div className="flex items-center gap-2">
            {p.equipo_visitante_logo && (
              <img src={p.equipo_visitante_logo} alt="" className="w-8 h-8 object-contain" />
            )}
            <span className="font-semibold text-gray-200 text-sm">{p.equipo_visitante_nombre}</span>
          </div>
        </div>
      </div>

      <PrediccionBadge prediccion={prediccion} />
    </Link>
  )
}
