import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
})

export const partidosApi = {
  obtenerHoy: () => api.get('/partidos/hoy'),
  obtenerPorFecha: (fecha, sincronizar = false) =>
    api.get(`/partidos/fecha/${fecha}`, { params: { sincronizar } }),
  obtenerPorId: (apiId) => api.get(`/partidos/${apiId}`),
  obtenerResultado: (apiId) => api.get(`/partidos/${apiId}/resultado`),
  sincronizar: (fecha) => api.post(`/partidos/sincronizar/${fecha}`, null, { timeout: 60000 }),
}

export const prediccionesApi = {
  crear: (partidoApiId) => api.post(`/predicciones/${partidoApiId}`),
  verificar: (partidoApiId) => api.post(`/predicciones/${partidoApiId}/verificar`),
  historial: (soloVerificadas = false) =>
    api.get('/predicciones/historial', { params: { solo_verificadas: soloVerificadas } }),
  actualizarResultados: () => api.post('/predicciones/actualizar-resultados', null, { timeout: 30000 }),
  estadisticas: () => api.get('/predicciones/estadisticas'),
}

export default api
