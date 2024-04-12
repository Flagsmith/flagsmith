import { FC, ReactNode, useEffect, useState } from 'react'
import AppActions from 'common/dispatcher/app-actions'
import {
  FeatureState,
  ProjectFlag,
  SegmentOverride,
} from 'common/types/responses'
import FeatureListStore from 'common/stores/feature-list-store'
import { Req } from 'common/types/requests'
import ProjectStore from 'common/stores/project-store'
import {
  CreateFeatureStateType,
  CreateProjectFlagType,
} from 'components/modals/CreateFlagValue'

type FeatureListProviderType = {
  onSave?: (isCreate?: boolean) => void
  onError?: (error?: any) => void
  children: (
    props: {
      projectFlags: ProjectFlag[]
      environmentFlags: null | Record<string, FeatureState>
      isLoading: boolean
      isSaving: boolean
      maxFeaturesAllowed: null | number
      totalFeatures: null | number
      error: any
    },
    actions: {
      createChangeRequest: CreateChangeRequestAction
      createFlag: CreateFlagAction
      editFeatureValue: EditFeatureValueAction
      removeFlag: RemoveFlagAction
      editFeatureSegments: EditFeatureSegmentsAction
      editFeatureSettings: EditFeatureSettingsAction
      toggleFlag: ToggleFlagAction
    },
  ) => ReactNode
}
const FeatureListProvider: FC<FeatureListProviderType> = ({
  children,
  onError,
  onSave,
}) => {
  const [_, setUpdate] = useState(Date.now())

  useEffect(() => {
    const _onSave = (isCreate?: boolean) => onSave?.(isCreate)
    const _onChange = () => setUpdate(Date.now())
    const _onError = () => {
      //@ts-expect-error error is defined
      onError?.(FeatureListStore.error)
      setUpdate(Date.now())
    }
    FeatureListStore.on('saved', _onSave)
    FeatureListStore.on('change', _onChange)
    FeatureListStore.on('problem', _onError)

    return () => {
      FeatureListStore.off('saved', _onSave)
      FeatureListStore.off('change', _onChange)
      FeatureListStore.off('problem', _onError)
    }
    //eslint-disable-next-line
  }, [])

  const editFeatureValue = (
    projectId: string,
    environmentId: string,
    newProjectFlag: CreateProjectFlagType,
    projectFlag: ProjectFlag,
    environmentFlag: CreateFeatureStateType,
  ) => {
    AppActions.editFeatureMv(
      projectId,
      Object.assign({}, projectFlag, {
        multivariate_options:
          newProjectFlag.multivariate_options &&
          newProjectFlag.multivariate_options.map((v) => {
            const matchingProjectVariate =
              (projectFlag.multivariate_options &&
                projectFlag.multivariate_options.find((p) => p.id === v.id)) ||
              v
            return {
              ...v,
              default_percentage_allocation:
                matchingProjectVariate.default_percentage_allocation,
            }
          }),
      }),
      (newProjectFlag: CreateProjectFlagType) => {
        AppActions.editEnvironmentFlag(
          projectId,
          environmentId,
          newProjectFlag,
          projectFlag,
          {
            ...environmentFlag,
            multivariate_feature_state_values:
              newProjectFlag.multivariate_options.map((v, i) => ({
                ...newProjectFlag.multivariate_options[i],
                id: v.id,
              })),
          },
          null,
          'VALUE',
        )
      },
    )
  }
  return (
    <>
      {children(
        {
          environmentFlags: FeatureListStore.getEnvironmentFlags(),
          //@ts-expect-error error can be defined
          error: FeatureListStore.error,
          isLoading: FeatureListStore.isLoading,
          isSaving: FeatureListStore.isSaving,
          maxFeaturesAllowed: ProjectStore.getMaxFeaturesAllowed(),
          projectFlags: FeatureListStore.getProjectFlags(),
          totalFeatures: ProjectStore.getTotalFeatures(),
        },
        {
          createChangeRequest: (
            projectId,
            environmentId,
            newProjectFlag,
            projectFlag,
            environmentFlag,
            segmentOverrides,
            changeRequest,
            commit,
          ) => {
            AppActions.editFeatureMv(
              projectId,
              Object.assign({}, projectFlag, newProjectFlag, {
                multivariate_options:
                  newProjectFlag.multivariate_options &&
                  newProjectFlag.multivariate_options.map((v) => {
                    const matchingProjectVariate =
                      (projectFlag.multivariate_options &&
                        projectFlag.multivariate_options.find(
                          (p) => p.id === v.id,
                        )) ||
                      v
                    return {
                      ...v,
                      default_percentage_allocation:
                        matchingProjectVariate.default_percentage_allocation,
                    }
                  }),
              }),
              (newProjectFlag: CreateProjectFlagType) => {
                AppActions.editEnvironmentFlagChangeRequest(
                  projectId,
                  environmentId,
                  newProjectFlag,
                  projectFlag,
                  {
                    ...environmentFlag,
                    multivariate_feature_state_values:
                      newProjectFlag.multivariate_options,
                  },
                  segmentOverrides,
                  changeRequest,
                  commit,
                )
              },
            )
          },
          createFlag: AppActions.createFlag,
          editFeatureSegments: (
            projectId,
            environmentId,
            newProjectFlag,
            projectFlag,
            environmentFlag,
            segmentOverrides,
            onComplete,
          ) => {
            AppActions.editEnvironmentFlag(
              projectId,
              environmentId,
              newProjectFlag,
              projectFlag,
              {
                ...environmentFlag,
                multivariate_feature_state_values:
                  newProjectFlag.multivariate_options,
              },
              segmentOverrides,
              'SEGMENT',
              onComplete,
            )
          },
          editFeatureSettings: (
            projectId,
            environmentId,
            newProjectFlag,
            projectFlag,
          ) => {
            AppActions.editFeature(
              projectId,
              Object.assign({}, projectFlag, newProjectFlag, {
                multivariate_options:
                  newProjectFlag.multivariate_options &&
                  newProjectFlag.multivariate_options.map((v) => {
                    const matchingProjectVariate =
                      (projectFlag.multivariate_options &&
                        projectFlag.multivariate_options.find(
                          (p) => p.id === v.id,
                        )) ||
                      v
                    return {
                      ...v,
                      default_percentage_allocation:
                        matchingProjectVariate.default_percentage_allocation,
                    }
                  }),
              }),
              () => {
                FeatureListStore.isSaving = false
                FeatureListStore.trigger('saved')
                FeatureListStore.trigger('change')
              },
            )
          },
          editFeatureValue,
          removeFlag: AppActions.removeFlag,
          toggleFlag: (
            projectId,
            environmentId,
            projectFlag,
            environmentFlag,
          ) => {
            editFeatureValue(
              projectId,
              environmentId,
              /* todo: Saving features involves sending an adjusted project flag rather than a feature state (old tech debt).
               This will be removed when migrating to RTK. The following converts the feature state to the accepted format.
              */
              {
                ...projectFlag,
                default_enabled: !environmentFlag.enabled,
                initial_value: environmentFlag.feature_state_value,
                multivariate_options: projectFlag.multivariate_options.map(
                  (mv) => {
                    const matching =
                      environmentFlag.multivariate_feature_state_values.find(
                        (v) => v.multivariate_feature_option == mv.id,
                      )
                    return {
                      ...mv,
                      default_percentage_allocation:
                        matching?.percentage_allocation || 0,
                    }
                  },
                ),
              },
              projectFlag,
              environmentFlag,
            )
          },
        },
      )}
    </>
  )
}

