export default function ErrorMsg({ mensaje, onReintentar }) {
  return (
    <div className="flex flex-col items-center justify-center py-20">
      <div className="bg-red-900/30 border border-red-800 rounded-lg p-6 max-w-md text-center">
        <p className="text-red-400 font-medium">{mensaje}</p>
        {onReintentar && (
          <button
            onClick={onReintentar}
            className="mt-4 px-4 py-2 bg-red-600 text-white rounded-lg text-sm hover:bg-red-700 transition-colors"
          >
            Reintentar
          </button>
        )}
      </div>
    </div>
  )
}
