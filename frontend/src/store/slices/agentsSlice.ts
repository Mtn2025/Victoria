/**
 * agentsSlice.ts
 * Redux slice for agent lifecycle management.
 */
import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit'
import { Agent } from '@/types/config'
import { agentService } from '@/services/agentService'

interface AgentsState {
    agents: Agent[]
    activeAgent: Agent | null
    loading: boolean
    error: string | null
}

const initialState: AgentsState = {
    agents: [],
    activeAgent: null,
    loading: false,
    error: null,
}

// ------------------------------------------------------------------ //
// Thunks                                                               //
// ------------------------------------------------------------------ //

export const fetchAgents = createAsyncThunk(
    'agents/fetchAgents',
    async () => agentService.listAgents()
)

export const fetchActiveAgent = createAsyncThunk(
    'agents/fetchActiveAgent',
    async () => agentService.getActiveAgent()
)

export const createAgent = createAsyncThunk(
    'agents/createAgent',
    async (name: string) => agentService.createAgent(name)
)

export const activateAgent = createAsyncThunk(
    'agents/activateAgent',
    async (agentUuid: string) => agentService.activateAgent(agentUuid)
)

export const updateAgentName = createAsyncThunk(
    'agents/updateAgentName',
    async ({ agentUuid, name }: { agentUuid: string; name: string }) =>
        agentService.updateAgentName(agentUuid, name)
)

export const deleteAgent = createAsyncThunk(
    'agents/deleteAgent',
    async (agentUuid: string) => {
        await agentService.deleteAgent(agentUuid)
        return agentUuid   // return uuid to remove from state
    }
)

// ------------------------------------------------------------------ //
// Slice                                                                //
// ------------------------------------------------------------------ //

const agentsSlice = createSlice({
    name: 'agents',
    initialState,
    reducers: {
        clearError: (state) => { state.error = null },
    },
    extraReducers: (builder) => {
        // fetchAgents
        builder.addCase(fetchAgents.pending, (state) => { state.loading = true })
        builder.addCase(fetchAgents.fulfilled, (state, action: PayloadAction<Agent[]>) => {
            state.loading = false
            state.agents = action.payload
        })
        builder.addCase(fetchAgents.rejected, (state, action) => {
            state.loading = false
            state.error = action.error.message ?? 'Error al cargar agentes'
        })

        // fetchActiveAgent
        builder.addCase(fetchActiveAgent.pending, (state) => { state.loading = true })
        builder.addCase(fetchActiveAgent.fulfilled, (state, action) => {
            state.loading = false
            state.activeAgent = action.payload
                ? {
                    agent_uuid: action.payload.agent_uuid,
                    name: action.payload.name,
                    is_active: action.payload.is_active,
                    created_at: action.payload.created_at,
                }
                : null
        })
        builder.addCase(fetchActiveAgent.rejected, (state, action) => {
            state.loading = false
            state.error = action.error.message ?? 'Error al cargar agente activo'
        })

        // createAgent
        builder.addCase(createAgent.pending, (state) => { state.loading = true })
        builder.addCase(createAgent.fulfilled, (state, action: PayloadAction<Agent>) => {
            state.loading = false
            state.agents = [...state.agents, action.payload]
        })
        builder.addCase(createAgent.rejected, (state, action) => {
            state.loading = false
            state.error = action.error.message ?? 'Error al crear agente'
        })

        // activateAgent — update both list and activeAgent
        builder.addCase(activateAgent.pending, (state) => { state.loading = true })
        builder.addCase(activateAgent.fulfilled, (state, action: PayloadAction<Agent>) => {
            state.loading = false
            state.activeAgent = action.payload
            state.agents = state.agents.map(a => ({
                ...a,
                is_active: a.agent_uuid === action.payload.agent_uuid,
            }))
        })
        builder.addCase(activateAgent.rejected, (state, action) => {
            state.loading = false
            state.error = action.error.message ?? 'Error al activar agente'
        })

        // updateAgentName — patch name in list
        builder.addCase(updateAgentName.fulfilled, (state, action: PayloadAction<Agent>) => {
            state.agents = state.agents.map(a =>
                a.agent_uuid === action.payload.agent_uuid ? { ...a, name: action.payload.name } : a
            )
            if (state.activeAgent?.agent_uuid === action.payload.agent_uuid) {
                state.activeAgent = { ...state.activeAgent, name: action.payload.name }
            }
        })
        builder.addCase(updateAgentName.rejected, (state, action) => {
            state.error = action.error.message ?? 'Error al renombrar agente'
        })

        // deleteAgent — remove from list
        builder.addCase(deleteAgent.fulfilled, (state, action: PayloadAction<string>) => {
            state.agents = state.agents.filter(a => a.agent_uuid !== action.payload)
        })
        builder.addCase(deleteAgent.rejected, (state, action) => {
            state.error = action.error.message ?? 'No se pudo eliminar el agente'
        })
    },
})

export const { clearError } = agentsSlice.actions
export default agentsSlice.reducer
