import React, { useState } from 'react';
import { Shield } from 'lucide-react';

export const LoginPage = () => {
    const [apiKey, setApiKey] = useState('');
    const [error, setError] = useState('');

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();

        if (!apiKey.trim()) {
            setError('Por favor, ingresa una clave válida.');
            return;
        }

        // Save to localStorage
        localStorage.setItem('api_key', apiKey.trim());

        // Hard reload to re-evaluate the App routing and clear any old state
        window.location.href = '/simulator';
    };

    return (
        <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center p-4">
            <div className="max-w-md w-full bg-slate-900 border border-slate-800 rounded-2xl shadow-xl overflow-hidden p-8">
                <div className="flex flex-col items-center mb-8">
                    <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-blue-600 to-indigo-600 flex items-center justify-center text-white mb-4 shadow-lg shadow-blue-500/20">
                        <Shield size={32} />
                    </div>
                    <h1 className="text-2xl font-bold text-white text-center">Panel de Control SIA</h1>
                    <p className="text-slate-400 mt-2 text-center text-sm">
                        Ingresa tu Clave de Acceso para desbloquear el sistema.
                    </p>
                </div>

                <form onSubmit={handleSubmit} className="space-y-6">
                    <div>
                        <label htmlFor="apiKey" className="block text-sm font-medium text-slate-300 mb-2">
                            Clave de Acceso (API Key)
                        </label>
                        <input
                            id="apiKey"
                            type="password"
                            value={apiKey}
                            onChange={(e) => {
                                setApiKey(e.target.value);
                                setError('');
                            }}
                            className="w-full bg-slate-950 border border-slate-700 rounded-xl px-4 py-3 text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-colors"
                            placeholder="Introduce tu clave secreta..."
                            autoComplete="off"
                        />
                        {error && (
                            <p className="mt-2 text-sm text-red-500">{error}</p>
                        )}
                    </div>

                    <button
                        type="submit"
                        className="w-full bg-blue-600 hover:bg-blue-500 text-white font-medium py-3 px-4 rounded-xl transition-colors duration-200"
                    >
                        Ingresar
                    </button>
                </form>
            </div>
        </div>
    );
};