export default FeatureListProvider

type CreateChangeRequestAction = (
  projectId: string,
  environmentApiKey: string,
  newProjectFlag: CreateProjectFlagType,
  projectFlag: ProjectFlag,
  environmentFlag: CreateFeatureStateType,
  segmentOverrides: SegmentOverride[],
  changeRequest: Req['createChangeRequest'],
  commit: boolean,
) => void

type CreateFlagAction = (
  projectId: string,
  environmentKey: string,
  newProjectFlag: CreateProjectFlagType,
  segmentOverrides: SegmentOverride[],
) => void

type RemoveFlagAction = (
  projectId: string,
  newProjectFlag: CreateProjectFlagType,
) => void

type EditFeatureSegmentsAction = (
  projectId: string,
  environmentApiKey: string,
  newProjectFlag: CreateProjectFlagType,
  projectFlag: ProjectFlag,
  environmentFlag: CreateFeatureStateType,
  segmentOverrides: SegmentOverride[],
  onComplete?: () => void,
) => void

type EditFeatureSettingsAction = (
  projectId: string,
  environmentApiKey: string,
  newProjectFlag: CreateProjectFlagType,
  projectFlag: ProjectFlag,
  environmentFlag: CreateFeatureStateType,
) => void

type EditFeatureValueAction = (
  projectId: string,
  environmentApiKey: string,
  newProjectFlag: CreateProjectFlagType,
  projectFlag: ProjectFlag,
  environmentFlag: CreateFeatureStateType,
) => void
type ToggleFlagAction = (
  projectId: string,
  environmentApiKey: string,
  projectFlag: ProjectFlag,
  environmentFlag: CreateFeatureStateType,
) => void
