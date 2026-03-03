import { useEffect, useCallback, useRef } from 'react'
import { useAppDispatch, useAppSelector } from '@/hooks/useRedux'
import { saveAgentConfig, setSaveStatus } from '@/store/slices/configSlice'
import debounce from 'lodash/debounce'

export const useAutoSave = (debounceMs = 800) => {
    const dispatch = useAppDispatch()
    const { browser, twilio, telnyx, saveStatus, lastSaved } = useAppSelector(state => state.config)
    const activeProfile = useAppSelector(state => state.ui.activeProfile)

    const initialLoadDone = useRef(false)
    const prevJSON = useRef(JSON.stringify({ browser, twilio, telnyx }))

    const saveChanges = useCallback(
        debounce((payload: any) => {
            dispatch(saveAgentConfig(payload))
        }, debounceMs),
        [dispatch, debounceMs]
    )

    useEffect(() => {
        // Skip first render/hydration
        if (!initialLoadDone.current) {
            initialLoadDone.current = true
            return
        }

        const currentString = JSON.stringify({ browser, twilio, telnyx })

        // If config changed, trigger debounced save
        if (currentString !== prevJSON.current) {
            prevJSON.current = currentString
            dispatch(setSaveStatus('saving'))

            // Construct payload: base config + connectivity_config based on profile
            const payload: any = { ...browser }
            if (activeProfile === 'twilio') {
                payload.connectivity_config = twilio
            } else if (activeProfile === 'telnyx') {
                payload.connectivity_config = telnyx
            }
            saveChanges(payload)
        }
    }, [browser, twilio, telnyx, activeProfile, dispatch, saveChanges])

    // Cleanup pending debounces on unmount
    useEffect(() => {
        return () => {
            saveChanges.cancel()
        }
    }, [saveChanges])

    return { saveStatus, lastSaved }
}
