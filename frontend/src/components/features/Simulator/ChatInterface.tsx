import React, { useEffect, useRef } from 'react';
import { TranscriptMessage } from '@/hooks/useAudioSimulator';

interface ChatInterfaceProps {
    transcripts: TranscriptMessage[];
}

export const ChatInterface: React.FC<ChatInterfaceProps> = ({ transcripts }) => {
    const bottomRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [transcripts]);

    return (
        <div className="flex flex-col h-full bg-slate-900/50 rounded-xl overflow-hidden border border-slate-700/50">
            <div className="px-4 py-2 border-b border-slate-700/50 bg-slate-800/50 flex justify-between items-center bg-slate-900/90 pb-2 border-b mb-2 sticky top-0">
                <span className="text-xs uppercase tracking-wider text-slate-500 font-bold">Transcripción en Vivo</span>
                <span className="text-xs font-mono text-emerald-500/50">{transcripts.length} msgs</span>
            </div>

            <div className="flex-1 overflow-y-auto p-4 space-y-4 font-mono text-xs">
                {transcripts.length === 0 && (
                    <div className="text-center text-slate-600 italic py-10">Esperando audio...</div>
                )}

                {transcripts.map((msg, idx) => (
                    <div
                        key={idx}
                        className={`flex flex-col space-y-1 ${msg.role === 'user' ? 'items-end' :
                                msg.role === 'assistant' ? 'items-start' : 'items-center'
                            }`}
                    >
                        <span className="text-[10px] text-slate-500 flex items-center gap-2">
                            {msg.role === 'user' ? 'Tú' : (msg.role === 'system' ? 'System' : 'Andrea')}
                            <span className="opacity-50">{msg.timestamp}</span>
                        </span>

                        <div className={`px-3 py-2 rounded-lg max-w-[90%] whitespace-pre-wrap ${msg.role === 'user'
                                ? 'bg-blue-600/20 text-blue-200 border border-blue-500/30'
                                : msg.role === 'assistant'
                                    ? 'bg-emerald-600/20 text-emerald-200 border border-emerald-500/30'
                                    : 'bg-slate-700/50 text-slate-400 border border-slate-600 italic'
                            }`}>
                            {msg.text}
                        </div>
                    </div>
                ))}
                <div ref={bottomRef} />
            </div>
        </div>
    );
};
