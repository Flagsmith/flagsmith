// import propTypes from 'prop-types';
import React, { Component } from 'react';
import { SortableContainer, SortableElement } from 'react-sortable-hoc';
import ProjectStore from '../../common/stores/project-store';
import ValueEditor from './ValueEditor';
import VariationOptions from './mv/VariationOptions';
import FeatureListStore from '../../common/stores/feature-list-store';
import CreateSegmentModal from './modals/CreateSegment';
import SegmentSelect from "./SegmentSelect";
import JSONReference from "./JSONReference";
import ConfigProvider from 'common/providers/ConfigProvider';

const arrayMoveMutate = (array, from, to) => {
    array.splice(to < 0 ? array.length + to : to, 0, array.splice(from, 1)[0]);
};

const arrayMove = (array, from, to) => {
    array = array.slice();
    arrayMoveMutate(array, from, to);
    return array;
};
const SegmentOverrideInner = class Override extends React.Component {
    constructor(props) {
        super(props);
        this.state = {};
        ES6Component(this);
    }

    componentDidMount() {
        this.listenTo(FeatureListStore, 'saved', () => {
            this.setState({ changed: false });
        });
    }

    render() {
        const { controlValue, multivariateOptions, setVariations, disabled, value: v, onSortEnd, index, confirmRemove, toggle, setValue, name, readOnly } = this.props;

        const mvOptions = multivariateOptions && multivariateOptions.map((mv) => {
            const foundMv = v.multivariate_options && v.multivariate_options.find(v => v.multivariate_feature_option === mv.id);
            if (foundMv) {
                return foundMv;
            }
            return {
                percentage_allocation: 0,
                multivariate_feature_option: mv.id,
            };
        });
        const changed = !v.id || this.state.changed;
        const showValue = !(multivariateOptions && multivariateOptions.length);
        const controlPercent = Utils.calculateControl(mvOptions);
        const invalid = !!multivariateOptions && multivariateOptions.length && controlPercent < 0;
        if (!v || v.toRemove) {
            if (this.props.id) {
                return (
                    <div>
                        You have removed this segment override, click save to confirm your changes.
                    </div>
                );
            }
            return <div/>;
        }
        return (
            <div data-test={`segment-override-${index}`} style={{ zIndex: 9999999999 }} className={`segment-overrides mb-2${this.props.id ? '' : ' panel panel-without-heading panel--draggable'}`}>
                <Row className="panel-content" space>
                    <div
                      className="flex flex-1 text-left"
                    >
                        <strong>
                            {name || v.segment_name}
                            {v.is_feature_specific && (
                            <div className="unread ml-2 px-2">
                                        Feature-Specific
                            </div>
                            )}
                            {changed && (
                            <div className="unread ml-2 px-2">
                                        Unsaved
                            </div>
                            )}
                        </strong>
                    </div>
                    <div>
                        <Row>
                            <Column>
                                <div>
                                    <Switch
                                      data-test={`segment-override-toggle-${index}`}
                                      disabled={disabled}
                                      checked={v.enabled}
                                      onChange={(v) => {
                                          if (!readOnly) {
                                              this.setState({ changed: true });
                                              toggle(v);
                                          }
                                      }}
                                    />
                                </div>
                            </Column>

                            {/* Input to adjust order without drag for E2E */}
                            {E2E && (
                            <input
                              readOnly={readOnly}
                              data-test={`sort-${index}`}
                              onChange={(e) => {
                                  this.setState({ changed: true });
                                  onSortEnd({ oldIndex: index, newIndex: parseInt(Utils.safeParseEventValue(e)) });
                              }}
                              type="text"
                            />
                            )}

                            {!readOnly && (
                            <button
                              disabled={disabled}
                              id="remove-feature"
                              onClick={confirmRemove}
                              className="btn btn--with-icon"
                            >
                                <RemoveIcon/>
                            </button>
                            )}
                            {this.props.showEditSegment && (
                                <ButtonLink
                                    target="_blank"
                                    href={`${document.location.origin}/project/${this.props.projectId}/environment/${this.props.environmentId}/segments?id=${v.segment}`}
                                    className="ml-2">
                                    Edit Segment
                                </ButtonLink>
                            )}
                        </Row>
                    </div>
                </Row>

                <div className="mx-2 text-left pb-2">

                    {showValue ? (
                            <>
                                <label>
                                    Value (optional)
                                </label>
                                <ValueEditor
                                  readOnly={readOnly}
                                  disabled={readOnly}

                                  value={v.value}
                                  data-test={`segment-override-value-${index}`}
                                  onChange={readOnly ? null : (e) => {
                                      this.setState({ changed: true });
                                      setValue(Utils.getTypedValue(Utils.safeParseEventValue(e)));
                                  }}
                                  placeholder="Value e.g. 'big' "
                                />
                            </>
                    ) : (
                            <>
                                <label>
                                    Segment Control Value - {controlPercent}%
                                </label>
                                <ValueEditor
                                  value={v.value}
                                  data-test={`segment-override-value-${index}`}
                                  disabled={true}
                                  placeholder="Value e.g. 'big' "
                                />
                            </>
                    )}
                    {!!controlValue && (!multivariateOptions || !multivariateOptions.length) && (
                    <div className="mt-2 mb-3 text-right">
                        <ButtonLink
                          className="text-primary" onClick={() => {
                              this.setState({ changed: true });
                              setValue(Utils.getTypedValue(Utils.safeParseEventValue(controlValue)));
                          }}
                        >
                            <div className="text-primary text-small">
                                        Copy from Environment Value
                            </div>
                        </ButtonLink>
                    </div>
                    )}


                    {(
                        <div>
                            <FormGroup className="mb-4">
                                <VariationOptions
                                  preventRemove
                                  readOnlyValue
                                  disabled={readOnly}
                                  controlValue={controlValue}
                                  variationOverrides={mvOptions}
                                  multivariateOptions={multivariateOptions.map((mv) => {
                                      const foundMv = v.multivariate_options && v.multivariate_options.find(v => v.multivariate_feature_option === mv.id);
                                      if (foundMv) {
                                          return {
                                              ...mv,
                                              default_percentage_allocation: foundMv.percentage_allocation,
                                          };
                                      }
                                      return {
                                          ...mv,
                                          default_percentage_allocation: 0,
                                      };
                                  })}
                                  setVariations={(i, e, variationOverrides) => {
                                      setVariations(i, e, variationOverrides);
                                      this.setState({ changed: true });
                                  }}
                                  setValue={(i, e, variationOverrides) => {
                                      setVariations(i, e, variationOverrides);
                                      this.setState({ changed: true });
                                  }}
                                  updateVariation={(i, e, variationOverrides) => {
                                      setVariations(i, e, variationOverrides);
                                      this.setState({ changed: true });
                                  }}
                                  weightTitle="Override Weight %"
                                />
                            </FormGroup>
                        </div>
                        )}
                </div>
            </div>
        );
    }
};
const SegmentOverride = ConfigProvider(SortableElement(
    SegmentOverrideInner,
));
const SegmentOverrideListInner = ({ disabled, id, name, showEditSegment, environmentId, projectId, multivariateOptions, onSortEnd, items, controlValue, confirmRemove, toggle, setValue, setVariations, readOnly }) => {
    const InnerComponent = id || disabled ? SegmentOverrideInner : SegmentOverride;
    return (
        <div>
            {items.map((value, index) => (
                <>
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
                        key={value.segment.name}
                        index={index}
                        readOnly={readOnly}
                        value={value}
                        confirmRemove={() => confirmRemove(index)}
                        controlValue={controlValue}
                        toggle={() => toggle(index)}
                        setValue={(value) => {
                            setValue(index, value);
                        }}
                        setVariations={(i, override, mvOptions) => {
                            const newValue = _.cloneDeep(mvOptions);
                            newValue[i] = {
                                ...newValue[i],
                                percentage_allocation: override.default_percentage_allocation,
                            };
                            setVariations(index, newValue);
                        }}
                    />
                    <div className="text-left">
                        <JSONReference showNamesButton title={"Segment Override"} json={value}/>
                    </div>
                </>

            ))}

        </div>
    );
};

