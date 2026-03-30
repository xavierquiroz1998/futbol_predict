import { Link, useLocation } from 'react-router-dom'

const links = [
  { to: '/', label: 'Partidos' },
  { to: '/historial', label: 'Historial' },
  { to: '/estadisticas', label: 'Estadisticas' },
]

export default function Navbar() {
  const { pathname } = useLocation()

  return (
    <nav className="bg-gray-950 text-white shadow-lg border-b border-gray-800">
      <div className="max-w-6xl mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          <Link to="/" className="text-xl font-bold tracking-tight text-green-400">
            Prediccion Futbol
          </Link>
          <div className="flex gap-1">
            {links.map((link) => (
              <Link
                key={link.to}
                to={link.to}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  pathname === link.to
                    ? 'bg-green-600 text-white'
                    : 'text-gray-400 hover:bg-gray-800 hover:text-white'
                }`}
              >
                {link.label}
              </Link>
            ))}
          </div>
        </div>
      </div>
    </nav>
  )
}
