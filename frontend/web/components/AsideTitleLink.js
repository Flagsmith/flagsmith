import React, { PureComponent } from 'react'
import Icon from './Icon'
const AsideTitleLink = class extends PureComponent {
  static displayName = 'AsideTitleLink'

  render() {
    return (
      <Tooltip
        title={
          <div
            id={this.props.id}
            className='flex-row space aside__title-wrapper mx-3'
          >
            <span className='aside__link-text'>{this.props.title}</span>
            <span className='aside__link-icon'>
              <Icon name='plus' fill='#27AB95' width={24} />
            </span>
          </div>
        }
        place='top'
      >
        {this.props.tooltip}
      </Tooltip>
    )
  }
}

AsideTitleLink.displayName = 'AsideTitleLink'

// Card.propTypes = {
//     title: oneOfType([OptionalObject, OptionalString]),
//     icon: OptionalString,
//     children: OptionalNode,
// };

module.exports = AsideTitleLink
