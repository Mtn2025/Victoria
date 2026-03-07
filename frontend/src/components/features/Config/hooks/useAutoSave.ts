import { useEffect, useCallback, useRef } from 'react'
import { useAppDispatch, useAppSelector } from '@/hooks/useRedux'
import { saveAgentConfig, setSaveStatus } from '@/store/slices/configSlice'
import debounce from 'lodash/debounce'

export const useAutoSave = (debounceMs = 800) => {
    const dispatch = useAppDispatch()
    const { browser, twilio, telnyx, saveStatus, lastSaved, isLoadingOptions } = useAppSelector(state => state.config)
    const activeProfile = useAppSelector(state => state.ui.activeProfile)

    const initialLoadDone = useRef(false)
    const prevJSON = useRef(JSON.stringify({ browser, twilio, telnyx }))

    // eslint-disable-next-line react-hooks/exhaustive-deps
    const saveChanges = useCallback(
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        debounce((payload: any) => {
            dispatch(saveAgentConfig(payload))
        }, debounceMs),
        [dispatch, debounceMs]
    )

    useEffect(() => {
        // Skip first render
        if (!initialLoadDone.current) {
            initialLoadDone.current = true
            return
        }

        const currentString = JSON.stringify({ browser, twilio, telnyx })

        // FIX CRÍTICO: Si fetchAgentConfig está hidratando el estado desde el servidor,
        // solo actualizar prevJSON — NO disparar ningún PATCH.
        // Sin este guard, cada recarga dispara un PATCH que sobreescribe los valores de la BD
        // con el estado transitorio de hidratación (loop destructivo).
        if (isLoadingOptions) {
            prevJSON.current = currentString
            return
        }

        // Si el estado cambió (por acción del USUARIO, no por hidratación), guardar
        if (currentString !== prevJSON.current) {
            prevJSON.current = currentString
            dispatch(setSaveStatus('saving'))

            if (activeProfile === 'telnyx') {
                const payload: any = { ...browser }
                payload.agent_provider = activeProfile
                payload.connectivity_config = telnyx
                saveChanges(payload)
            } else if (activeProfile === 'twilio') {
                const payload: any = { ...browser }
                payload.agent_provider = activeProfile
                payload.connectivity_config = twilio
                saveChanges(payload)
            } else {
                const payload: any = { ...browser }
                payload.agent_provider = activeProfile
                saveChanges(payload)
            }
        }
    }, [browser, twilio, telnyx, activeProfile, isLoadingOptions, dispatch, saveChanges])

    // Cleanup pending debounces on unmount
    useEffect(() => {
        return () => {
            saveChanges.cancel()
        }
    }, [saveChanges])

    return { saveStatus, lastSaved }
}
