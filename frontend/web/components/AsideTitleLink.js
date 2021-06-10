import React, { PureComponent } from 'react';
import NavLink from 'react-router-dom/NavLink';

const cn = require('classnames');

const AsideTitleLink = class extends PureComponent {
    static displayName = 'AsideTitleLink'

    render() {
        return (
            <Tooltip
                title={
                    <div id={this.props.id} className="flex-row space aside__title-wrapper">
                        <span className="aside__link-text">{this.props.title}</span>
                        <span className={`aside__link-icon ${this.props.iconClassName || ''}`} />
                    </div>
                }
                place="top"
            >
                {this.props.tooltip}
            </Tooltip>
        );
    }
};

AsideTitleLink.displayName = 'AsideTitleLink';

// Card.propTypes = {
//     title: oneOfType([OptionalObject, OptionalString]),
//     icon: OptionalString,
//     children: OptionalNode,
// };

module.exports = AsideTitleLink;
