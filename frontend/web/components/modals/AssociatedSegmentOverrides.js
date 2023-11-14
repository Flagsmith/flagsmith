import React, { Component } from 'react'
import { groupBy } from 'lodash'
import _data from 'common/data/base/_data'
import ProjectStore from 'common/stores/project-store'
import withSegmentOverrides from 'common/providers/withSegmentOverrides'
import FeatureListStore from 'common/stores/feature-list-store'
import ConfigProvider from 'common/providers/ConfigProvider'
import SegmentOverrides from 'components/SegmentOverrides'
import FlagSelect from 'components/FlagSelect'
import InfoMessage from 'components/InfoMessage'
import EnvironmentSelect from 'components/EnvironmentSelect'
import SegmentOverrideLimit from 'components/SegmentOverrideLimit'
import { getStore } from 'common/store'
import { getEnvironment } from 'common/services/useEnvironment'

class TheComponent extends Component {
  state = {
    isLoading: true,
  }
  componentDidMount() {
    this.fetch()
  }
  fetch = () => {
    _data
      .get(
        `${Project.api}projects/${this.props.projectId}/segments/${this.props.id}/associated-features/`,
      )
      .then((v) =>
        Promise.all(
          v.results.map((result) =>
            _data
              .get(
                `${Project.api}projects/${this.props.projectId}/features/${result.feature}/`,
              )
              .then((feature) => {
                result.feature = feature
              }),
          ),
        )
          .then(() =>
            groupBy(v.results, (e) => {
              const env = ProjectStore.getEnvs().find(
                (v) => v.id === e.environment,
              )
              e.env = env
              return env && env.name
            }),
          )
          .then((v) => {
            if (v.undefined) {
              delete v.undefined
            }
            _.each(Object.keys(v), (key) => {
              v[key] = _.sortBy(v[key], (val) => val.feature.name)
            })
            const newItems = this.state.newItems || {}
            const selectedEnv =
              this.state.selectedEnv || ProjectStore.getEnvs()[0].name
            newItems[selectedEnv] = (newItems[selectedEnv] || []).filter(
              (newItem) => {
                const existingSegmentOverride =
                  !!v[selectedEnv] &&
                  v[selectedEnv].find(
                    (s) => newItem.feature.id === s.feature.id,
                  )
                return !existingSegmentOverride
              },
            )
            this.setState({
              isLoading: false,
              newItems,
              results: v,
              selectedEnv,
            })
          }),
      )
  }

  addItem = (item) => {
    const newItems = this.state.newItems || {}
    newItems[this.state.selectedEnv] = newItems[this.state.selectedEnv] || []
    newItems[this.state.selectedEnv].unshift(item)
    this.setState({
      newItems,
    })
  }

