import { useEffect, useState } from 'react'
import flagsmith from '@flagsmith/flagsmith'
import { storageGet, storageSet } from './safeLocalStorage'

export default function useSignupExperiment(useEnvironmentFlag: boolean) {
  const [variant, setVariant] = useState<string>()

  useEffect(() => {
    if (useEnvironmentFlag) {
      return
    }
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
    identifyAndExpose()
  }, [useEnvironmentFlag])

  return variant
}
