import { useEffect, useCallback, useRef } from 'react'
import { useAppDispatch, useAppSelector } from '@/hooks/useRedux'
import { saveAgentConfig, saveTelnyxConfig, setSaveStatus } from '@/store/slices/configSlice'
import debounce from 'lodash/debounce'

export const useAutoSave = (debounceMs = 800) => {
    const dispatch = useAppDispatch()
    const { browser, twilio, telnyx, saveStatus, lastSaved } = useAppSelector(state => state.config)
    const activeProfile = useAppSelector(state => state.ui.activeProfile)

    const initialLoadDone = useRef(false)
    const prevJSON = useRef(JSON.stringify({ browser, twilio, telnyx }))

    const saveChanges = useCallback(
        debounce((payload: any, profile: string) => {
            if (profile === 'telnyx') {
                // Telnyx connectivity / tools / system fields go via dedicated thunk
                dispatch(saveTelnyxConfig(payload))
            } else {
                // Browser or Twilio: send via updateBrowserConfig (includes connectivity_config for twilio)
                dispatch(saveAgentConfig(payload))
            }
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

            if (activeProfile === 'telnyx') {
                // Save only the telnyx slice fields
                saveChanges(telnyx, 'telnyx')
            } else if (activeProfile === 'twilio') {
                const payload: any = { ...browser }
                payload.agent_provider = activeProfile
                payload.connectivity_config = twilio
                saveChanges(payload, 'twilio')
            } else {
                // Browser profile: send browser config
                const payload: any = { ...browser }
                payload.agent_provider = activeProfile
                saveChanges(payload, 'browser')
            }
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

