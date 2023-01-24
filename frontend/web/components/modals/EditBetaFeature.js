import React, { Component } from 'react';
import withSegmentOverrides from 'common/providers/withSegmentOverrides';
import Constants from 'common/constants';
import ConfigProvider from 'common/providers/ConfigProvider';
import ValueEditor from '../ValueEditor';

const FEATURE_ID_MAXLENGTH = Constants.forms.maxLength.FEATURE_ID;

const CreateFlag = class extends Component {
    static displayName = 'CreateFlag'

    constructor(props, context) {
        super(props, context);
        this.state = {
            enabled: props.enabled,
            value: props.value,
        };
    }

    render() {
        const {
            enabled,
            value,
        } = this.state;

        return (
            <div>
                {this.props.showEnabled && (
                    <div className="mb-2">
                        <div className="mb-2">
                            <strong>
                                Enabled
                            </strong>
                        </div>
                        <Switch checked={this.state.enabled} onChange={() => this.setState({ enabled: !this.state.enabled })}/>
                    </div>
                )}

                {this.props.showValue && (
                    <div className="mb-2">
                        <div className="mb-2">
                            <strong>
                                Value
                            </strong>
                        </div>
                        <ValueEditor
                          value={`${typeof value === 'undefined' || value === null ? '' : value}`}
                          onChange={value => this.setState({ value: Utils.safeParseEventValue(value) })}
                          placeholder="e.g. 'big' "
                        />
                    </div>
                )}


                <p>
                    This will update the feature just for your user when you login to Flagsmith.
                </p>
                <Button onClick={() => {
                    this.props.onSave(this.state.enabled, this.state.value);
                    closeModal();
                }}
                >
                        Save
                </Button>
            </div>
        );
    }
};

CreateFlag.propTypes = {};

module.exports = ConfigProvider(withSegmentOverrides(CreateFlag));