const SegmentOverrideList = SortableContainer(SegmentOverrideListInner);

class TheComponent extends Component {
    static displayName = 'TheComponent';

    static propTypes = {
    };

    constructor(props) {
        super(props);
        this.state = {};
    }

    addItem = () => {
        const value = (this.props.value || []).map(val => ({ ...val, priority: val.priority }));
        const matchingValue = value.find(v => v.segment === this.state.selectedSegment.value);
        if (matchingValue) {
            matchingValue.toRemove = false;
            this.props.onChange(value);
            return;
        }
        const newValue = {
            feature: this.props.feature,
            segment: this.state.selectedSegment.value,
            segment_name: this.state.selectedSegment.label,
            environment: ProjectStore.getEnvironmentIdFromKey(this.props.environmentId),
            priority: value.length,
            feature_segment_value: {
                enabled: false,
                feature: this.props.feature,
                environment: ProjectStore.getEnvironmentIdFromKey(this.props.environmentId),
                feature_segment: null,
                feature_state_value: Utils.valueToFeatureState(''),
            },
        };
        this.props.onChange([newValue].concat(value));
        this.setState({selectedSegment: null})
    }

    confirmRemove = (i) => {
        if (!this.props.value[i].id) {
            this.props.onChange(_.filter(this.props.value, (v, index) => index !== i).map((v, i) => ({
                ...v,
                priority: i,
            })));
            if (this.props.onRemove) {
                this.props.onRemove();
            }
            return;
        }
        this.setState({ isLoading: true });
        openConfirm(
            <h3>Delete Segment Override</h3>,
            <p>
                {'Are you sure you want to delete this segment override? This will be applied when you click Update Segment Overrides.'}
            </p>,
            () => {
                this.props.value[i].toRemove = true;
            },
            () => {
                this.setState({ isLoading: false });
            },
        );
    }

