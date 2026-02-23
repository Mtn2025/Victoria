import { useEffect, useCallback, useRef } from 'react'
import { useAppDispatch, useAppSelector } from '@/hooks/useRedux'
import { saveBrowserConfig, setSaveStatus } from '@/store/slices/configSlice'
import debounce from 'lodash/debounce'

export const useAutoSave = (debounceMs = 800) => {
    const dispatch = useAppDispatch()
    const { browser, saveStatus, lastSaved } = useAppSelector(state => state.config)

    const initialLoadDone = useRef(false)
    const prevBrowser = useRef(JSON.stringify(browser))

    const saveChanges = useCallback(
        debounce((currentConfig: typeof browser) => {
            dispatch(saveBrowserConfig(currentConfig))
        }, debounceMs),
        [dispatch, debounceMs]
    )

    useEffect(() => {
        // Skip first render/hydration
        if (!initialLoadDone.current) {
            initialLoadDone.current = true
            return
        }

        const currentString = JSON.stringify(browser)

        // If config changed, trigger debounced save
        if (currentString !== prevBrowser.current) {
            prevBrowser.current = currentString
            dispatch(setSaveStatus('saving'))
            saveChanges(browser)
        }
    }, [browser, dispatch, saveChanges])

    // Cleanup pending debounces on unmount
    useEffect(() => {
        return () => {
            saveChanges.cancel()
        }
    }, [saveChanges])

    return { saveStatus, lastSaved }
}
