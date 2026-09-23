import { useEffect, useRef, useState } from 'react'
import flagsmith from '@flagsmith/flagsmith'
import isFreeEmailDomain from './utils/isFreeEmailDomain'
import { storageGet, storageSet } from './safeLocalStorage'

// The experiment only starts (identify + exposure) once the visitor types a
// free email domain — corporate-email visitors never enter the experiment.
export default function useSignupExperiment(
  useEnvironmentFlag: boolean,
  email: string,
) {
  const [variant, setVariant] = useState<string>()
  const started = useRef(false)

  useEffect(() => {
    if (useEnvironmentFlag || started.current || !isFreeEmailDomain(email)) {
      return
    }
    started.current = true
    const identifyAndExpose = async () => {
      const id =
        storageGet('signup_anonymous_id') ||
        (crypto.randomUUID?.() ?? `${Date.now()}-${Math.random()}`)
      storageSet('signup_anonymous_id', id)
      // @ts-expect-error transient is missing from the SDK's identify type
      await flagsmith.identify(id, {}, true)
      const flag = flagsmith.getExperimentFlag('signup_corporate_only')
      setVariant(flag?.enabled ? flag.variant : undefined)
    }
    identifyAndExpose().catch(() => {
      started.current = false
    })
  }, [useEnvironmentFlag, email])

  return variant
}