    setValue = (i, value) => {
        this.props.value[i].value = value;
        this.props.onChange(this.props.value);
    }

    setVariations = (i, value) => {
        this.props.value[i].multivariate_options = value;
        this.props.onChange(this.props.value);
    }

    toggle = (i) => {
        this.props.value[i].enabled = !this.props.value[i].enabled;
        this.props.onChange(this.props.value);
    }

    onSortEnd = ({ oldIndex, newIndex }) => {
        this.props.onChange(arrayMove(this.props.value, oldIndex, newIndex)
            .map((v, i) => ({
                ...v,
                priority: i,
            })));
    };

    render() {
        const { state: { isLoading }, props: { value, multivariateOptions } } = this;
        const filter = (segment) => {
                if (segment.feature && segment.feature !== this.props.feature) return false;
                if (this.props.id && (this.props.id !== segment.id)) return null;
                const foundSegment = _.find(value, v => v.segment === segment.id);
                return !value || (!foundSegment || (foundSegment && foundSegment.toRemove));
            }
        const InnerComponent = this.props.id || this.props.readOnly ? SegmentOverrideListInner : SegmentOverrideList;

        const visibleValues = value && value.filter((v)=>!v.toRemove);

        return (
            <div>

                <div className="text-center mt-2 mb-2">

                    {!this.props.id && !this.props.disableCreate && !this.props.showCreateSegment && !this.props.readOnly && (
                        <Flex className="text-left">
                            <SegmentSelect
                                projectId={this.props.projectId}
                                data-test="select-segment"
                                placeholder="Create a Segment Override..."
                                filter={filter}
                                value={this.state.selectedSegment}
                                onChange={selectedSegment => this.setState({ selectedSegment }, this.addItem)}
                            />
                        </Flex>
                    )}
                    {!this.props.showCreateSegment && !this.props.readOnly && !this.props.disableCreate &&  (
                        <div className="text-right">
                            <Button
                              className="mt-2" onClick={() => {
                                  this.setState({ selectedSegment: null });
                                  this.props.setShowCreateSegment(true);
                              }}
                            >
                            Create Feature-Specific Segment
                            </Button>
                        </div>
                    )}
                    {this.props.showCreateSegment && (
                        <div className="text-left panel--grey mt-2">
                            <CreateSegmentModal
                              onComplete={(segment) => {
                                  if (this.state.selectedSegment) {
                                      this.props.setShowCreateSegment(false);
                                  } else {
                                      this.props.setShowCreateSegment(false);
                                      this.setState({ selectedSegment: {label:segment.name, value:segment.id} }, this.addItem);
                                  }
                              }}
                              onCancel={() => {
                                  this.props.setShowCreateSegment(false);
                              }}
                              condensed
                              feature={this.props.feature}
                              environmentId={this.props.environmentId}
                              projectId={this.props.projectId}
                            />
                        </div>
                    )}
                    {visibleValues && !!visibleValues.length && !this.props.showCreateSegment && (
                        <div style={isLoading ? { opacity: 0.5 } : null} className="mt-4 overflow-visible">
                            {!this.props.id && (
                                <div>
                                    <div className="mb-4 text-left faint">
                                        Prioritise a segment override by dragging it to the top of the list.
                                    </div>
                                </div>
                            )}


                            {value && (
                                <>
                                    <InnerComponent
                                        disabled={isLoading || this.props.readOnly}
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
                                        items={value.map(v => (
                                            {
                                                ...v,
                                            }
                                        ))}
                                        onSortEnd={this.onSortEnd}
                                    />
                                    <div className="text-left mt-4">
                                        <JSONReference showNamesButton title={"Segment Overrides"} json={value}/>
                                    </div>
                                </>

                            )}
                        </div>
                    )}
                </div>
            </div>
        );
    }
}

export default TheComponent;
