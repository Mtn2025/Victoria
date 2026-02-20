import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { callsService } from '../../services/callsService';
import { Call, CallFilter } from '../../types/call';

interface CallsState {
    items: Call[];
    webhookCalls: Call[]; // Real-time/Simulated calls
    status: 'idle' | 'loading' | 'succeeded' | 'failed';
    error: string | null;
    currentCall: Call | null;
}

const initialState: CallsState = {
    items: [],
    webhookCalls: [],
    status: 'idle',
    error: null,
    currentCall: null,
};

export const fetchCalls = createAsyncThunk('calls/fetchCalls', async (filter: CallFilter | undefined) => {
    const response = await callsService.getAll(filter);
    return response.data || [];
});

const callsSlice = createSlice({
    name: 'calls',
    initialState,
    reducers: {
        addCall: (state, action: PayloadAction<Call>) => {
            state.items.unshift(action.payload);
        },
        updateCall: (state, action: PayloadAction<Call>) => {
            const index = state.items.findIndex(c => c.id === action.payload.id);
            if (index !== -1) {
                state.items[index] = action.payload;
            }
        },
        setCurrentCall: (state, action: PayloadAction<Call | null>) => {
            state.currentCall = action.payload;
        },
        addWebhookCall: (state, action: PayloadAction<Call>) => {
            state.webhookCalls.unshift(action.payload);
        }
    },
    extraReducers: (builder) => {
        builder
            .addCase(fetchCalls.pending, (state) => {
                state.status = 'loading';
            })
            .addCase(fetchCalls.fulfilled, (state, action) => {
                state.status = 'succeeded';
                state.items = action.payload;
            })
            .addCase(fetchCalls.rejected, (state, action) => {
                state.status = 'failed';
                state.error = action.error.message || 'Failed to fetch calls';
            });
    },
});

export const { addCall, updateCall, setCurrentCall, addWebhookCall } = callsSlice.actions;
export default callsSlice.reducer;
