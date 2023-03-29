// propTypes: value: OptionalNumber
import { PureComponent } from 'react'
const Column = class extends PureComponent {
  static displayName = 'Column'

  render() {
    return (
      <div
        {...this.props}
        className={`${this.props.className || ''} flex-column`}
      >
        {this.props.children}
      </div>
    )
  }
}

Column.defaultProps = {}

Column.propTypes = {
  children: OptionalNode,
  className: OptionalString,
  style: propTypes.any,
  value: OptionalNumber,
}

module.exports = Column
