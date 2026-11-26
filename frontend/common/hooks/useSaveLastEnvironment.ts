import { useEffect } from 'react'

type LastEnvironment = {
  environmentId?: string
  organisationId?: number
  projectId?: number
}

export function useSaveLastEnvironment({
  environmentId,
  organisationId,
  projectId,
}: LastEnvironment): void {
  useEffect(() => {
    if (typeof AsyncStorage !== 'undefined' && AsyncStorage.setItem) {
      AsyncStorage.setItem(
        'lastEnv',
        JSON.stringify({ environmentId, orgId: organisationId, projectId }),
      )
    }
  }, [environmentId, organisationId, projectId])
}
