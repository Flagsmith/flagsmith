import { useCallback, useMemo } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { setLifecycleEnvironment } from 'common/lifecycleEnvironmentSlice'
import { useProjectEnvironments } from 'common/hooks/useProjectEnvironments'
import { StoreStateType } from 'common/store'
import { predictProdEnvironment } from './predictProdEnvironment'

// Resolves the environment used for lifecycle classification for a project.
// Preference order: the user's stored choice → an environment whose name
// looks like production → the first environment. The choice is cached per
// project in the Redux store so it survives navigation.
export function useLifecycleEnvironment(projectId: number) {
  const dispatch = useDispatch()
  const { environments } = useProjectEnvironments(projectId)

  const storedEnvironmentId = useSelector(
    (state: StoreStateType) => state.lifecycleEnvironment.byProject[projectId],
  )

  const defaultEnvironmentId = useMemo(
    () => predictProdEnvironment(environments),
    [environments],
  )

  const environmentId = storedEnvironmentId ?? defaultEnvironmentId

  const setEnvironmentId = useCallback(
    (id: number) => {
      dispatch(setLifecycleEnvironment({ environmentId: id, projectId }))
    },
    [dispatch, projectId],
  )

  return { environmentId, environments, setEnvironmentId }
}
