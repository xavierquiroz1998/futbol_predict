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

export default function PartidoCard({ partido, prediccion }) {
  const p = partido
  const pred = prediccion

  return (
    <Link
      to={`/partido/${p.api_id}`}
      className="block bg-gray-800 rounded-xl shadow-sm border border-gray-700 p-4 hover:border-gray-600 hover:shadow-md transition-all"
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs text-gray-400 font-medium">{p.liga_nombre}</span>
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-500">{formatHora(p.fecha)}</span>
          <EstadoBadge estado={p.estado} finalizado={p.finalizado} />
        </div>
      </div>

      {/* Equipos, marcador y predicción */}
      <div className="flex items-start justify-between gap-2">
        {/* Equipo local */}
        <div className="flex-1 text-center">
          <div className="flex items-center justify-center gap-2 mb-1">
            <span className="font-semibold text-gray-200 text-sm">{p.equipo_local_nombre}</span>
            {p.equipo_local_logo && (
              <img src={p.equipo_local_logo} alt="" className="w-8 h-8 object-contain" />
            )}
          </div>
          {pred && pred.prediccion === 'local' && (
            <div className="mt-1">
              <span className="px-2 py-0.5 text-xs font-bold rounded bg-green-900/50 text-green-300 border border-green-700">
                Gana {(pred.prob_local * 100).toFixed(0)}%
              </span>
            </div>
          )}
          {pred && pred.prediccion !== 'local' && (
            <p className="text-xs text-gray-600 mt-1">{(pred.prob_local * 100).toFixed(0)}%</p>
          )}
        </div>

        {/* Centro: marcador o vs + empate */}
        <div className="flex-shrink-0 text-center min-w-[60px]">
          {p.finalizado || p.goles_local !== null ? (
            <span className="text-2xl font-bold text-gray-100">
              {p.goles_local} - {p.goles_visitante}
            </span>
          ) : (
            <span className="text-lg font-medium text-gray-500">vs</span>
          )}
          {pred && pred.prediccion === 'empate' && (
            <div className="mt-1">
              <span className="px-2 py-0.5 text-xs font-bold rounded bg-yellow-900/50 text-yellow-300 border border-yellow-700">
                Empate {(pred.prob_empate * 100).toFixed(0)}%
              </span>
            </div>
          )}
          {pred && pred.prediccion !== 'empate' && (
            <p className="text-xs text-gray-600 mt-1">{(pred.prob_empate * 100).toFixed(0)}%</p>
          )}
        </div>

        {/* Equipo visitante */}
        <div className="flex-1 text-center">
          <div className="flex items-center justify-center gap-2 mb-1">
            {p.equipo_visitante_logo && (
              <img src={p.equipo_visitante_logo} alt="" className="w-8 h-8 object-contain" />
            )}
            <span className="font-semibold text-gray-200 text-sm">{p.equipo_visitante_nombre}</span>
          </div>
          {pred && pred.prediccion === 'visitante' && (
            <div className="mt-1">
              <span className="px-2 py-0.5 text-xs font-bold rounded bg-blue-900/50 text-blue-300 border border-blue-700">
                Gana {(pred.prob_visitante * 100).toFixed(0)}%
              </span>
            </div>
          )}
          {pred && pred.prediccion !== 'visitante' && (
            <p className="text-xs text-gray-600 mt-1">{(pred.prob_visitante * 100).toFixed(0)}%</p>
          )}
        </div>
      </div>

      {/* Verificación */}
      {pred && pred.acertada !== null && (
        <div className="mt-2 text-center">
          <span className={`px-2 py-1 text-xs font-bold rounded ${
            pred.acertada ? 'bg-green-500 text-white' : 'bg-red-500 text-white'
          }`}>
            {pred.acertada ? 'Acerto' : 'Fallo'}
          </span>
        </div>
      )}
    </Link>
  )
}
