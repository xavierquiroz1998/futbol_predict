export default function Loading({ mensaje = 'Cargando...' }) {
  return (
    <div className="flex flex-col items-center justify-center py-20">
      <div className="w-10 h-10 border-4 border-green-500 border-t-transparent rounded-full animate-spin" />
      <p className="mt-4 text-gray-400 text-sm">{mensaje}</p>
    </div>
  )
}
