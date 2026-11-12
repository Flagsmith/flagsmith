import { useState } from 'react'
import { getApiErrorDetail } from './warehouseFormUtils'

const useWarehouseFormSubmit = <T>(onSave: (data: T) => Promise<unknown>) => {
  const [isSaving, setIsSaving] = useState(false)
  const [saveFailed, setSaveFailed] = useState(false)
  const [saveErrorDetail, setSaveErrorDetail] = useState<string | null>(null)

  const submit = async (data: T) => {
    if (isSaving) return
    setIsSaving(true)
    setSaveFailed(false)
    setSaveErrorDetail(null)
    try {
      await onSave(data)
    } catch (error) {
      setSaveErrorDetail(getApiErrorDetail(error))
      setSaveFailed(true)
      setIsSaving(false)
    }
  }

  return {
    clearSaveFailed: () => setSaveFailed(false),
    isSaving,
    saveErrorDetail,
    saveFailed,
    submit,
  }
}

export default useWarehouseFormSubmit
