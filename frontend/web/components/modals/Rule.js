// import propTypes from 'prop-types';
import React, { PureComponent } from 'react';

export default class Rule extends PureComponent {
    static displayName = 'Rule';

    static propTypes = {};

    renderRule = (rule, i) => {
        const { props: { operators, rule: { conditions: rules } } } = this;
        const isLastRule = i === (rules.length - 1);
        const hasOr = i > 0;
        return (
            <div className="rule__row reveal" key={i}>
                {hasOr && (
                    <Row className="or-divider">
                        <Row>
                            <div className="or-divider__up"/>
                            Or
                            <div className="or-divider__down"/>
                        </Row>
                        <Flex className="or-divider__line"/>
                    </Row>
                )}
                <Row noWrap className="rule">
                    <Flex>
                        <Row>
                            <Flex value={20} className="px-1">
                                <Tooltip
                                  title={(
                                      <Input
                                        readOnly={this.props.readOnly}
                                        data-test={`${this.props['data-test']}-property-${i}`}
                                        className="input-container full-width"
                                        value={`${rule.property}`}
                                        placeholder={rule.operator && rule.operator === 'PERCENTAGE_SPLIT' ? 'Trait (N/A)' : 'Trait *'}
                                        onChange={e => this.setRuleProperty(i, 'property', { value: Utils.safeParseEventValue(e) })}
                                        disabled={rule.operator && rule.operator === 'PERCENTAGE_SPLIT'}
                                      />
                                    )}
                                  place="top"
                                >
                                    {Constants.strings.USER_PROPERTY_DESCRIPTION}
                                </Tooltip>
                            </Flex>
                            <Flex value={30} className="px-1 text-center">
                                {this.props.readOnly ? _.find(operators, { value: rule.operator }).label : (
                                    <Select
                                      data-test={`${this.props['data-test']}-operator-${i}`}
                                      value={rule.operator && _.find(operators, { value: rule.operator })}
                                      onChange={value => this.setRuleProperty(i, 'operator', value)}
                                      options={operators}
                                    />
                                )}
                            </Flex>
                            <Flex value={15} className="px-1">
                                <Input
                                  readOnly={this.props.readOnly}
                                  data-test={`${this.props['data-test']}-value-${i}`}
                                  className="input-container--flat full-width"
                                  value={`${rule.value}`}
                                  placeholder="Value *"
                                  onChange={e => this.setRuleProperty(i, 'value', { value: Utils.getTypedValue(Utils.safeParseEventValue(e), true) })}
                                  isValid={rule.value && this.validateRule(rule)}
                                />
                            </Flex>
                        </Row>
                    </Flex>
                    <div>
                        <Row noWrap>
                            {isLastRule && !this.props.readOnly ? (
                                <ButtonOutline
                                  data-test={`${this.props['data-test']}-or`}
                                  type="button" onClick={this.addRule}

                                >
                                    Or
                                </ButtonOutline>
                            ) : (
                                <div style={{ width: 64 }} />
                            )}

                            <div>
                                <button
                                  data-test={`${this.props['data-test']}-remove`}
                                  type="button"
                                  id="remove-feature"
                                  onClick={() => this.removeRule(i)}
                                  className="btn btn--with-icon btn--condensed reveal--child btn--remove"
                                >
                                    <RemoveIcon/>
                                </button>
                            </div>
                        </Row>
                    </div>
                </Row>
            </div>
        );
    }

    removeRule = (i) => {
        const { props: { rule: { conditions: rules } } } = this;

        if (rules.length === 1) {
            this.props.onRemove();
        } else {
            rules.splice(i, 1);
            this.props.onChange(this.props.rule);
        }
    }

    setRuleProperty = (i, prop, { value }) => {
        const { props: { rule: { conditions: rules } } } = this;
        rules[i][prop] = Utils.getTypedValue(value,true);
        if (prop === 'operator' && value === 'PERCENTAGE_SPLIT') {
            rules[i].property = '';
        }
        this.props.onChange(this.props.rule);
    }

    addRule = () => {
        const { props: { rule: { conditions: rules } } } = this;
        this.props.rule.conditions = rules.concat([{ ...Constants.defaultRule }]);
        this.props.onChange(this.props.rule);
    };

    validateRule = (rule) => {
        switch (rule.operator) {
            case 'PERCENTAGE_SPLIT': {
                const value = parseFloat(rule.value);
                return value && value >= 0 && value <= 100;
            }
            default:
                return true;
        }
    }

    render() {
        const { props: { rule: { conditions: rules } } } = this;
        return (
            <FormGroup>
                <div className="panel overflow-visible">
                    <div className="panel-content">
                        {rules.map(this.renderRule)}
                    </div>
                </div>
            </FormGroup>
        );
    }
}
