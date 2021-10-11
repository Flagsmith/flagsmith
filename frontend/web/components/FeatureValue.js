import React, { Component } from 'react';

const FeatureValue = class extends Component {
    static displayName = 'FeatureValue'

    constructor(props, context) {
        super(props, context);
        this.state = {};
    }

    render() {
        if (this.props.value === null || this.props.value === undefined) {
            return null;
        }
        const type = typeof Utils.getTypedValue(`${this.props.value}`);
        if (type === 'string' && this.props.value === '' && !this.props.includeEmpty) {
            return null;
        }
        return (
            <span className={`feature-value-container ${type} ${this.props.className || ''}`} onClick={this.props.onClick} data-test={this.props['data-test']}>
                {type == 'string' && <span className="quot">"</span>}
                <span
                  className="feature-value"
                >
                    {Format.truncateText(`${this.props.value}`, 20)}
                </span>
                {type == 'string' && <span className="quot">"</span>}
            </span>
        );
    }
};

FeatureValue.propTypes = {};

module.exports = FeatureValue;
