import { useState } from 'react'

const useWarehouseFormSubmit = <T>(onSave: (data: T) => Promise<unknown>) => {
  const [isSaving, setIsSaving] = useState(false)
  const [saveFailed, setSaveFailed] = useState(false)

  const submit = async (data: T) => {
    if (isSaving) return
    setIsSaving(true)
    setSaveFailed(false)
    try {
      await onSave(data)
    } catch {
      setSaveFailed(true)
      setIsSaving(false)
    }
  }

  return {
    clearSaveFailed: () => setSaveFailed(false),
    isSaving,
    saveFailed,
    submit,
  }
}

export default useWarehouseFormSubmit
