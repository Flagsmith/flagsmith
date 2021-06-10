// propTypes: value: OptionalNumber
import { PureComponent } from 'react';

const cn = require('classnames');

const Column = class extends PureComponent {
    static displayName = 'Column';

    render() {
        return (
            <div {...this.props} className={`${this.props.className || ''} flex-column`}>
                {this.props.children}
            </div>
        );
    }
};

Column.defaultProps = {};

Column.propTypes = {
    className: OptionalString,
    value: OptionalNumber,
    children: OptionalNode,
    style: propTypes.any,
};

module.exports = Column;