  render() {
    const results = this.state.results
    const newItems = this.state.newItems
    const selectedNewResults =
      (newItems && newItems[this.state.selectedEnv]) || []

    const environment = ProjectStore.getEnvs().find(
      (v) => v.name === this.state.selectedEnv,
    )
    const selectedResults = selectedNewResults.concat(
      (results && results[this.state.selectedEnv]) || [],
    )
    const addOverride = (
      <div style={{ width: 300 }} className='my-4'>
        <WrappedSegmentOverrideAdd
          onSave={this.fetch}
          addItem={this.addItem}
          feature={this.props.feature}
          selectedResults={selectedResults}
          ignoreFlags={
            selectedResults && selectedResults.map((v) => v.feature.id)
          }
          id={this.props.id}
          projectId={this.props.projectId}
          environmentId={this.state.selectedEnv}
          readOnly={this.props.readOnly}
        />
      </div>
    )

    return this.state.isLoading ? (
      <div className='text-center'>
        <Loader />
      </div>
    ) : (
      <div className='mt-4'>
        <InfoMessage>
          This shows the list of segment overrides associated with this segment.
          <br />
          Segment overrides will only apply when you identify via the SDK.{' '}
          <a
            target='_blank'
            href='https://docs.flagsmith.com/basic-features/managing-segments'
            rel='noreferrer'
          >
            Check the Docs for more details
          </a>
          .
        </InfoMessage>
        <SegmentOverrideLimit
          id={environment.api_key}
          maxSegmentOverridesAllowed={ProjectStore.getMaxSegmentOverridesAllowed()}
        />
        <div>
          <InputGroup
            component={
              <EnvironmentSelect
                projectId={this.props.projectId}
                value={environment.api_key}
                onChange={(selectedEnv) =>
                  this.setState({
                    selectedEnv: ProjectStore.getEnvs().find(
                      (v) => v.api_key === selectedEnv,
                    ).name,
                  })
                }
              />
            }
            title='Environment'
          />
          <PanelSearch
            searchPanel={addOverride}
            search={this.state.search}
            onChange={(search) => this.setState({ search })}
            filterRow={(row, search) =>
              row.feature.name.toLowerCase().includes(search.toLowerCase())
            }
            className='no-pad panel-override'
            title='Associated Features'
            items={selectedResults}
            renderNoResults={
              <Panel className='no-pad' title='Associated Features'>
                {addOverride}
                <div className='p-2 text-center'>
                  There are no segment overrides in this environment
                </div>
              </Panel>
            }
            renderRow={(v) => (
              <div key={v.feature.id} className='list-item-override p-3 mb-4'>
                <div
                  onClick={() => {
                    // window.open(`${document.location.origin}/project/${this.props.projectId}/environment/${v.env.api_key}/features?feature=${v.feature.id}&tab=1`)
                  }}
                >
                  <WrappedSegmentOverrides
                    onSave={this.fetch}
                    projectFlag={v.feature}
                    newSegmentOverrides={v.newSegmentOverrides}
                    onRemove={() => {
                      if (v.newSegmentOverrides) {
                        newItems[this.state.selectedEnv] = newItems[
                          this.state.selectedEnv
                        ].filter((x) => x !== v)
                        this.setState({
                          newItems,
                        })
                      }
                    }}
                    id={this.props.id}
                    projectId={this.props.projectId}
                    environmentId={v.env.api_key}
                    readOnly={this.props.readOnly}
                  />
                </div>
              </div>
            )}
          />
        </div>
      </div>
    )
  }
}

class UncontrolledSegmentOverrides extends Component {
  constructor(props) {
    super(props)
    this.state = {
      value: this.props.value,
    }
  }

  onChange = (value) => {
    this.setState({ value })
    this.props.onChange(value)
  }

  render() {
    return (
      <SegmentOverrides
        {...this.props}
        disableCreate
        onChange={this.onChange}
        value={this.state.value}
      />
    )
  }
}

export default class SegmentOverridesInner extends Component {
  state = {}

  componentDidMount() {
    ES6Component(this)
  }

  openPriorities = () => {
    const {
      environmentId,
      originalSegmentOverrides,
      projectFlag,
      projectId,
      segmentOverrides,
      updateSegments,
    } = this.props
    const arrayMoveMutate = (array, from, to) => {
      array.splice(to < 0 ? array.length + to : to, 0, array.splice(from, 1)[0])
    }
    const arrayMove = (array, from, to) => {
      array = array.slice()
      arrayMoveMutate(array, from, to)
      return array
    }
    const overrides = originalSegmentOverrides
      .filter((v) => v.segment !== segmentOverrides[0].segment)
      .concat([segmentOverrides[0]])
    openModal2(
      'Edit Segment Override Priorities',
      <div>
        <UncontrolledSegmentOverrides
          feature={projectFlag.id}
          readOnly
          projectId={projectId}
          multivariateOptions={_.cloneDeep(projectFlag.multivariate_options)}
          environmentId={environmentId}
          value={arrayMove(
            overrides,
            overrides.length - 1,
            overrides[overrides.length - 1].priority,
          )}
          controlValue={projectFlag.feature_state_value}
          onChange={updateSegments}
        />
        <div className='text-right'>
          <Button
            onClick={() => {
              closeModal2()
            }}
          >
            Done
          </Button>
        </div>
      </div>,
    )
  }

