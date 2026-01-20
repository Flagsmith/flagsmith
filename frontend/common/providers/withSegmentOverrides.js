import data from 'common/data/base/_data'
import ProjectStore from 'common/stores/project-store'
import FeatureListStore from 'common/stores/feature-list-store'
import { mergeChangeSets } from 'common/services/useChangeRequest'

export default (WrappedComponent) => {
  class HOC extends React.Component {
    static displayName = 'withFoo'

    constructor(props) {
      super(props)
      ES6Component(this)
      this.listenTo(FeatureListStore, 'saved', () => {
        this.getOverrides()
      })
      this.state = {}
    }

    componentDidMount() {
      this.getOverrides()
    }

    componentDidUpdate(prevProps, prevState, snapshot) {
      if (prevProps.environmentId !== this.props.environmentId) {
        this.getOverrides()
      }
    }

    getOverrides = () => {
      if (this.props.projectFlag) {
        //todo: migrate to useSegmentFeatureState
        const projectId = this.props.projectFlag.project
        Promise.all([
          data.get(
            `${
              Project.api
            }features/feature-segments/?environment=${ProjectStore.getEnvironmentIdFromKey(
              this.props.environmentId,
            )}&feature=${this.props.projectFlag.id}`,
          ),
          data.get(
            `${
              Project.api
            }features/featurestates/?environment=${ProjectStore.getEnvironmentIdFromKey(
              this.props.environmentId,
            )}&feature=${this.props.projectFlag.id}`,
          ),
          this.props.changeRequest?.change_sets
            ? data.get(
                `${Project.api}projects/${projectId}/segments/?page_size=1000`,
              )
            : Promise.resolve({ results: [] }),
        ]).then(([res, res2, segmentsRes]) => {
          const results = res.results
          const featureStates = res2.results
          const environmentOverride = res2.results.find(
            (v) => !v.feature_segment && !v.identity,
          )
          _.each(featureStates, (f) => {
            if (f.feature_segment) {
              const index = _.findIndex(results, { id: f.feature_segment })
              if (index !== -1) {
                results[index].value = Utils.featureStateToValue(
                  f.feature_state_value,
                )
                results[index].enabled = f.enabled
                results[index].feature_segment_value = f
                const multiVariates =
                  res2 &&
                  res2.results.find(
                    (mv) => mv.feature_segment === f.feature_segment,
                  )
                results[index].multivariate_feature_state_values =
                  (multiVariates &&
                    multiVariates.multivariate_feature_state_values) ||
                  []
                results[index].multivariate_options =
                  f.multivariate_feature_state_values
              }
            }
          })

          let segmentOverrides
          if (this.props.changeRequest?.change_sets) {
            // Add changesets to existing segment overrides
            const mergedFeatureStates = mergeChangeSets(
              this.props.changeRequest.change_sets,
              featureStates,
              this.props.changeRequest.conflicts,
            )

            // Get segment IDs marked for deletion
            const segmentIdsToDelete =
              this.props.changeRequest.change_sets?.flatMap(
                (changeSet) => changeSet.segment_ids_to_delete_overrides || [],
              ) || []

            segmentOverrides = results.map((currentSegmentOverride) => {
              const changedFeatureState = mergedFeatureStates.find(
                (featureState) =>
                  featureState.feature_segment?.segment ===
                  currentSegmentOverride.segment,
              )

              // Any segment_ids_to_delete_overrides should be marked as toRemove
              const toRemove = segmentIdsToDelete.includes(
                currentSegmentOverride.segment,
              )

              if (changedFeatureState) {
                return {
                  ...currentSegmentOverride,
                  ...changedFeatureState,
                  id: changedFeatureState.id || currentSegmentOverride.id,
                  is_feature_specific:
                    changedFeatureState.feature_segment?.is_feature_specific,
                  multivariate_options:
                    changedFeatureState.multivariate_feature_state_values || [],
                  priority: changedFeatureState.feature_segment?.priority || 0,
                  segment: changedFeatureState.feature_segment?.segment,
                  segment_name:
                    changedFeatureState.feature_segment?.segment_name ||
                    currentSegmentOverride.segment_name,
                  toRemove,
                  uuid:
                    changedFeatureState.feature_segment?.uuid ||
                    currentSegmentOverride.uuid,
                  value: Utils.featureStateToValue(
                    changedFeatureState.feature_state_value,
                  ),
                }
              }

              return toRemove
                ? { ...currentSegmentOverride, toRemove }
                : currentSegmentOverride
            })

            // Add any new segment overrides from the changesets
            mergedFeatureStates
              .filter(
                (featureState) =>
                  !!featureState.feature_segment?.segment &&
                  !results.find(
                    (currentOverride) =>
                      currentOverride.segment ===
                      featureState.feature_segment.segment,
                  ),
              )
              .forEach((newFeatureState) => {
                // Look up segment metadata from segments API to get segment name
                const segmentMetadata = segmentsRes.results?.find(
                  (segment) =>
                    segment.id === newFeatureState.feature_segment?.segment,
                )

                segmentOverrides.push({
                  enabled: newFeatureState.enabled,
                  environment: newFeatureState.environment,
                  feature: newFeatureState.feature,
                  id: newFeatureState.id,
                  is_feature_specific:
                    newFeatureState.feature_segment?.is_feature_specific,
                  multivariate_options:
                    newFeatureState.multivariate_feature_state_values || [],
                  priority: newFeatureState.feature_segment?.priority || 0,
                  segment: newFeatureState.feature_segment?.segment,
                  segment_name:
                    newFeatureState.feature_segment?.segment_name ||
                    segmentMetadata?.name ||
                    'Unknown Segment',
                  uuid: newFeatureState.feature_segment?.uuid,
                  value: Utils.featureStateToValue(
                    newFeatureState.feature_state_value,
                  ),
                })
              })
          } else {
            segmentOverrides = results.concat(
              (this.props.newSegmentOverrides || []).map((v, i) => ({
                ...v,
              })),
            )
          }
          segmentOverrides = segmentOverrides.map((v, i) => ({
            ...v,
            originalPriority: i,
            priority: i,
          }))

          const originalSegmentOverrides = _.cloneDeep(segmentOverrides)
          this.setState({
            environmentVariations:
              environmentOverride &&
              environmentOverride.multivariate_feature_state_values &&
              environmentOverride.multivariate_feature_state_values,
            originalSegmentOverrides,
            segmentOverrides,
          })
        })
      }
    }

    onEnvironmentVariationsChange = (environmentVariations) => {
      this.setState({ environmentVariations })
    }

    removeMultivariateOption = (id) => {
      this.setState({
        segmentOverrides:
          this.state.segmentOverrides &&
          this.state.segmentOverrides.map((v) => ({
            ...v,
            multivariate_options:
              v.multivariate_options &&
              v.multivariate_options.filter(
                (m) => m.multivariate_feature_option !== id,
              ),
          })),
      })
    }

    updateSegments = (segmentOverrides) => this.setState({ segmentOverrides })

    render() {
      return (
        <WrappedComponent
          ref='wrappedComponent'
          updateSegments={this.updateSegments}
          onEnvironmentVariationsChange={this.onEnvironmentVariationsChange}
          removeMultivariateOption={this.removeMultivariateOption}
          {...this.props}
          {...this.state}
        />
      )
    }
  }

  return HOC
}
