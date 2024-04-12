import { useMemo } from 'react'

export default function (name: string, regexString: string | null) {
  const regex = useMemo(() => {
    return regexString ? new RegExp(regexString) : null
  }, [regexString])
  let regexValid = true
  try {
    if (name && regex) {
      regexValid = !!name.match(new RegExp(regex))
    }
  } catch (e) {
    regexValid = false
  }
  return regexValid
}
