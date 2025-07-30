import React, { useEffect } from 'react'
import { UtmsType } from './types/utms'
import Utils from './utils/utils'

export const useUTMs = () => {
  const [utms, setUtms] = React.useState<UtmsType | null>(null)

  useEffect(() => {
    const utmsParams = Utils.getUtmsFromUrl(document.location.href)
    if (Object.keys(utmsParams).length > 0) {
      setUtms(utmsParams)
    }
  }, [])

  return utms
}
