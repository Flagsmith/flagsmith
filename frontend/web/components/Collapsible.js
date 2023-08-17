import { PureComponent } from 'react'
import Icon from './Icon'

const cn = require('classnames')

const Collapsible = class extends PureComponent {
  static displayName = 'Collapsible'

  static propTypes = {}

  render() {
    return (
      <div
        data-test={this.props['data-test']}
        className={cn('collapsible', this.props.className, {
          active: this.props.active,
        })}
      >
        <div
          className='collapsible__header ml-5 mr-3'
          onClick={this.props.onClick}
        >
          <Row space className='no-wrap clickable'>
            <div>{this.props.title}</div>
            <div className='align-self-start'>
              <Icon
                name={this.props.active ? 'chevron-down' : 'chevron-right'}
              />
            </div>
          </Row>
        </div>
        {this.props.active ? (
          <div className='collapsible__content'>{this.props.children}</div>
        ) : null}
      </div>
    )
  }
}

Collapsible.displayName = 'Collapsible'

// Card.propTypes = {
//     title: oneOfType([OptionalObject, OptionalString]),
//     icon: OptionalString,
//     children: OptionalNode,
// };

module.exports = Collapsible
