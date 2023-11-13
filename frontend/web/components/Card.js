import { PureComponent } from 'react'

const Card = class extends PureComponent {
  static displayName = 'Card'

  render() {
    return (
      <div
        className={`rounded-3 panel panel-default ${
          this.props.className || ''
        }`}
      >
        <div className='panel-content p-4'>{this.props.children}</div>
      </div>
    )
  }
}

Card.displayName = 'Card'

Card.propTypes = {
  children: OptionalNode,
  icon: OptionalString,
  title: oneOfType([OptionalObject, OptionalString]),
}

module.exports = Card
