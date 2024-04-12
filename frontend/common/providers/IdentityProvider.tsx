import { FC, ReactNode, useEffect, useState } from 'react'
import AppActions from 'common/dispatcher/app-actions'
import {
  FeatureState,
  IdentityStoreModel,
  ProjectFlag,
} from 'common/types/responses'
import IdentityStore from 'common/stores/identity-store'
import FeatureListStore from 'common/stores/feature-list-store'

type IdentityProviderType = {
  onSave?: () => void
  children: (
    props: {
      identityFlags: null | Record<string, FeatureState>
      environmentFlags: null | Record<string, FeatureState>
      identity: null | IdentityStoreModel
      projectFlags: ProjectFlag[]
      traits: IdentityStoreModel['traits']
      isLoading: boolean
      isSaving: boolean
      error: any
    },
    actions: {
      changeUserFlag: typeof AppActions.changeUserFlag
      createTrait: typeof AppActions.editTrait
      editFeatureValue: typeof AppActions.editUserFlag
      editTrait: typeof AppActions.editTrait
      removeFlag: typeof AppActions.removeUserFlag
      toggleFlag: typeof AppActions.toggleUserFlag
    },
  ) => ReactNode
}

const IdentityProvider: FC<IdentityProviderType> = ({ children, onSave }) => {
  const [_, setUpdate] = useState(Date.now())

  useEffect(() => {
    const _onSave = () => onSave?.()
    const _onChange = () => setUpdate(Date.now())
    IdentityStore.on('saved', _onSave)
    IdentityStore.on('change', _onChange)
    FeatureListStore.on('change', _onChange)

    return () => {
      IdentityStore.off('saved', _onSave)
      IdentityStore.off('change', _onChange)
      FeatureListStore.off('change', _onChange)
    }
    //eslint-disable-next-line
  }, [])

  return (
    <>
      {children(
        {
          environmentFlags: FeatureListStore.getEnvironmentFlags(),
          //@ts-expect-error error can be defined
          error: FeatureListStore.error,
          //@ts-expect-error model does exist
          identity: IdentityStore.model,
          identityFlags: IdentityStore.getIdentityFlags(),
          isLoading: IdentityStore.isLoading || FeatureListStore.isLoading,
          isSaving: IdentityStore.isSaving,
          projectFlags: FeatureListStore.getProjectFlags(),
          traits: IdentityStore.getTraits(),
        },
        {
          changeUserFlag: AppActions.changeUserFlag,
          createTrait: AppActions.editTrait,
          editFeatureValue: AppActions.editUserFlag,
          editTrait: AppActions.editTrait,
          removeFlag: AppActions.removeUserFlag,
          toggleFlag: AppActions.toggleUserFlag,
        },
      )}
    </>
  )
}

export default IdentityProvider
