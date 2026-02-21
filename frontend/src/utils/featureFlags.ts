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
    // ── Fase 1: Auth ── AUDITADO y verificado
    AUTH: true,

    // ── Fase 2: Simulador de llamada real ──────────────────────────────────
    SIMULATOR_PANEL: true,         // Panel derecho (SimulatorPage)
    SIMULATOR_CONFIG: true,        // Panel izquierdo en /simulator (ConfigPage tabs)
    SIMULATOR_WEBSOCKET: true,     // Conexión WebSocket real al backend
    SIMULATOR_TRANSCRIPTS: true,   // Transcripciones en tiempo real

    // ── Fase 3: Agentes ──────────────────────────────────────────────────
    AGENTS_LIST: false,            // Listar agentes desde DB
    AGENTS_CREATE: false,          // Crear nuevo agente
    AGENTS_EDIT: false,            // Editar agente existente
    AGENTS_ACTIVATE: false,        // Activar/desactivar agente

    // ── Fase 4: Config del agente activo ─────────────────────────────────
    CONFIG_MODEL: true,            // ModelSettings (LLM provider/model/temp)
    CONFIG_VOICE: true,            // VoiceSettings (TTS voice/speed/pitch)
    CONFIG_TRANSCRIBER: true,      // TranscriberSettings (STT language)

    // ── Fase 5: Historial ────────────────────────────────────────────────
    HISTORY_LIST: false,           // Lista de llamadas desde DB
    HISTORY_DETAIL: false,         // Detalle + transcripción completa
    HISTORY_EXTRACTION: false,     // Datos extraídos (intent, summary, entities)
} as const

export type FeatureKey = keyof typeof FEATURES
