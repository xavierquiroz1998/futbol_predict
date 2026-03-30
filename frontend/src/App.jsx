import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Navbar from './components/Navbar'
import Partidos from './pages/Partidos'
import DetallePartido from './pages/DetallePartido'
import Historial from './pages/Historial'
import Estadisticas from './pages/Estadisticas'

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-900 text-gray-100">
        <Navbar />
        <Routes>
          <Route path="/" element={<Partidos />} />
          <Route path="/partido/:apiId" element={<DetallePartido />} />
          <Route path="/historial" element={<Historial />} />
          <Route path="/estadisticas" element={<Estadisticas />} />
        </Routes>
      </div>
    </BrowserRouter>
  )
}
