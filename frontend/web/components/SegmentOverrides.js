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
import Tooltip from './Tooltip'
import SegmentsIcon from './svg/SegmentsIcon'
import SegmentOverrideActions from './SegmentOverrideActions'

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
        className={`segment-overrides mb-3${
          this.props.id
            ? ''
            : ' panel user-select-none panel-without-heading panel--draggable pb-0'
        }`}
      >
        <Row className='p-0 table-header px-3 py-1' space>
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
              <Row className='fs-small'>
                <SegmentsIcon
                  className='opacity-50'
                  fill='#1a2634'
                  width={16}
                  height={16}
                />
                <span className='ms-2 fw-bold text-body mb-0'>
                  {name || v.segment_name}
                </span>
                {v.is_feature_specific && (
                  <div className='chip chip--xs ml-2'>Feature-Specific</div>
                )}
                {changed && <div className='chip chip--xs ml-2'>Unsaved</div>}
              </Row>
            )}
          </div>
          <div>
            <Row className='gap-3'>
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
                        <SegmentOverrideActions
                          onCopyValue={() => {
                            this.setState({ changed: true })
                            setValue(
                              Utils.getTypedValue(
                                Utils.safeParseEventValue(controlValue),
                              ),
                            )
                          }}
                          canCopyValue={
                            !!controlValue &&
                            (!multivariateOptions ||
                              !multivariateOptions.length)
                          }
                          canRemove={!disabled && !readOnly}
                          onRemove={confirmRemove}
                          onEdit={() => {
                            if (v.is_feature_specific) {
                              setShowCreateSegment(true)
                              setSegmentEditId(v.segment)
                            } else {
                              window.open(
                                `${document.location.origin}/project/${this.props.projectId}/segments?id=${v.segment}`,
                                '_blank',
                              )
                            }
                          }}
                          canEdit={permission}
                        />
                      </>,
                    )
                  }
                </Permission>
              </Row>
            </Row>
          </div>
        </Row>
        <div className='d-flex px-3 mt-2'>
          <div>
            <div className='me-4'>
              <Tooltip
                title={
                  <div className='label-switch justify-content-center d-flex align-items-center gap-1'>
                    <span>Enabled</span> <Icon name='info-outlined' />
                  </div>
                }
              >
                Controls whether the feature is enabled for users belonging to
                this segment.
              </Tooltip>
            </div>
            <Switch
              className='mt-4'
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
          </div>
          {showValue ? (
            <>
              <div className='flex-fill overflow-hidden'>
                <label>Value</label>
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
              </div>
            </>
          ) : (
            <div className='flex-1 flex-column'>
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
            </div>
          )}
        </div>
        {!!multivariateOptions?.length && (
          <div className='px-3'>
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
          </div>
        )}
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
    this.props.onChange(value.concat([newValue]))
    this.setState({ selectedSegment: null })
    setTimeout(() => {
      const container = document.querySelector('.tabs-content .tab-active')
      if (container) {
        container.scrollTop = container.scrollHeight
      }
    }, 0)
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
          {`Are you sure you want to delete this segment override?${
            this.props.is4Eyes
              ? ''
              : ' This will be applied when you click Update Segment Overrides and cannot be undone.'
          }`}
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
                          <InfoMessage collapseId={'segment-overrides'} className='mb-4 text-left faint'>
                            Segment overrides override the environment defaults,
                            prioritise them by dragging it to the top of the
                            list. Segment overrides will only apply when you
                            identify via the SDK, any identity overrides will
                            take priority.{' '}
                      <a
                        target='_blank'
                        href='https://docs.flagsmith.com/basic-features/segments'
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
                      shouldCancelStart={(e) => {
                        const tagName = e.target.tagName.toLowerCase()

                        // Check if the clicked element is a button, input, or textarea
                        if (
                          tagName === 'input' ||
                          tagName === 'textarea' ||
                          tagName === 'button'
                        ) {
                          return true // Cancel sorting for inputs, buttons, etc.
                        }

                        // Cancel if the clicked element has class 'feature-action__list'
                        if (
                          e.target.closest('.feature-action__item') || // Checks for parent elements with the class
                          e.target.closest('.hljs')
                        ) {
                          return true // Cancel sorting if the target or parent has these classes
                        }

                        // Otherwise, allow sorting
                        return false
                      }} // Here we pass the function to prevent sorting in certain cases
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
                      setShowCreateSegment={this.props.setShowCreateSegment}
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
      </div>
    )
  }
}

export default TheComponent
