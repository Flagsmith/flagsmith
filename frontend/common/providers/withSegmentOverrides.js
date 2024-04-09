import data from 'common/data/base/_data'
import ProjectStore from 'common/stores/project-store'
import FeatureListStore from 'common/stores/feature-list-store'

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
        ]).then(([res, res2]) => {
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
          const resResults = res.results || []
          const segmentOverrides = results.concat(
            (this.props.newSegmentOverrides || []).map((v, i) => ({
              ...v,
              priority: resResults.length + i,
            })),
          )
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