  render() {
    const {
      environmentId,
      id,
      originalSegmentOverrides,
      projectFlag,
      projectId,
      readOnly,
      segmentOverrides,
      updateSegments,
    } = this.props

    return (
      <FeatureListProvider>
        {({}, { editFeatureSegments, isSaving }) => {
          const save = () => {
            FeatureListStore.isSaving = true
            FeatureListStore.trigger('change')
            !isSaving &&
              editFeatureSegments(
                projectId,
                environmentId,
                projectFlag,
                projectFlag,
                {},
                segmentOverrides,
                () => {
                  toast('Segment override saved')
                  this.setState({ isSaving: false })
                  this.props.onSave()
                },
              )
            this.setState({ isSaving: true })
          }
          const segmentOverride =
            segmentOverrides && segmentOverrides.filter((v) => v.segment === id)
          if (!segmentOverrides) return null
          return (
            <div>
              {originalSegmentOverrides.length > 1 && (
                <div style={{ width: 165 }}>
                  <Tooltip
                    title={
                      <div className='chip mt-2'>
                        Priority:{' '}
                        {segmentOverride && segmentOverride[0].priority + 1} of{' '}
                        {originalSegmentOverrides.length}
                        <a
                          href='#'
                          className='ml-2'
                          onClick={this.openPriorities}
                        >
                          Edit
                        </a>
                      </div>
                    }
                  >
                    If a user belongs to more than 1 segment, overrides are
                    determined by this priority.
                  </Tooltip>
                </div>
              )}

              <SegmentOverrides
                projectFlag={projectFlag}
                feature={projectFlag.id}
                id={id}
                name=' '
                disableCreate
                projectId={projectId}
                onRemove={this.props.onRemove}
                multivariateOptions={_.cloneDeep(
                  projectFlag.multivariate_options,
                )}
                environmentId={environmentId}
                value={segmentOverride}
                controlValue={projectFlag.feature_state_value}
                onChange={updateSegments}
                readOnly={readOnly}
              />
              <div className='text-right'>
                {!readOnly && (
                  <Button disabled={this.state.isSaving} onClick={save}>
                    {this.state.isSaving ? 'Saving' : 'Save'}
                  </Button>
                )}
              </div>
            </div>
          )
        }}
      </FeatureListProvider>
    )
  }
}

class SegmentOverridesInnerAdd extends Component {
  state = { totalSegmentOverrides: 0 }

  fetchTotalSegmentOverrides() {
    const { environmentId } = this.props
    const env = ProjectStore.getEnvs().find((v) => v.name === environmentId)

    if (!env) {
      return
    }

    const id = env.api_key

    getEnvironment(getStore(), { id }).then((res) => {
      this.setState({
        totalSegmentOverrides: res.data.total_segment_overrides,
      })
    })
  }

  componentDidMount() {
    ES6Component(this)
    this.fetchTotalSegmentOverrides()
  }

  componentDidUpdate(prevProps) {
    if (prevProps.environmentId !== this.props.environmentId) {
      this.fetchTotalSegmentOverrides()
    }
  }
  render() {
    const { environmentId, id, ignoreFlags, projectId, readOnly } = this.props
    const addValue = (featureId, feature) => {
      const env = ProjectStore.getEnvs().find((v) => v.name === environmentId)
      const item = {
        env,
        environment: environmentId,
        feature,
        isNew: true,
        newSegmentOverrides: [
          {
            environment: env.id,
            feature: featureId,
            feature_segment_value: {
              enabled: false,
              environment: env.id,
              feature: featureId,
              feature_segment: null,
              feature_state_value: Utils.valueToFeatureState(''),
            },
            priority: 999,
            segment: id,
          },
        ],
      }
      this.props.addItem(item)
      // const newValue = ;
      // updateSegments(segmentOverrides.concat([newValue]))
    }
    const segmentOverrideLimitAlert =
      this.state.totalSegmentOverrides >=
      ProjectStore.getMaxSegmentOverridesAllowed()

    return (
      <FeatureListProvider>
        {() => {
          return (
            <div className='mt-2'>
              {!readOnly && (
                <FlagSelect
                  disabled={!!segmentOverrideLimitAlert}
                  onlyInclude={this.props.feature}
                  placeholder='Create a Segment Override...'
                  projectId={projectId}
                  ignore={ignoreFlags}
                  onChange={addValue}
                />
              )}
            </div>
          )
        }}
      </FeatureListProvider>
    )
  }
}

const WrappedSegmentOverrides = withSegmentOverrides(SegmentOverridesInner)

const WrappedSegmentOverrideAdd = withSegmentOverrides(SegmentOverridesInnerAdd)

module.exports = ConfigProvider(TheComponent)
