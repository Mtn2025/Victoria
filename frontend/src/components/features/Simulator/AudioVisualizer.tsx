import React, { useEffect, useRef } from 'react';

interface AudioVisualizerProps {
    mode: 'wave' | 'bars' | 'orb';
    analyser: AnalyserNode | null;
    outputAnalyser: AnalyserNode | null;
    isAgentSpeaking: boolean;
}

export const AudioVisualizer: React.FC<AudioVisualizerProps> = ({ mode, analyser, outputAnalyser, isAgentSpeaking }) => {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const animationRef = useRef<number>();

    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        if (!ctx) return;

        const draw = () => {
            if (!analyser && !outputAnalyser) {
                // Idle state
                ctx.clearRect(0, 0, canvas.width, canvas.height);
                ctx.fillStyle = '#1e293b'; // slate-800
                ctx.font = '12px monospace';
                ctx.textAlign = 'center';
                ctx.fillText('Waiting for connection...', canvas.width / 2, canvas.height / 2);
                return;
            }

            animationRef.current = requestAnimationFrame(draw);

            // Resize handling
            if (canvas.width !== canvas.offsetWidth) canvas.width = canvas.offsetWidth;
            if (canvas.height !== canvas.offsetHeight) canvas.height = canvas.offsetHeight;

            const WIDTH = canvas.width;
            const HEIGHT = canvas.height;
            const bufferLength = 256; // Standard
            const dataArray = new Uint8Array(bufferLength);

            ctx.clearRect(0, 0, WIDTH, HEIGHT);

            if (mode === 'wave') {
                const activeAnalyser = (isAgentSpeaking && outputAnalyser) ? outputAnalyser : analyser;
                if (activeAnalyser) activeAnalyser.getByteTimeDomainData(dataArray);

                ctx.lineWidth = 2;
                ctx.strokeStyle = isAgentSpeaking ? '#3b82f6' : '#34d399'; // Blue vs Green
                ctx.beginPath();

                const sliceWidth = WIDTH * 1.0 / bufferLength;
                let x = 0;

                for (let i = 0; i < bufferLength; i++) {
                    const v = dataArray[i] / 128.0;
                    const y = v * HEIGHT / 2;
                    if (i === 0) ctx.moveTo(x, y);
                    else ctx.lineTo(x, y);
                    x += sliceWidth;
                }
                ctx.lineTo(WIDTH, HEIGHT / 2);
                ctx.stroke();

            } else if (mode === 'bars') {
                const activeAnalyser = (isAgentSpeaking && outputAnalyser) ? outputAnalyser : analyser;
                if (activeAnalyser) activeAnalyser.getByteFrequencyData(dataArray);

                const barWidth = (WIDTH / bufferLength) * 2.5;
                let barHeight;
                let x = 0;

                for (let i = 0; i < bufferLength; i++) {
                    barHeight = dataArray[i] / 2;
                    // Dynamic color based on height/index
                    const r = barHeight + 25 * (i / bufferLength);
                    const g = isAgentSpeaking ? 50 : 250 * (i / bufferLength);
                    const b = isAgentSpeaking ? 250 : 50;

                    ctx.fillStyle = `rgb(${r},${g},${b})`;
                    ctx.fillRect(x, HEIGHT - barHeight, barWidth, barHeight);
                    x += barWidth + 1;
                }
            } else if (mode === 'orb') {
                const activeAnalyser = (isAgentSpeaking && outputAnalyser) ? outputAnalyser : analyser;
                if (activeAnalyser) activeAnalyser.getByteFrequencyData(dataArray);

                let sum = 0;
                for (let i = 0; i < bufferLength; i++) sum += dataArray[i];
                const avg = sum / bufferLength;

                const centerX = WIDTH / 2;
                const centerY = HEIGHT / 2;
                const radius = 50 + avg; // Dynamic radius

                const gradient = ctx.createRadialGradient(centerX, centerY, radius * 0.2, centerX, centerY, radius);
                if (isAgentSpeaking) {
                    gradient.addColorStop(0, "rgba(59, 130, 246, 0.8)"); // Blue
                    gradient.addColorStop(1, "rgba(29, 78, 216, 0)");
                } else {
                    gradient.addColorStop(0, "rgba(52, 211, 153, 0.8)"); // Green
                    gradient.addColorStop(1, "rgba(5, 150, 105, 0)");
                }

                ctx.beginPath();
                ctx.arc(centerX, centerY, radius, 0, 2 * Math.PI);
                ctx.fillStyle = gradient;
                ctx.fill();
            }
        };

        draw();

        return () => {
            if (animationRef.current) cancelAnimationFrame(animationRef.current);
        };
    }, [mode, analyser, outputAnalyser, isAgentSpeaking]);

    return (
        <canvas ref={canvasRef} className="w-full h-full absolute inset-0 block" />
    );
};
