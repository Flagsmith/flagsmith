import { PureComponent } from 'react';

const cn = require('classnames');

const FormGroup = class extends PureComponent {
    static displayName = 'FormGroup';

    render() {
        return (
            <div className={`form-group ${this.props.className || ''}`}>
                {this.props.children}
            </div>
        );
    }
};

FormGroup.displayName = 'FormGroup';
FormGroup.propTypes = {
    children: OptionalNode,
};
module.exports = FormGroup;
