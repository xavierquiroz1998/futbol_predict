import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { partidosApi, prediccionesApi } from '../services/api'
import Loading from '../components/Loading'
import ErrorMsg from '../components/ErrorMsg'

function BarraProbabilidad({ label, valor, color }) {
  const pct = (valor * 100).toFixed(1)
  return (
    <div className="mb-3">
      <div className="flex justify-between text-sm mb-1">
        <span className="text-gray-400">{label}</span>
        <span className="font-semibold text-gray-200">{pct}%</span>
      </div>
      <div className="w-full bg-gray-700 rounded-full h-3">
        <div className={`h-3 rounded-full transition-all duration-500 ${color}`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  )
}

function FormaReciente({ texto }) {
  return (
    <div className="flex gap-1">
      {texto.split('').map((c, i) => (
        <span key={i} className={`w-6 h-6 rounded text-xs font-bold flex items-center justify-center ${
          c === 'V' ? 'bg-green-600 text-white' :
          c === 'E' ? 'bg-yellow-600 text-white' :
          'bg-red-600 text-white'
        }`}>{c}</span>
      ))}
    </div>
  )
}

function StatComparison({ label, localVal, visitanteVal, format = 'number', invertBetter = false }) {
  const lv = typeof localVal === 'number' ? localVal : 0
  const vv = typeof visitanteVal === 'number' ? visitanteVal : 0
  const localBetter = invertBetter ? lv < vv : lv > vv
  const visitanteBetter = invertBetter ? vv < lv : vv > lv

  const formatVal = (v) => {
    if (format === 'pct') return `${v}%`
    if (format === 'decimal') return v.toFixed(2)
    return v
  }

  return (
    <div className="flex items-center justify-between py-2 border-b border-gray-700/50">
      <span className={`text-sm font-semibold w-16 text-right ${localBetter ? 'text-green-400' : 'text-gray-400'}`}>
        {formatVal(localVal)}
      </span>
      <span className="text-xs text-gray-500 flex-1 text-center">{label}</span>
      <span className={`text-sm font-semibold w-16 text-left ${visitanteBetter ? 'text-green-400' : 'text-gray-400'}`}>
        {formatVal(visitanteVal)}
      </span>
    </div>
  )
}

function getNivelConfianza(prob) {
  if (prob >= 0.65) return { texto: 'Alta', color: 'text-green-400', bgColor: 'bg-green-900/30 border-green-700', icono: '▲' }
  if (prob >= 0.45) return { texto: 'Media', color: 'text-yellow-400', bgColor: 'bg-yellow-900/30 border-yellow-700', icono: '■' }
  return { texto: 'Baja', color: 'text-red-400', bgColor: 'bg-red-900/30 border-red-700', icono: '▼' }
}

function getAnalisis(pred, ctx, equipoLocal, equipoVisitante) {
  const probMax = Math.max(pred.prob_local, pred.prob_empate, pred.prob_visitante)
  const nivel = getNivelConfianza(probMax)
  const sorted = [pred.prob_local, pred.prob_empate, pred.prob_visitante].sort((a, b) => b - a)
  const diff = sorted[0] - sorted[1]

  let partes = []

  if (ctx) {
    const l = ctx.local
    const v = ctx.visitante

    // Forma reciente
    if (l.victorias_5 >= 4) partes.push(`${equipoLocal} viene en gran forma con ${l.victorias_5} victorias en sus ultimos 5 partidos.`)
    else if (l.victorias_5 <= 1 && l.derrotas_5 >= 3) partes.push(`${equipoLocal} atraviesa un mal momento con ${l.derrotas_5} derrotas en sus ultimos 5.`)

    if (v.victorias_5 >= 4) partes.push(`${equipoVisitante} llega con ${v.victorias_5} victorias consecutivas en sus ultimos 5.`)
    else if (v.victorias_5 <= 1 && v.derrotas_5 >= 3) partes.push(`${equipoVisitante} no pasa por su mejor momento con ${v.derrotas_5} derrotas recientes.`)

    // Rachas
    if (l.racha_victorias >= 3) partes.push(`Racha de ${l.racha_victorias} victorias seguidas para ${equipoLocal}.`)
    if (v.racha_victorias >= 3) partes.push(`${equipoVisitante} acumula ${v.racha_victorias} victorias al hilo.`)
    if (l.racha_derrotas >= 3) partes.push(`${equipoLocal} viene de ${l.racha_derrotas} derrotas consecutivas.`)
    if (v.racha_derrotas >= 3) partes.push(`${equipoVisitante} arrastra ${v.racha_derrotas} derrotas seguidas.`)

    // Rendimiento local/visitante
    if (l.win_rate_condicion >= 70) partes.push(`Como local, ${equipoLocal} gana el ${l.win_rate_condicion}% de sus partidos.`)
    if (v.win_rate_condicion >= 40) partes.push(`${equipoVisitante} gana el ${v.win_rate_condicion}% de sus partidos fuera de casa.`)
    else if (v.win_rate_condicion <= 15) partes.push(`${equipoVisitante} solo gana el ${v.win_rate_condicion}% como visitante.`)

    // Goles
    if (l.over_2_5_pct >= 70) partes.push(`El ${l.over_2_5_pct}% de los partidos de ${equipoLocal} tienen mas de 2.5 goles.`)
    if (l.btts_pct >= 70 && v.btts_pct >= 70) partes.push(`Ambos equipos tienden a anotar — BTTS en ${l.btts_pct}% (local) y ${v.btts_pct}% (visitante).`)

    // H2H
    if (ctx.h2h_total > 0) {
      if (ctx.h2h_wins_local > ctx.h2h_wins_visitante) {
        partes.push(`En ${ctx.h2h_total} enfrentamientos directos, ${equipoLocal} domina con ${ctx.h2h_wins_local} victorias vs ${ctx.h2h_wins_visitante}.`)
      } else if (ctx.h2h_wins_visitante > ctx.h2h_wins_local) {
        partes.push(`Historial favorable para ${equipoVisitante}: ${ctx.h2h_wins_visitante} victorias vs ${ctx.h2h_wins_local} en ${ctx.h2h_total} encuentros.`)
      } else {
        partes.push(`Historial parejo: ${ctx.h2h_wins_local}-${ctx.h2h_empates}-${ctx.h2h_wins_visitante} en ${ctx.h2h_total} enfrentamientos.`)
      }
    }

    // Clean sheets
    if (l.clean_sheets_5 >= 3) partes.push(`${equipoLocal} mantuvo porteria a cero en ${l.clean_sheets_5} de sus ultimos 5 partidos.`)
    if (v.clean_sheets_5 >= 3) partes.push(`Defensa solida de ${equipoVisitante}: ${v.clean_sheets_5} clean sheets en 5 partidos.`)
  }

  // Conclusión basada en predicción
  if (pred.prediccion === 'local') {
    if (nivel.texto === 'Alta') partes.push(`El modelo predice con alta confianza que ${equipoLocal} ganara este partido.`)
    else if (nivel.texto === 'Media') partes.push(`${equipoLocal} es favorito pero el resultado no es seguro.`)
    else partes.push(`${equipoLocal} tiene una ligera ventaja. Partido abierto.`)
  } else if (pred.prediccion === 'visitante') {
    if (nivel.texto === 'Alta') partes.push(`${equipoVisitante} es claro favorito segun el analisis.`)
    else partes.push(`${equipoVisitante} tiene ventaja pero jugar fuera agrega incertidumbre.`)
  } else {
    partes.push(`Los equipos estan muy igualados. El empate es el resultado mas probable.`)
  }

  if (partes.length === 0) {
    partes.push('No hay suficientes datos historicos para generar un analisis detallado.')
  }

  return { nivel, descripcion: partes.join(' '), diff }
}

export default function DetallePartido() {
  const { apiId } = useParams()
  const [data, setData] = useState(null)
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState(null)
  const [prediciendo, setPrediciendo] = useState(false)
  const [verificando, setVerificando] = useState(false)

  const cargar = async () => {
    setCargando(true)
    setError(null)
    try {
      const res = await partidosApi.obtenerPorId(apiId)
      setData(res.data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Error al cargar partido')
    } finally {
      setCargando(false)
    }
  }

  useEffect(() => { cargar() }, [apiId])

  const generarPrediccion = async () => {
    setPrediciendo(true)
    setError(null)
    try {
      const res = await prediccionesApi.crear(apiId)
      setData((prev) => ({ ...prev, prediccion: res.data }))
    } catch (err) {
      setError(err.response?.data?.detail || 'Error al generar prediccion')
    } finally {
      setPrediciendo(false)
    }
  }

  const verificarPrediccion = async () => {
    setVerificando(true)
    try {
      const res = await prediccionesApi.verificar(apiId)
      setData((prev) => ({ ...prev, prediccion: res.data }))
    } catch (err) {
      setError(err.response?.data?.detail || 'Error al verificar')
    } finally {
      setVerificando(false)
    }
  }

  if (cargando) return <Loading mensaje="Cargando partido..." />
  if (error && !data) return <ErrorMsg mensaje={error} onReintentar={cargar} />
  if (!data) return null

  const { partido: p, prediccion: pred, contexto: ctx, cuotas } = data
  const fecha = new Date(p.fecha)
  const analisis = pred ? getAnalisis(pred, ctx, p.equipo_local_nombre, p.equipo_visitante_nombre) : null

  return (
    <div className="max-w-2xl mx-auto px-4 py-6">
      <Link to="/" className="text-green-400 hover:text-green-300 text-sm font-medium mb-4 inline-block">
        &larr; Volver a partidos
      </Link>

      <div className="bg-gray-800 rounded-xl shadow-lg border border-gray-700 overflow-hidden">
        {/* Header */}
        <div className="px-6 py-3 border-b border-gray-700 bg-gray-900/50">
          <div className="flex items-center gap-2">
            {p.liga_logo_url && <img src={p.liga_logo_url} alt="" className="w-5 h-5 object-contain" />}
            <span className="text-sm font-medium text-gray-400">{p.liga_nombre}</span>
            <span className="text-xs text-gray-500 ml-auto">
              {fecha.toLocaleDateString('es', { weekday: 'long', day: 'numeric', month: 'long' })}
              {' - '}
              {fecha.toLocaleTimeString('es', { hour: '2-digit', minute: '2-digit' })}
            </span>
          </div>
        </div>

        {/* Equipos */}
        <div className="px-6 py-8">
          <div className="flex items-center justify-between gap-6">
            <div className="flex-1 text-center">
              {p.equipo_local_logo && <img src={p.equipo_local_logo} alt="" className="w-16 h-16 object-contain mx-auto mb-2" />}
              <p className="font-bold text-gray-100">{p.equipo_local_nombre}</p>
              <p className="text-xs text-gray-500 mt-1">Local</p>
              {ctx && <div className="mt-2 flex justify-center"><FormaReciente texto={ctx.local.ultimos_5} /></div>}
            </div>
            <div className="flex-shrink-0 text-center">
              {p.finalizado || p.goles_local !== null ? (
                <p className="text-4xl font-black text-gray-100">{p.goles_local} - {p.goles_visitante}</p>
              ) : (
                <p className="text-2xl font-medium text-gray-500">vs</p>
              )}
              <p className={`text-xs font-semibold mt-2 ${p.finalizado ? 'text-gray-500' : 'text-green-400'}`}>
                {p.finalizado ? 'Finalizado' : p.estado === 'NS' ? 'Por jugar' : 'En vivo'}
              </p>
            </div>
            <div className="flex-1 text-center">
              {p.equipo_visitante_logo && <img src={p.equipo_visitante_logo} alt="" className="w-16 h-16 object-contain mx-auto mb-2" />}
              <p className="font-bold text-gray-100">{p.equipo_visitante_nombre}</p>
              <p className="text-xs text-gray-500 mt-1">Visitante</p>
              {ctx && <div className="mt-2 flex justify-center"><FormaReciente texto={ctx.visitante.ultimos_5} /></div>}
            </div>
          </div>
        </div>

        {/* Estadísticas comparativas */}
        {ctx && (
          <div className="px-6 py-5 border-t border-gray-700">
            <h3 className="text-sm font-semibold text-gray-400 mb-3 uppercase tracking-wide">Estadisticas</h3>
            <StatComparison label="Victorias (ult. 5)" localVal={ctx.local.victorias_5} visitanteVal={ctx.visitante.victorias_5} />
            <StatComparison label="Derrotas (ult. 5)" localVal={ctx.local.derrotas_5} visitanteVal={ctx.visitante.derrotas_5} invertBetter />
            <StatComparison label="Goles a favor (prom)" localVal={ctx.local.goles_favor_prom} visitanteVal={ctx.visitante.goles_favor_prom} format="decimal" />
            <StatComparison label="Goles en contra (prom)" localVal={ctx.local.goles_contra_prom} visitanteVal={ctx.visitante.goles_contra_prom} format="decimal" invertBetter />
            <StatComparison label="Clean sheets" localVal={ctx.local.clean_sheets_5} visitanteVal={ctx.visitante.clean_sheets_5} />
            <StatComparison label="Racha victorias" localVal={ctx.local.racha_victorias} visitanteVal={ctx.visitante.racha_victorias} />
            <StatComparison label="Racha sin perder" localVal={ctx.local.racha_sin_perder} visitanteVal={ctx.visitante.racha_sin_perder} />
            <StatComparison label="Win rate (L/V)" localVal={ctx.local.win_rate_condicion} visitanteVal={ctx.visitante.win_rate_condicion} format="pct" />
            <StatComparison label="Over 2.5" localVal={ctx.local.over_2_5_pct} visitanteVal={ctx.visitante.over_2_5_pct} format="pct" />
            <StatComparison label="Ambos anotan" localVal={ctx.local.btts_pct} visitanteVal={ctx.visitante.btts_pct} format="pct" />

            {/* H2H */}
            {ctx.h2h_total > 0 && (
              <div className="mt-4 p-3 bg-gray-900/50 rounded-lg border border-gray-700">
                <p className="text-xs font-semibold text-gray-400 uppercase mb-2">Enfrentamientos directos ({ctx.h2h_total})</p>
                <div className="flex justify-center gap-6 text-sm mb-2">
                  <span className="text-green-400 font-bold">{ctx.h2h_wins_local} V</span>
                  <span className="text-yellow-400 font-bold">{ctx.h2h_empates} E</span>
                  <span className="text-blue-400 font-bold">{ctx.h2h_wins_visitante} V</span>
                </div>
                <p className="text-xs text-gray-500 text-center">Promedio: {ctx.h2h_goles_prom} goles/partido</p>
                {ctx.h2h_ultimos.length > 0 && (
                  <div className="mt-2 space-y-1">
                    {ctx.h2h_ultimos.map((r, i) => (
                      <p key={i} className="text-xs text-gray-500 text-center">{r}</p>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* Cuotas de apuestas */}
        {cuotas && cuotas.media && (
          <div className="px-6 py-5 border-t border-gray-700">
            <h3 className="text-sm font-semibold text-gray-400 mb-3 uppercase tracking-wide">
              {cuotas.estimadas ? 'Cuotas estimadas' : 'Cuotas de apuestas'}
              {cuotas.total_casas > 0 && <span className="text-xs text-gray-600 normal-case"> ({cuotas.total_casas} casas)</span>}
              {cuotas.estimadas && <span className="text-xs text-yellow-500 normal-case ml-2">basadas en el modelo ML</span>}
            </h3>

            {cuotas.media && (
              <div className="grid grid-cols-3 gap-3 mb-4">
                <div className="bg-green-900/20 border border-green-800/50 rounded-lg p-3 text-center">
                  <p className="text-xs text-gray-400">{p.equipo_local_nombre}</p>
                  <p className="text-2xl font-black text-green-400">{cuotas.media.local}</p>
                  <p className="text-xs text-gray-500">{cuotas.media.prob_local}%</p>
                </div>
                <div className="bg-yellow-900/20 border border-yellow-800/50 rounded-lg p-3 text-center">
                  <p className="text-xs text-gray-400">Empate</p>
                  <p className="text-2xl font-black text-yellow-400">{cuotas.media.empate}</p>
                  <p className="text-xs text-gray-500">{cuotas.media.prob_empate}%</p>
                </div>
                <div className="bg-blue-900/20 border border-blue-800/50 rounded-lg p-3 text-center">
                  <p className="text-xs text-gray-400">{p.equipo_visitante_nombre}</p>
                  <p className="text-2xl font-black text-blue-400">{cuotas.media.visitante}</p>
                  <p className="text-xs text-gray-500">{cuotas.media.prob_visitante}%</p>
                </div>
              </div>
            )}

            {cuotas.media?.over && (
              <div className="grid grid-cols-2 gap-3 mb-4">
                <div className="bg-gray-700/30 border border-gray-600 rounded-lg p-2 text-center">
                  <p className="text-xs text-gray-400">Over 2.5</p>
                  <p className="text-lg font-bold text-gray-200">{cuotas.media.over}</p>
                </div>
                <div className="bg-gray-700/30 border border-gray-600 rounded-lg p-2 text-center">
                  <p className="text-xs text-gray-400">Under 2.5</p>
                  <p className="text-lg font-bold text-gray-200">{cuotas.media.under}</p>
                </div>
              </div>
            )}

            <details className="group">
              <summary className="text-xs text-gray-500 cursor-pointer hover:text-gray-300 transition-colors">
                Ver detalle por casa de apuestas
              </summary>
              <div className="mt-2 bg-gray-900/50 rounded-lg border border-gray-700 overflow-hidden">
                <table className="w-full text-xs">
                  <thead className="bg-gray-900/80">
                    <tr>
                      <th className="px-3 py-2 text-left text-gray-500">Casa</th>
                      <th className="px-3 py-2 text-center text-gray-500">1</th>
                      <th className="px-3 py-2 text-center text-gray-500">X</th>
                      <th className="px-3 py-2 text-center text-gray-500">2</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-800">
                    {cuotas.casas.map((c, i) => (
                      <tr key={i} className="hover:bg-gray-800/50">
                        <td className="px-3 py-1.5 text-gray-400">{c.casa}</td>
                        <td className="px-3 py-1.5 text-center text-gray-300">{c.local}</td>
                        <td className="px-3 py-1.5 text-center text-gray-300">{c.empate}</td>
                        <td className="px-3 py-1.5 text-center text-gray-300">{c.visitante}</td>
                      </tr>
                    ))}
                    <tr className="bg-gray-800/80 font-semibold">
                      <td className="px-3 py-1.5 text-gray-300">Media</td>
                      <td className="px-3 py-1.5 text-center text-green-400">{cuotas.media?.local}</td>
                      <td className="px-3 py-1.5 text-center text-yellow-400">{cuotas.media?.empate}</td>
                      <td className="px-3 py-1.5 text-center text-blue-400">{cuotas.media?.visitante}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </details>
          </div>
        )}

        {/* Prediccion */}
        <div className="px-6 py-6 border-t border-gray-700 bg-gray-900/50">
          <h3 className="text-sm font-semibold text-gray-400 mb-4 uppercase tracking-wide">Prediccion</h3>

          {error && (
            <div className="mb-4 p-3 bg-red-900/30 border border-red-800 rounded-lg text-red-400 text-sm">{error}</div>
          )}

          {pred ? (
            <div>
              <div className="flex items-center gap-3 mb-4 flex-wrap">
                <span className={`px-3 py-1 rounded-full text-sm font-bold ${
                  pred.prediccion === 'local' ? 'bg-green-900/50 text-green-300' :
                  pred.prediccion === 'empate' ? 'bg-yellow-900/50 text-yellow-300' :
                  'bg-blue-900/50 text-blue-300'
                }`}>
                  {pred.prediccion === 'local' ? `Gana ${p.equipo_local_nombre}` :
                   pred.prediccion === 'empate' ? 'Empate' :
                   `Gana ${p.equipo_visitante_nombre}`}
                </span>
                {analisis && (
                  <span className={`px-3 py-1 rounded-full text-sm font-bold ${analisis.nivel.color} ${analisis.nivel.bgColor} border`}>
                    {analisis.nivel.icono} Confianza {analisis.nivel.texto}
                  </span>
                )}
                {pred.acertada !== null && (
                  <span className={`px-3 py-1 rounded-full text-sm font-bold ${pred.acertada ? 'bg-green-500 text-white' : 'bg-red-500 text-white'}`}>
                    {pred.acertada ? 'Acerto' : 'Fallo'}
                  </span>
                )}
              </div>

              {analisis && (
                <div className={`p-4 rounded-lg border mb-4 ${analisis.nivel.bgColor}`}>
                  <p className="text-sm text-gray-300 leading-relaxed">{analisis.descripcion}</p>
                  <div className="mt-2 flex items-center gap-4 text-xs text-gray-500">
                    <span>Probabilidad max: <strong className={analisis.nivel.color}>{(Math.max(pred.prob_local, pred.prob_empate, pred.prob_visitante) * 100).toFixed(1)}%</strong></span>
                    <span>Diferencia vs 2do: <strong className="text-gray-400">{(analisis.diff * 100).toFixed(1)}%</strong></span>
                  </div>
                </div>
              )}

              <BarraProbabilidad label={p.equipo_local_nombre} valor={pred.prob_local} color="bg-green-500" />
              <BarraProbabilidad label="Empate" valor={pred.prob_empate} color="bg-yellow-500" />
              <BarraProbabilidad label={p.equipo_visitante_nombre} valor={pred.prob_visitante} color="bg-blue-500" />

              {/* Predicciones adicionales */}
              {(pred.marcador_pred || pred.over_under_pred || pred.btts_pred !== null) && (
                <div className="mt-4 grid grid-cols-3 gap-3">
                  {pred.marcador_pred && (
                    <div className="bg-gray-700/50 rounded-lg p-3 text-center border border-gray-600">
                      <p className="text-xs text-gray-400 mb-1">Marcador</p>
                      <p className="text-2xl font-black text-white">{pred.marcador_pred}</p>
                    </div>
                  )}
                  {pred.over_under_pred && (
                    <div className="bg-gray-700/50 rounded-lg p-3 text-center border border-gray-600">
                      <p className="text-xs text-gray-400 mb-1">Over/Under 2.5</p>
                      <p className={`text-lg font-bold ${pred.over_under_pred === 'over' ? 'text-green-400' : 'text-red-400'}`}>
                        {pred.over_under_pred === 'over' ? 'Over' : 'Under'}
                      </p>
                      <p className="text-xs text-gray-500 mt-1">{(pred.prob_over * 100).toFixed(0)}% / {(pred.prob_under * 100).toFixed(0)}%</p>
                    </div>
                  )}
                  {pred.btts_pred !== null && (
                    <div className="bg-gray-700/50 rounded-lg p-3 text-center border border-gray-600">
                      <p className="text-xs text-gray-400 mb-1">Ambos anotan</p>
                      <p className={`text-lg font-bold ${pred.btts_pred ? 'text-green-400' : 'text-red-400'}`}>
                        {pred.btts_pred ? 'Si' : 'No'}
                      </p>
                      <p className="text-xs text-gray-500 mt-1">{(pred.prob_btts * 100).toFixed(0)}%</p>
                    </div>
                  )}
                </div>
              )}

              {p.finalizado && pred.acertada === null && (
                <button onClick={verificarPrediccion} disabled={verificando}
                  className="mt-4 w-full py-2 bg-purple-600 text-white rounded-lg text-sm font-medium hover:bg-purple-700 disabled:opacity-50 transition-colors">
                  {verificando ? 'Verificando...' : 'Verificar prediccion'}
                </button>
              )}
            </div>
          ) : (
            <div className="text-center">
              {p.finalizado ? (
                <p className="text-gray-500 text-sm">No se genero prediccion para este partido</p>
              ) : (
                <button onClick={generarPrediccion} disabled={prediciendo}
                  className="w-full py-3 bg-green-600 text-white rounded-lg font-medium hover:bg-green-700 disabled:opacity-50 transition-colors">
                  {prediciendo ? 'Generando prediccion...' : 'Generar prediccion'}
                </button>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
