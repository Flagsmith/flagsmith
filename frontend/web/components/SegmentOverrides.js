// import propTypes from 'prop-types';
import React, { Component, Fragment } from 'react'
import { SortableContainer, SortableElement } from 'react-sortable-hoc'
import ProjectStore from 'common/stores/project-store'
import ValueEditor from './ValueEditor'
import VariationOptions from './mv/VariationOptions'
import FeatureListStore from 'common/stores/feature-list-store'
import CreateSegmentModal from './modals/CreateSegment'
import SegmentSelect from './SegmentSelect'
import JSONReference from './JSONReference'
import ConfigProvider from 'common/providers/ConfigProvider'
import InfoMessage from './InfoMessage'
import Permission from 'common/providers/Permission'
import Constants from 'common/constants'
import Icon from './Icon'
import SegmentOverrideLimit from './SegmentOverrideLimit'
import { getStore } from 'common/store'
import { getEnvironment } from 'common/services/useEnvironment'

const arrayMoveMutate = (array, from, to) => {
  array.splice(to < 0 ? array.length + to : to, 0, array.splice(from, 1)[0])
}

const arrayMove = (array, from, to) => {
  array = array.slice()
  arrayMoveMutate(array, from, to)
  return array
}
const SegmentOverrideInner = class Override extends React.Component {
  constructor(props) {
    super(props)
    this.state = {}
    ES6Component(this)
  }

  componentDidMount() {
    this.listenTo(FeatureListStore, 'saved', () => {
      this.setState({ changed: false })
    })
  }

  render() {
    const {
      confirmRemove,
      controlValue,
      disabled,
      index,
      multivariateOptions,
      name,
      onSortEnd,
      projectFlag,
      projectId,
      readOnly,
      setSegmentEditId,
      setShowCreateSegment,
      setValue,
      setVariations,
      toggle,
      value: v,
    } = this.props

    const mvOptions =
      multivariateOptions &&
      multivariateOptions.map((mv) => {
        const foundMv =
          v.multivariate_options &&
          v.multivariate_options.find(
            (v) => v.multivariate_feature_option === mv.id,
          )
        if (foundMv) {
          return foundMv
        }
        return {
          multivariate_feature_option: mv.id,
          percentage_allocation: 0,
        }
      })
    const changed = !v.id || this.state.changed
    const showValue = !(multivariateOptions && multivariateOptions.length)
    const controlPercent = Utils.calculateControl(mvOptions)
    if (!v || v.toRemove) {
      if (this.props.id) {
        return (
          <div>
            You have removed this segment override, click save to confirm your
            changes.
          </div>
        )
      }
      return <div />
    }
    return (
      <div
        data-test={`segment-override-${index}`}
        style={{ zIndex: 9999999999 }}
        className={`segment-overrides mb-2${
          this.props.id
            ? ''
            : ' panel panel-without-heading panel--draggable p-3'
        }`}
      >
        <Row className='panel-content p-0' space>
          <div className='flex flex-1 text-left'>
            {this.props.id ? (
              <>
                <Row className='font-weight-medium text-dark mb-1'>
                  {projectFlag.description ? (
                    <Tooltip
                      title={
                        <Row>
                          {projectFlag.name}
                          <span className={'ms-1'}></span>
                          <Icon name='info-outlined' />
                        </Row>
                      }
                    >
                      {projectFlag.description}
                    </Tooltip>
                  ) : (
                    projectFlag.name
                  )}
                  {v.is_feature_specific && (
                    <div className='chip chip--xs ml-2'>Feature-Specific</div>
                  )}
                  {changed && <div className='chip chip--xs ml-2'>Unsaved</div>}
                </Row>
                <div className='list-item-footer faint'>
                  <Row>
                    <div>
                      Created{' '}
                      {moment(projectFlag.created_date).format(
                        'Do MMM YYYY HH:mma',
                      )}
                    </div>
                  </Row>
                </div>
              </>
            ) : (
              <Row className='font-weight-medium text-dark'>
                {name || v.segment_name}
                {v.is_feature_specific && (
                  <div className='chip chip--xs ml-2'>Feature-Specific</div>
                )}
                {changed && <div className='chip chip--xs ml-2'>Unsaved</div>}
              </Row>
            )}
          </div>
          <div>
            <Row className='gap-3'>
              <Tooltip
                title={
                  <label className='cols-sm-2 control-label mb-0 ml-3'>
                    <Icon name='info-outlined' />
                  </label>
                }
              >
                Set the Feature state to On or Off for Identities in this
                Segment
              </Tooltip>
              <Switch
                data-test={`segment-override-toggle-${index}`}
                disabled={disabled}
                checked={v.enabled}
                onChange={(v) => {
                  if (!readOnly) {
                    this.setState({ changed: true })
                    toggle(v)
                  }
                }}
              />

              {/* Input to adjust order without drag for E2E */}
              {E2E && (
                <input
                  readOnly={readOnly}
                  data-test={`sort-${index}`}
                  onChange={(e) => {
                    this.setState({ changed: true })
                    onSortEnd({
                      newIndex: parseInt(Utils.safeParseEventValue(e)),
                      oldIndex: index,
                    })
                  }}
                  type='text'
                />
              )}
              <Row className='gap-2'>
                <Permission
                  id={projectId}
                  permission={'MANAGE_SEGMENTS'}
                  level={'project'}
                >
                  {({ permission }) =>
                    Utils.renderWithPermission(
                      permission,
                      Constants.projectPermissions('Manage Segments'),
                      <>
                        {!v.id || v.is_feature_specific ? (
                          <Button
                            disabled={!permission}
                            onClick={() => {
                              setShowCreateSegment(true)
                              setSegmentEditId(v.segment)
                            }}
                            className='btn btn-with-icon'
                          >
                            <span className='no-pointer'>
                              <Icon name='edit' fill={'#656D7B'} width={20} />
                            </span>
                          </Button>
                        ) : (
                          <Button
                            theme='text'
                            disabled={!permission}
                            target='_blank'
                            href={`${document.location.origin}/project/${this.props.projectId}/environment/${this.props.environmentId}/segments?id=${v.segment}`}
                            className='btn btn-with-icon'
                          >
                            <span className='no-pointer'>
                              <Icon name='edit' fill={'#656D7B'} width={20} />
                            </span>
                          </Button>
                        )}
                      </>,
                    )
                  }
                </Permission>
                {!readOnly && (
                  <Button
                    disabled={disabled}
                    id='remove-feature'
                    onClick={confirmRemove}
                    className='btn btn-with-icon'
                  >
                    <span className='no-pointer'>
                      <Icon name='trash-2' fill={'#656D7B'} width={20} />
                    </span>
                  </Button>
                )}
              </Row>
            </Row>
          </div>
        </Row>

        <div className='text-left mt-2'>
          {showValue ? (
            <>
              <label>Value (optional)</label>
              <ValueEditor
                readOnly={readOnly}
                disabled={readOnly}
                value={v.value}
                data-test={`segment-override-value-${index}`}
                onChange={
                  readOnly
                    ? null
                    : (e) => {
                        this.setState({ changed: true })
                        setValue(
                          Utils.getTypedValue(Utils.safeParseEventValue(e)),
                        )
                      }
                }
                placeholder="Value e.g. 'big' "
              />
            </>
          ) : (
            <>
              <label>Segment Control Value - {controlPercent}%</label>
              <ValueEditor
                value={v.value}
                data-test={`segment-override-value-${index}`}
                placeholder="Value e.g. 'big' "
                disabled={readOnly}
                onChange={
                  readOnly
                    ? null
                    : (e) => {
                        this.setState({ changed: true })
                        setValue(
                          Utils.getTypedValue(Utils.safeParseEventValue(e)),
                        )
                      }
                }
              />
            </>
          )}
          {!!controlValue &&
            (!multivariateOptions || !multivariateOptions.length) && (
              <div className='mt-2 text-right'>
                <Button
                  theme='text'
                  className='text-primary'
                  onClick={() => {
                    this.setState({ changed: true })
                    setValue(
                      Utils.getTypedValue(
                        Utils.safeParseEventValue(controlValue),
                      ),
                    )
                  }}
                >
                  <div className='text-primary text-small'>
                    Copy from Environment Value
                  </div>
                </Button>
              </div>
            )}

          {!!multivariateOptions?.length && (
            <div>
              <FormGroup className='mb-4'>
                <VariationOptions
                  preventRemove
                  readOnlyValue
                  disabled={readOnly}
                  controlValue={controlValue}
                  controlPercentage={controlPercent}
                  variationOverrides={mvOptions}
                  multivariateOptions={multivariateOptions.map((mv) => {
                    const foundMv =
                      v.multivariate_options &&
                      v.multivariate_options.find(
                        (v) => v.multivariate_feature_option === mv.id,
                      )
                    if (foundMv) {
                      return {
                        ...mv,
                        default_percentage_allocation:
                          foundMv.percentage_allocation,
                      }
                    }
                    return {
                      ...mv,
                      default_percentage_allocation: 0,
                    }
                  })}
                  setVariations={(i, e, variationOverrides) => {
                    setVariations(i, e, variationOverrides)
                    this.setState({ changed: true })
                  }}
                  setValue={(i, e, variationOverrides) => {
                    setVariations(i, e, variationOverrides)
                    this.setState({ changed: true })
                  }}
                  updateVariation={(i, e, variationOverrides) => {
                    setVariations(i, e, variationOverrides)
                    this.setState({ changed: true })
                  }}
                  weightTitle='Override Weight %'
                />
              </FormGroup>
            </div>
          )}
        </div>
      </div>
    )
  }
}
const SegmentOverride = ConfigProvider(SortableElement(SegmentOverrideInner))
const SegmentOverrideListInner = ({
  confirmRemove,
  controlValue,
  disabled,
  environmentId,
  id,
  items,
  multivariateOptions,
  name,
  onSortEnd,
  projectFlag,
  projectId,
  readOnly,
  setSegmentEditId,
  setShowCreateSegment,
  setValue,
  setVariations,
  showEditSegment,
  toggle,
}) => {
  const InnerComponent = id || disabled ? SegmentOverrideInner : SegmentOverride
  return (
    <div>
      {items.map((value, index) => (
        <Fragment key={value.segment.name}>
          <InnerComponent
            id={id}
            name={name}
            segment={value.segment}
            onSortEnd={onSortEnd}
            disabled={disabled}
            showEditSegment={showEditSegment}
            environmentId={environmentId}
            projectId={projectId}
            multivariateOptions={multivariateOptions}
            index={index}
            readOnly={readOnly}
            value={value}
            setSegmentEditId={setSegmentEditId}
            setShowCreateSegment={setShowCreateSegment}
            confirmRemove={() => confirmRemove(index)}
            controlValue={controlValue}
            toggle={() => toggle(index)}
            setValue={(value) => {
              setValue(index, value)
            }}
            setVariations={(i, override, mvOptions) => {
              const newValue = _.cloneDeep(mvOptions)
              newValue[i] = {
                ...newValue[i],
                percentage_allocation: override.default_percentage_allocation,
              }
              setVariations(index, newValue)
            }}
            projectFlag={projectFlag}
          />
          <div className='text-left'>
            <JSONReference
              showNamesButton
              title={'Segment Override'}
              json={value}
            />
          </div>
        </Fragment>
      ))}
    </div>
  )
}

