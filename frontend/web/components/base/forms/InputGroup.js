/**
 * Created by kylejohnson on 25/07/2016.
 */
import React, { Component } from 'react';
import Constants from '../../../../common/constants';

const FormGroup = class extends Component {
    static displayName = 'FormGroup'

    constructor(props, context) {
        super(props, context);
        this.state = {};
    }

    focus = () => {
        this.input.focus();
    };

    render() {
        const { props } = this;
        const id = Utils.GUID();
        const { inputProps } = this.props;
        return (
            <div className={`${this.props.className} form-group ${(this.props.isInvalid ? 'invalid' : '')}`}>
                {this.props.tooltip ? (
                    <Tooltip
                      title={<label htmlFor={id} className="cols-sm-2 control-label">{props.title} <span className="icon ion-ios-information-circle"/></label>}
                      place="right"
                    >
                        {this.props.tooltip}
                    </Tooltip>
                ) : (
                    <Row>
                        {!!props.title && (
                        <Flex className="mr-4">
                            <label htmlFor={id} className="cols-sm-2 control-label">{props.title}</label>
                        </Flex>
                        )}
                        {!!this.props.rightComponent && (
                            <div style={{
                                marginBottom: '0.5rem',
                            }}
                            />
                        )}

                    </Row>

                )}

                {inputProps && inputProps.error && (
                    <span>
                        <span> - </span>
                        <span id={props.inputProps.name ? `${props.inputProps.name}-error` : ''} className="text-danger">
                            {inputProps.error}
                        </span>
                    </span>
                )}

                <div>
                    {this.props.component ? this.props.component : (
                        <div>
                            {
                            this.props.textarea ? (
                                <textarea
                                  ref={c => this.input = c} {...props.inputProps} isValid={props.isValid}
                                  disabled={props.disabled}
                                  value={props.value}
                                  defaultValue={props.defaultValue}
                                  data-test={props['data-test']}
                                  onChange={props.onChange} type={props.type || 'text'} id={id}
                                  placeholder={props.placeholder}
                                />
                            ) : (
                                <Input
                                  ref={c => this.input = c} {...props.inputProps} isValid={props.isValid}
                                  disabled={props.disabled}
                                  defaultValue={props.defaultValue}
                                  value={props.value}
                                  data-test={props['data-test']}
                                  onChange={props.onChange} type={props.type || 'text'} id={id}
                                  placeholder={props.placeholder}
                                />
                            )
                        }
                        </div>
                    )}
                </div>
            </div>
        );
    }
};

FormGroup.propTypes = {
    disabled: OptionalBool,
    title: propTypes.any,
    isValid: propTypes.any,
    inputProps: OptionalObject,
    value: OptionalString,
    onChange: OptionalFunc,
    type: OptionalString,
    placeholder: OptionalString,
};

module.exports = FormGroup;
