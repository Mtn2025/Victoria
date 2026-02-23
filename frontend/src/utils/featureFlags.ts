/**
 * Feature Flags — Victoria Dashboard
 *
 * ARQUITECTURA: Todos los flags comienzan en FALSE (FREEZE).
 * Se activan uno por uno después de verificación E2E completa
 * (backend endpoint ✓ + frontend service ✓ + UI ✓ + sin hardcodes ✓).
 *
 * Para activar una feature:
 *   1. Cambiar el flag a `true`
 *   2. Verificar E2E localmente
 *   3. `git push` → Coolify despliega
 *
 * NUNCA activar un flag sin pasar E2E primero.
 */
export const FEATURES = {
    // ── FASE 1: Auth — siempre activo ──────────────────────────────────────
    AUTH: true,

    // ── FASE 3: Simulador WebSocket — activar después de verificar E2E ─────
    // Orden: WEBSOCKET → PANEL → TRANSCRIPTS → CONFIG
    SIMULATOR_WEBSOCKET: true,     // Conexión WebSocket real al backend
    SIMULATOR_PANEL: true,         // Panel derecho (SimulatorPage UI)
    SIMULATOR_TRANSCRIPTS: true,   // Transcripciones en tiempo real
    SIMULATOR_CONFIG: false,       // Panel izquierdo (pestañas Config)

    // ── FASE 7: Agentes — activar después de verificar E2E ─────────────────
    AGENTS_LIST: false,            // Listar agentes desde DB
    AGENTS_CREATE: false,          // Crear nuevo agente
    AGENTS_EDIT: false,            // Editar agente existente
    AGENTS_ACTIVATE: false,        // Activar/desactivar agente

    // ── FASE 4-6: Config — activar después de verificar endpoints ──────────
    CONFIG_MODEL: false,           // ModelSettings (LLM provider/model/temp)
    CONFIG_VOICE: false,           // VoiceSettings (TTS voice/speed/pitch)
    CONFIG_TRANSCRIBER: false,     // TranscriberSettings (STT language)

    // ── FASE 8: Historial — activar después de verificar E2E ───────────────
    HISTORY_LIST: false,           // Lista de llamadas desde DB
    HISTORY_DETAIL: false,         // Detalle + transcripción completa
    HISTORY_EXTRACTION: false,     // Datos extraídos (intent, summary, entities)
} as const

export type FeatureKey = keyof typeof FEATURES
