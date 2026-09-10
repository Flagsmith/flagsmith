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
              (v) => v.multivariate_feature_option === mv.id,
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
    AppActions.createFlag(
      projectId,
      environmentId,
      {
        ...flag,
        multivariate_options: flag.multivariate_options?.map((v, i) => ({
          ...v,
          key: v.key || Utils.getDefaultVariantKey(i),
        })),
      },
      segmentOverrides,
    )
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
          flag.multivariate_options.map((v, i) => {
            const matchingProjectVariate =
              (projectFlag.multivariate_options &&
                projectFlag.multivariate_options.find((p) => p.id === v.id)) ||
              v
            return {
              ...v,
              default_percentage_allocation:
                matchingProjectVariate.default_percentage_allocation,
              key: v.key || Utils.getDefaultVariantKey(i),
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
  ) => {
    // Variations belong to the feature, so a request scoped to one environment
    // cannot carry them. saveVariationValues is where they change. Take the ids
    // from what is stored and the weights from what the user edited.
    const weightedVariations = (projectFlag.multivariate_options || []).map(
      (option) => {
        const edited = flag.multivariate_options?.find(
          (v) => v.id === option.id,
        )
        return {
          ...option,
          default_percentage_allocation:
            edited?.default_percentage_allocation ??
            option.default_percentage_allocation,
        }
      },
    )

    AppActions.editEnvironmentFlagChangeRequest(
      projectId,
      environmentId,
      flag,
      projectFlag,
      {
        ...environmentFlag,
        multivariate_feature_state_values: Utils.mapMvOptionsToStateValues(
          weightedVariations,
          environmentFlag.multivariate_feature_state_values,
        ),
      },
      segmentOverrides,
      changeRequest,
      commit,
    )
  }

  // The deliberate variation save: applies values, labels, additions and
  // removals to the feature, and so to every environment at once.
  saveVariationValues = (projectId, flag, projectFlag, onComplete) => {
    AppActions.editFeatureMv(
      projectId,
      Object.assign({}, projectFlag, {
        multivariate_options: flag.multivariate_options?.map((v, i) => ({
          ...v,
          key: v.key || Utils.getDefaultVariantKey(i),
        })),
      }),
      onComplete,
    )
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
        saveVariationValues: this.saveVariationValues,
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

export default FeatureListProvider
