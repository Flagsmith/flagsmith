// import propTypes from 'prop-types';
import React, { Component } from 'react';
import { SortableContainer, SortableElement } from 'react-sortable-hoc';
import _data from '../../common/data/base/_data';
import ProjectStore from '../../common/stores/project-store';
import ValueEditor from './ValueEditor';
import VariationOptions from './mv/VariationOptions';
import FeatureListStore from '../../common/stores/feature-list-store';

const arrayMoveMutate = (array, from, to) => {
    array.splice(to < 0 ? array.length + to : to, 0, array.splice(from, 1)[0]);
};

const arrayMove = (array, from, to) => {
    array = array.slice();
    arrayMoveMutate(array, from, to);
    return array;
};
const SegmentOverrideInner =
    class Override extends React.Component {
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
                if(this.props.id) {
                    return <div>
                        You have removed this segment override, click save to confirm your changes.
                    </div>
                }
                return null;
            }
            return (
                <div data-test={`segment-override-${index}`} style={{ zIndex: 9999999999 }} className={"segment-overrides mb-2" + (this.props.id? "": " panel panel-without-heading panel--draggable")}>
                    <Row className="panel-content" space>
                        <div
                            className="flex flex-1 text-left"
                        >
                            <strong>
                                {name||v.segment.name}
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
                                                if(!readOnly) {
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
                                    value={v.value}
                                    data-test={`segment-override-value-${index}`}
                                    onChange={(e) => {
                                        this.setState({ changed: true });
                                        setValue(Utils.getTypedValue(Utils.safeParseEventValue(e)));
                                    }}
                                    placeholder="Value e.g. 'big' "
                                />
                            </>
                        ) : (
                            <>
                                <label>
                                    Control Value - {controlPercent}%
                                </label>
                                <ValueEditor
                                    value={v.value}
                                    data-test={`segment-override-value-${index}`}
                                    onChange={(e) => {
                                        this.setState({ changed: true });
                                        setValue(Utils.getTypedValue(Utils.safeParseEventValue(e)));
                                    }}
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
    }
const SegmentOverride = ConfigProvider(SortableElement(
    SegmentOverrideInner
))
;

const SegmentOverrideListInner = ({ disabled, id, name, multivariateOptions, onSortEnd, items, controlValue, confirmRemove, toggle, setValue, setVariations, readOnly }) => {
    const InnerComponent = id? SegmentOverrideInner : SegmentOverride;
    return (
        <div>
            {items.map((value, index) => (
                <InnerComponent
                    id={id}
                    name={name}
                    onSortEnd={onSortEnd}
                    disabled={disabled}
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
                        // multivariate_feature_option: 2228
                        // multivariate_feature_option_index: 0
                        // percentage_allocation: 100
                        const newValue = _.cloneDeep(mvOptions);
                        newValue[i] = {
                            ...newValue[i],
                            percentage_allocation: override.default_percentage_allocation,
                        };
                        setVariations(index, newValue);
                    }}
                />
            ))}
        </div>
    )
}

const SegmentOverrideList = SortableContainer(SegmentOverrideListInner);

class TheComponent extends Component {
    static displayName = 'TheComponent';

    static propTypes = {
    };

    constructor(props) {
        super(props);
        this.state = {};
        AppActions.getSegments(props.projectId, props.environmentId);
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
    }

    confirmRemove = (i) => {
        if (!this.props.value[i].id) {
            this.props.onChange(_.filter(this.props.value, (v, index) => index !== i).map((v, i) => ({
                ...v,
                priority: i,
            })));
            if(this.props.onRemove) {
                this.props.onRemove()
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
        const { state: { isLoading }, props: { value, segments, multivariateOptions } } = this;
        const segmentOptions = _.filter(
            segments, (segment) => {
                if(this.props.id && (this.props.id !== segment.id)) return null
                const foundSegment = _.find(value, v => v.segment === segment.id);
                return !value || (!foundSegment || (foundSegment && foundSegment.toRemove));
            },
        )
            .map(({ name: label, id: value }) => ({ value, label }));
        const InnerComponent = this.props.id ? SegmentOverrideListInner : SegmentOverrideList
        return (
            <div>

                <div className="text-center mt-2 mb-2">

                    {segments && !this.props.id && (
                        <Flex className="text-left">
                            <Select
                              data-test="select-segment"
                              placeholder="Create a Segment Override..."
                              value={this.state.selectedSegment}
                              onChange={selectedSegment => this.setState({ selectedSegment }, this.addItem)}
                              options={
                                    segmentOptions
                                }
                              styles={{
                                  control: base => ({
                                      ...base,
                                      '&:hover': { borderColor: '$bt-brand-secondary' },
                                      border: '1px solid $bt-brand-secondary',
                                  }),
                              }}
                            />
                        </Flex>
                    )}
                    {value && !!value.length && (
                        <div style={isLoading ? { opacity: 0.5 } : null} className="mt-4 overflow-visible">
                            {!this.props.id && (
                                <div>
                                    <Row className="mb-2">
                                        <div
                                            className="flex flex-1 text-left"
                                        >
                                            <label>Segment</label>
                                        </div>
                                        <Column className="text-right" style={{ width: 120 }}>
                                            <label>
                                                Value
                                            </label>
                                        </Column>
                                    </Row>
                                    <div className="mb-4 text-left faint">
                                        Prioritise a segment override by dragging it to the top of the list.
                                    </div>
                                </div>
                            )}


                            {value && (
                            <InnerComponent
                              disabled={isLoading}
                              id={this.props.id}
                              name={this.props.name}
                              controlValue={this.props.controlValue}
                              multivariateOptions={multivariateOptions}
                              confirmRemove={this.confirmRemove}
                              setVariations={this.setVariations}
                              toggle={this.toggle}
                              setValue={this.setValue}
                              readOnly={this.props.readOnly}
                              items={value.map(v => (
                                  {
                                      ...v,
                                      segment: _.find(segments, { id: v.segment }) || {},
                                  }
                              ))}
                              onSortEnd={this.onSortEnd}
                            />
                            )}
                        </div>
                    )}
                </div>
            </div>
        );
    }
}

export default hot(module)(TheComponent);
