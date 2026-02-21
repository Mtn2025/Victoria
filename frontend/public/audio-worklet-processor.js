class PCMProcessor extends AudioWorkletProcessor {
    constructor() {
        super();

        // --- 1. Ring Buffer for Output (TTS) ---
        // Tuned to 100 seconds (24kHz) to handle "Burst Mode" from backend without wrapping.
        // Backend TTS synthesizes a 20-second sentence in ~2 seconds, so we need a
        // massive buffer to receive all the audio immediately without overwriting the start.
        this.bufferSize = 2400000;
        this.outBuffer = new Float32Array(this.bufferSize);
        this.writePtr = 0;
        this.readPtr = 0;
        this.available = 0;

        // --- 2. Input Buffer for Mic (Capture) ---
        this.inBufferSize = 4096;
        this.inBuffer = new Int16Array(this.inBufferSize);
        this.inPtr = 0;

        // Messaging Handlers
        this.port.onmessage = (e) => {
            const data = e.data;
            // Handle raw Int16Array as TTS Data (Legacy/Simple) or Object?
            // Let's support both or just raw array for speed.
            // If it's a typed array, treat as TTS feed.
            if (data && data.length && (data instanceof Int16Array || data instanceof ArrayBuffer)) {
                this.writeOutput(new Int16Array(data.buffer || data));
            } else if (data && data.type === 'feed') {
                this.writeOutput(data.buffer);
            } else if (data && data.type === 'clear') {
                // Clear the TTS audio buffer immediately
                this.available = 0;
                this.writePtr = 0;
                this.readPtr = 0;
            }
        };
    }

    writeOutput(int16Data) {
        // Write incoming TTS Int16 chunks to Ring Buffer (Float32)
        for (let i = 0; i < int16Data.length; i++) {
            const s = int16Data[i];
            const floatSample = s < 0 ? s / 32768 : s / 32767;

            this.outBuffer[this.writePtr] = floatSample;
            this.writePtr = (this.writePtr + 1) % this.bufferSize;
            this.available = Math.min(this.available + 1, this.bufferSize);
        }
    }

    process(inputs, outputs, parameters) {
        // --- 1. CAPTURE (Mic Input) ---
        // Input[0] is the Mic stream
        const input = inputs[0];
        if (input && input.length && input[0] && input[0].length > 0) {
            const channelData = input[0];
            for (let i = 0; i < channelData.length; i++) {
                // Float32 -> Int16
                let s = Math.max(-1, Math.min(1, channelData[i]));
                s = s < 0 ? s * 0x8000 : s * 0x7FFF;

                this.inBuffer[this.inPtr++] = s;

                // Flush Input Buffer
                if (this.inPtr >= this.inBufferSize) {
                    // HALF-DUPLEX ECHO AVOIDANCE
                    // If TTS is playing (available > 0), do NOT send mic data to the backend.
                    // This prevents the speaker's audio from looping back and triggering a false Barge-In.
                    if (this.available <= 0) {
                        this.port.postMessage(this.inBuffer); // Post Int16Array to hook
                    }
                    this.inPtr = 0;
                }
            }
        } else {
            // DIAG: inputs[0] is empty — mic not connected to this worklet node
            // Log once every ~5s at 24kHz/128 frames to avoid flooding
            this._emptyInputCount = (this._emptyInputCount || 0) + 1;
            if (this._emptyInputCount % 1000 === 1) {
                this.port.postMessage({ type: 'debug', msg: 'empty_input', count: this._emptyInputCount });
            }
        }

        // --- 2. RENDER (TTS Output) ---
        // Output[0] is the Speaker
        const output = outputs[0];
        if (output && output.length) {
            const channel = output[0];
            for (let i = 0; i < channel.length; i++) {
                if (this.available > 0) {
                    const sample = this.outBuffer[this.readPtr];
                    channel[i] = sample;
                    this.readPtr = (this.readPtr + 1) % this.bufferSize;
                    this.available--;
                } else {
                    channel[i] = 0; // Silence
                }
            }
        }

        return true; // Keep processor alive
    }
}

registerProcessor('pcm-processor', PCMProcessor);