const SegmentOverrideList = SortableContainer(SegmentOverrideListInner)

class TheComponent extends Component {
  static displayName = 'TheComponent'

  static propTypes = {}

  constructor(props) {
    super(props)
    this.state = { segmentEditId: undefined, totalSegmentOverrides: 0 }
  }
  componentDidMount() {
    getEnvironment(getStore(), {
      id: this.props.environmentId,
    }).then((res) => {
      this.setState({
        totalSegmentOverrides: res.data.total_segment_overrides,
      })
    })
  }

  addItem = () => {
    const value = (this.props.value || []).map((val) => ({
      ...val,
      priority: val.priority,
    }))
    const matchingValue = value.find(
      (v) => v.segment === this.state.selectedSegment.value,
    )
    if (matchingValue) {
      matchingValue.toRemove = false
      this.props.onChange(value)
      return
    }
    const newValue = {
      environment: ProjectStore.getEnvironmentIdFromKey(
        this.props.environmentId,
      ),
      feature: this.props.feature,
      feature_segment_value: {
        enabled: false,
        environment: ProjectStore.getEnvironmentIdFromKey(
          this.props.environmentId,
        ),
        feature: this.props.feature,
        feature_segment: null,
        feature_state_value: Utils.valueToFeatureState(
          `${this.props.controlValue || ''}`,
        ),
      },
      priority: value.length,
      segment: this.state.selectedSegment.value,
      segment_name: this.state.selectedSegment.label,
      value: `${this.props.controlValue || ''}`,
    }
    this.props.onChange([newValue].concat(value))
    this.setState({ selectedSegment: null })
  }

