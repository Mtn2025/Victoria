"""
Silero VAD Adapter (Infrastructure Layer).
Wraps ONNX runtime execution for VAD.
"""
import logging
from pathlib import Path
import numpy as np

try:
    import onnxruntime
except ImportError:
    logging.error("onnxruntime not found. Please install it to use Silero VAD.")
    onnxruntime = None

logger = logging.getLogger(__name__)

class SileroVadAdapter:
    """
    Adapter for Silero VAD ONNX model.
    """
    def __init__(self, model_path: str | Path | None = None):
        if not onnxruntime:
            raise ImportError("onnxruntime is required for Silero VAD")

        if not model_path:
            # Default to adjacent 'data' folder
            model_path = Path(__file__).parent / "data" / "silero_vad.onnx"
            
        if not Path(model_path).exists():
             raise FileNotFoundError(f"Silero VAD model not found at: {model_path}")

        opts = onnxruntime.SessionOptions()
        opts.inter_op_num_threads = 1
        opts.intra_op_num_threads = 1

        self.session = onnxruntime.InferenceSession(
            str(model_path), 
            providers=["CPUExecutionProvider"], 
            sess_options=opts
        )
        
        self.reset_states()
        self.sample_rates = [8000, 16000]

    def reset_states(self, batch_size=1):
        self._state = np.zeros((2, batch_size, 128), dtype="float32")
        self._context = np.zeros((batch_size, 0), dtype="float32")
        self._last_sr = 0
        self._last_batch_size = 0

    def _validate_input(self, x, sr: int):
        if np.ndim(x) == 1:
            x = np.expand_dims(x, 0)
        if np.ndim(x) > 2:
            raise ValueError(f"Too many dimensions for input audio chunk {x.ndim}")

        if sr not in self.sample_rates:
            raise ValueError(f"Supported sampling rates: {self.sample_rates}")

        if sr / np.shape(x)[1] > 31.25:
            # Chunk too small logic from Pipecat
            raise ValueError("Input audio chunk is too short")

        return x, sr

    def __call__(self, x, sr: int):
        # Ensure input is float32
        if x.dtype != np.float32:
             x = x.astype(np.float32)

        x, sr = self._validate_input(x, sr)

        # Silero V5 specific window sizes
        num_samples = 512 if sr == 16000 else 256

        # Strict window size validation (Silero V5 requires exact chunk size)
        if np.shape(x)[-1] != num_samples:
            raise ValueError(
                f"Provided number of samples is {np.shape(x)[-1]} "
                f"(Required: 256 for 8kHz, 512 for 16kHz)"
            )

        batch_size = np.shape(x)[0]
        context_size = 64 if sr == 16000 else 32

        if not self._last_batch_size:
            self.reset_states(batch_size)
        if (self._last_sr) and (self._last_sr != sr):
            self.reset_states(batch_size)
        if (self._last_batch_size) and (self._last_batch_size != batch_size):
            self.reset_states(batch_size)

        if not np.shape(self._context)[1]:
            self._context = np.zeros((batch_size, context_size), dtype="float32")

        x = np.concatenate((self._context, x), axis=1)

        if sr in [8000, 16000]:
            ort_inputs = {"input": x, "state": self._state, "sr": np.array(sr, dtype="int64")}
            ort_outs = self.session.run(None, ort_inputs)
            out, state = ort_outs
            self._state = state
        else:
            raise ValueError("Unsupported sample rate")

        self._context = x[..., -context_size:]
        self._last_sr = sr
        self._last_batch_size = batch_size

        return out[0][0] # Return float confidence
