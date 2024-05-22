import React from 'react'
import FeatureListStore from 'common/stores/feature-list-store'
import ProjectStore from 'common/stores/project-store'

const FeatureListProvider = class extends React.Component {
  static displayName = 'FeatureListProvider'

  constructor(props, context) {
    super(props, context)
    this.state = {
      environmentFlags: FeatureListStore.getEnvironmentFlags(),
      isLoading: FeatureListStore.isLoading,
      isSaving: FeatureListStore.isSaving,
      lastSaved: FeatureListStore.getLastSaved(),
      maxFeaturesAllowed: ProjectStore.getMaxFeaturesAllowed(),
      projectFlags: FeatureListStore.getProjectFlags(),
      totalFeatures: ProjectStore.getTotalFeatures(),
    }
    ES6Component(this)
    this.listenTo(FeatureListStore, 'change', () => {
      this.setState({
        environmentFlags: FeatureListStore.getEnvironmentFlags(),
        error: FeatureListStore.error,
        isLoading: FeatureListStore.isLoading,
        isSaving: FeatureListStore.isSaving,
        lastSaved: FeatureListStore.getLastSaved(),
        maxFeaturesAllowed: ProjectStore.getMaxFeaturesAllowed(),
        projectFlags: FeatureListStore.getProjectFlags(),
        totalFeatures: ProjectStore.getTotalFeatures(),
        usageData: FeatureListStore.getFeatureUsage(),
      })
    })

    this.listenTo(FeatureListStore, 'saved', (data) => {
      this.props.onSave && this.props.onSave(data)
    })

    this.listenTo(FeatureListStore, 'problem', () => {
      this.setState({
        error: FeatureListStore.error,
        isLoading: FeatureListStore.isLoading,
        isSaving: FeatureListStore.isSaving,
        lastSaved: FeatureListStore.getLastSaved(),
        usageData: FeatureListStore.getFeatureUsage(),
      })
      this.props.onError && this.props.onError(FeatureListStore.error)
    })
  }

  toggleFlag = (projectId, environmentId, projectFlag, environmentFlag) => {
    this.editFeatureValue(
      projectId,
      environmentId,
      /* todo: Saving features involves sending an adjusted project flag rather than a feature state (old tech debt).
       This will be removed when migrating to RTK. The following converts the feature state to the accepted format.
      */
      {
        ...projectFlag,
        default_enabled: !environmentFlag.enabled,
        initial_value: environmentFlag.feature_state_value,
        multivariate_options: projectFlag.multivariate_options.map((mv) => {
          const matching =
            environmentFlag.multivariate_feature_state_values.find(
              (v) => v.multivariate_feature_option == mv.id,
            )
          return {
            ...mv,
            default_percentage_allocation: matching.percentage_allocation,
          }
        }),
      },
      projectFlag,
      environmentFlag,
    )
  }

  createFlag = (
    projectId,
    environmentId,
    flag,
    projectFlag,
    environmentFlag,
    segmentOverrides,
  ) => {
    AppActions.createFlag(projectId, environmentId, flag, segmentOverrides)
  }

  editFeatureValue = (
    projectId,
    environmentId,
    flag,
    projectFlag,
    environmentFlag,
  ) => {
    AppActions.editFeatureMv(
      projectId,
      Object.assign({}, projectFlag, {
        multivariate_options:
          flag.multivariate_options &&
          flag.multivariate_options.map((v) => {
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
      (newProjectFlag) => {
        AppActions.editEnvironmentFlag(
          projectId,
          environmentId,
          flag,
          newProjectFlag,
          {
            ...environmentFlag,
            multivariate_feature_state_values:
              newProjectFlag.multivariate_options.map((v, i) => ({
                ...flag.multivariate_options[i],
                id: v.id,
              })),
          },
          null,
          'VALUE',
        )
      },
    )
  }

  editFeatureSegments = (
    projectId,
    environmentId,
    flag,
    projectFlag,
    environmentFlag,
    segmentOverrides,
    onComplete,
  ) => {
    AppActions.editEnvironmentFlag(
      projectId,
      environmentId,
      flag,
      projectFlag,
      {
        ...environmentFlag,
        multivariate_feature_state_values: flag.multivariate_options,
      },
      segmentOverrides,
      'SEGMENT',
      onComplete,
    )
  }

  editFeatureSettings = (projectId, environmentId, flag, projectFlag) => {
    AppActions.editFeature(
      projectId,
      Object.assign({}, projectFlag, flag, {
        multivariate_options:
          flag.multivariate_options &&
          flag.multivariate_options.map((v) => {
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
      () => {
        FeatureListStore.isSaving = false
        FeatureListStore.trigger('saved', {})
        FeatureListStore.trigger('change')
      },
    )
  }

  createChangeRequest = (
    projectId,
    environmentId,
    flag,
    projectFlag,
    environmentFlag,
    segmentOverrides,
    changeRequest,
    commit,
    mode,
  ) => {
    AppActions.editFeatureMv(
      projectId,
      Object.assign({}, projectFlag, flag, {
        multivariate_options:
          flag.multivariate_options &&
          flag.multivariate_options.map((v) => {
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
      (newProjectFlag) => {
        AppActions.editEnvironmentFlagChangeRequest(
          projectId,
          environmentId,
          flag,
          newProjectFlag,
          {
            ...environmentFlag,
            multivariate_feature_state_values: flag.multivariate_options,
          },
          segmentOverrides,
          changeRequest,
          commit,
          mode,
        )
      },
    )
  }

  removeFlag = (projectId, flag) => {
    AppActions.removeFlag(projectId, flag)
  }

  render() {
    return this.props.children(
      {
        ...this.state,
      },
      {
        createChangeRequest: this.createChangeRequest,
        createFlag: this.createFlag,
        editFeatureSegments: this.editFeatureSegments,
        editFeatureSettings: this.editFeatureSettings,
        editFeatureValue: this.editFeatureValue,
        environmentHasFlag: FeatureListStore.hasFlagInEnvironment,
        removeFlag: this.removeFlag,
        toggleFlag: this.toggleFlag,
      },
    )
  }
}

FeatureListProvider.propTypes = {
  children: OptionalFunc,
  onError: OptionalFunc,
  onSave: OptionalFunc,
}

module.exports = FeatureListProvider