  confirmRemove = (i) => {
    if (!this.props.value[i].id) {
      this.props.onChange(
        _.filter(this.props.value, (v, index) => index !== i).map((v, i) => ({
          ...v,
          priority: i,
        })),
      )
      if (this.props.onRemove) {
        this.props.onRemove()
      }
      return
    }
    openConfirm({
      body: (
        <div>
          {
            'Are you sure you want to delete this segment override? This will be applied when you click Update Segment Overrides and cannot be undone.'
          }
        </div>
      ),
      destructive: true,
      onYes: () => {
        this.props.value[i].toRemove = true
        this.setState({ isLoading: false })
      },
      title: 'Delete Segment Override',
      yesText: 'Confirm',
    })
  }

  setValue = (i, value) => {
    this.props.value[i].value = value
    this.props.onChange(this.props.value)
  }

  setSegmentEditId = (id) => {
    this.setState({ segmentEditId: id })
  }

  setVariations = (i, value) => {
    this.props.value[i].multivariate_options = value
    this.props.onChange(this.props.value)
  }

  toggle = (i) => {
    this.props.value[i].enabled = !this.props.value[i].enabled
    this.props.onChange(this.props.value)
  }

  onSortEnd = ({ newIndex, oldIndex }) => {
    this.props.onChange(
      arrayMove(this.props.value, oldIndex, newIndex).map((v, i) => ({
        ...v,
        priority: i,
      })),
    )
  }

