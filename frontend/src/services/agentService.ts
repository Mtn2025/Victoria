/**
 * agentService.ts
 * Handles all /api/agents/* API calls.
 * All URLs are built from the shared `api` client (no hardcoded URLs here).
 */
import { api } from './api'
import { Agent } from '@/types/config'

interface ActiveAgentResponse extends Agent {
    system_prompt: string
    language: string
    first_message: string
    silence_timeout_ms: number
    voice: {
        name: string
        style: string | null
        speed: number
        pitch: number
        volume: number
    }
    llm_config: Record<string, unknown>
    stt_config: Record<string, unknown>
    voice_config_json: Record<string, unknown>
    tools_config: Record<string, unknown>
    flow_config: Record<string, unknown>
    analysis_config: Record<string, unknown>
    system_config: Record<string, unknown>
    connectivity_config: Record<string, unknown>
}

export const agentService = {
    /** Return all agents ordered by creation date. Filter by provider if specified. */
    listAgents: async (provider?: string): Promise<Agent[]> => {
        const url = provider ? `/agents?provider=${provider}` : '/agents'
        return await api.get<Agent[]>(url)
    },

    /** Create a new agent with system-default configuration. */
    createAgent: async (name: string, language: string = 'es-MX'): Promise<Agent> => {
        return await api.post<Agent>('/agents', { name, language })
    },

    /** Return the active agent with its full configuration. Returns null on 404. */
    getActiveAgent: async (): Promise<ActiveAgentResponse | null> => {
        try {
            return await api.get<ActiveAgentResponse>('/agents/active')
        } catch (err: unknown) {
            // 404 = no active agent (expected when none has been activated yet)
            if (err && typeof err === 'object' && 'response' in err) {
                const response = (err as { response?: { status?: number } }).response
                if (response?.status === 404) return null
            }
            throw err
        }
    },

    /** Activate the given agent (deactivates all others). */
    activateAgent: async (agentUuid: string): Promise<Agent> => {
        return await api.post<Agent>(`/agents/${agentUuid}/activate`)
    },

    /** Clone the given agent to a new provider context. */
    cloneAgent: async (agentUuid: string, targetProvider: string): Promise<Agent> => {
        return await api.post<Agent>(`/agents/${agentUuid}/clone`, { provider: targetProvider })
    },

    /** Update config fields for a specific agent. */
    updateAgentConfig: async (agentUuid: string, config: Record<string, unknown>): Promise<void> => {
        await api.patch(`/agents/${agentUuid}`, config)
    },

    /** Rename an agent. */
    updateAgentName: async (agentUuid: string, name: string): Promise<Agent> => {
        return await api.patch<Agent>(`/agents/${agentUuid}/name`, { name })
    },

    /** Permanently delete an agent. The backend rejects deleting the active agent. */
    deleteAgent: async (agentUuid: string): Promise<void> => {
        await api.delete(`/agents/${agentUuid}`)
    },
}
