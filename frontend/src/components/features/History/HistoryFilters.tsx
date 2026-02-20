import React from 'react'

interface HistoryFiltersProps {
    activeFilter: string
    onFilterChange: (filter: string) => void
}

export const HistoryFilters: React.FC<HistoryFiltersProps> = ({ activeFilter, onFilterChange }) => {
    const filters = [
        { id: 'all', label: 'Todos', color: 'bg-blue-600' },
        { id: 'browser', label: 'Simulador', color: 'bg-blue-600' },
        { id: 'twilio', label: 'Twilio', color: 'bg-red-600' },
        { id: 'telnyx', label: 'Telnyx', color: 'bg-emerald-600' }
    ]

    return (
        <div className="flex space-x-2 bg-slate-900/50 rounded-lg p-1 border border-slate-700 w-fit">
            {filters.map((filter) => (
                <button
                    key={filter.id}
                    type="button"
                    onClick={() => onFilterChange(filter.id)}
                    className={`px-3 py-1 rounded text-xs font-bold transition-all ${activeFilter === filter.id
                        ? `${filter.color} text-white`
                        : 'text-slate-400 hover:text-white'
                        }`}
                >
                    {filter.label}
                </button>
            ))}
        </div>
    )
}
