/**
 * agentService.ts
 * Handles all /api/agents/* API calls.
 * All URLs are built from the shared `api` client (no hardcoded URLs here).
 */
import { api } from './api'
import { Agent } from '@/types/config'

interface ActiveAgentResponse extends Agent {
    system_prompt: string
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
}

export const agentService = {
    /** Return all agents ordered by creation date. */
    listAgents: async (): Promise<Agent[]> => {
        return await api.get<Agent[]>('/agents')
    },

    /** Create a new agent with system-default configuration. */
    createAgent: async (name: string): Promise<Agent> => {
        return await api.post<Agent>('/agents', { name })
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
