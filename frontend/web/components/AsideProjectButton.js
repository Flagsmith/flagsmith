import { PureComponent } from 'react'
import Format from 'common/utils/format'

const AsideProjectButton = class extends PureComponent {
  static displayName = 'AsideProjectButton'

  render() {
    const truncated = Format.truncateText(this.props.name, 26)
    const children = (
      <div onClick={this.props.onClick}>
        <div
          className={`clickable project-select-btn ${
            this.props.active ? 'active' : ''
          }`}
        >
          <div className={`${this.props.className}`}>{truncated}</div>
        </div>
      </div>
    )
    return truncated === this.props.name ? (
      children
    ) : (
      <Tooltip title={children} place='right'>
        {this.props.name}
      </Tooltip>
    )
  }
}

AsideProjectButton.displayName = 'AsideProjectButton'

// Card.propTypes = {
//     title: oneOfType([OptionalObject, OptionalString]),
//     icon: OptionalString,
//     children: OptionalNode,
// };

module.exports = AsideProjectButton