  render() {
    const {
      props: { multivariateOptions, value },
    } = this
    const filter = (segment) => {
      if (segment.feature && segment.feature !== this.props.feature)
        return false
      if (this.props.id && this.props.id !== segment.id) return null
      const foundSegment = _.find(value, (v) => v.segment === segment.id)
      return !value || !foundSegment || (foundSegment && foundSegment.toRemove)
    }
    const InnerComponent =
      this.props.id || this.props.readOnly
        ? SegmentOverrideListInner
        : SegmentOverrideList

    const visibleValues = value && value.filter((v) => !v.toRemove)

    const segmentOverrideLimitAlert = Utils.calculateRemainingLimitsPercentage(
      this.state.totalSegmentOverrides,
      ProjectStore.getMaxSegmentOverridesAllowed(),
    )

    const isLimitReached =
      segmentOverrideLimitAlert.percentage &&
      segmentOverrideLimitAlert.percentage >= 100
    return (
      <div>
        <Permission
          level='project'
          permission={'MANAGE_SEGMENTS'}
          id={this.props.projectId}
        >
          {({ permission: manageSegments }) => {
            return (
              <div className='mt-2 mb-2'>
                {!this.props.id &&
                  !this.props.disableCreate &&
                  !this.props.showCreateSegment &&
                  !this.props.readOnly && (
                    <Flex className='text-left'>
                      <SegmentSelect
                        disabled={!!isLimitReached}
                        projectId={this.props.projectId}
                        data-test='select-segment'
                        placeholder='Create a Segment Override...'
                        filter={filter}
                        value={this.state.selectedSegment}
                        onChange={(selectedSegment) =>
                          this.setState({ selectedSegment }, this.addItem)
                        }
                      />
                    </Flex>
                  )}
                {!this.props.showCreateSegment &&
                  !this.props.readOnly &&
                  !this.props.disableCreate && (
                    <div className='text-right'>
                      <Button
                        className='mt-4'
                        onClick={() => {
                          this.setState({ selectedSegment: null })
                          this.props.setShowCreateSegment(true)
                        }}
                        theme='outline'
                        disabled={!!isLimitReached || !manageSegments}
                      >
                        Create Feature-Specific Segment
                      </Button>
                    </div>
                  )}
                {this.props.showCreateSegment && !this.state.segmentEditId && (
                  <div className='create-segment-overrides'>
                    <CreateSegmentModal
                      onComplete={(segment) => {
                        this.props.setShowCreateSegment(false)
                        if (!this.state.selectedSegment) {
                          this.setState(
                            {
                              selectedSegment: {
                                label: segment.name,
                                value: segment.id,
                              },
                            },
                            this.addItem,
                          )
                        }
                      }}
                      onCancel={() => {
                        this.props.setShowCreateSegment(false)
                      }}
                      condensed
                      feature={this.props.feature}
                      environmentId={this.props.environmentId}
                      projectId={this.props.projectId}
                    />
                  </div>
                )}
                {this.props.showCreateSegment && this.state.segmentEditId && (
                  <CreateSegmentModal
                    className='my-2'
                    segment={this.state.segmentEditId}
                    isEdit
                    condensed
                    onComplete={() => {
                      this.setState({
                        segmentEditId: undefined,
                      })
                      this.props.setShowCreateSegment(false)
                    }}
                    onCancel={() => {
                      this.setState({ segmentEditId: undefined })
                      this.props.setShowCreateSegment(false)
                    }}
                    environmentId={this.props.environmentId}
                    projectId={this.props.projectId}
                  />
                )}
                {visibleValues &&
                  !!visibleValues.length &&
                  !this.props.showCreateSegment && (
                    <div className='overflow-visible'>
                      {!this.props.id && (
                        <div className='my-4'>
                          <InfoMessage className='mb-4 text-left faint'>
                            Segment overrides override the environment defaults,
                            prioritise them by dragging it to the top of the
                            list. Segment overrides will only apply when you
                            identify via the SDK, any identity overrides will
                            take priority.{' '}
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
                            id={this.props.environmentId}
                            maxSegmentOverridesAllowed={ProjectStore.getMaxSegmentOverridesAllowed()}
                          />
                        </div>
                      )}

                      {value && (
                        <>
                          <InnerComponent
                            disabled={this.props.readOnly}
                            id={this.props.id}
                            name={this.props.name}
                            controlValue={this.props.controlValue}
                            multivariateOptions={multivariateOptions}
                            confirmRemove={this.confirmRemove}
                            setVariations={this.setVariations}
                            toggle={this.toggle}
                            setValue={this.setValue}
                            readOnly={this.props.readOnly}
                            showEditSegment={this.props.showEditSegment}
                            environmentId={this.props.environmentId}
                            projectId={this.props.projectId}
                            setShowCreateSegment={
                              this.props.setShowCreateSegment
                            }
                            items={value.map((v) => ({
                              ...v,
                            }))}
                            setSegmentEditId={this.setSegmentEditId}
                            onSortEnd={this.onSortEnd}
                            projectFlag={this.props.projectFlag}
                          />
                          <div className='text-left mt-4'>
                            <JSONReference
                              showNamesButton
                              title={'Segment Overrides'}
                              json={value}
                            />
                          </div>
                        </>
                      )}
                    </div>
                  )}
              </div>
            )
          }}
        </Permission>
      </div>
    )
  }
}

export default TheComponent
