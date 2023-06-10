import { PureComponent } from 'react'
import Format from 'common/utils/format'
import Button from './base/forms/Button'

const AsideProjectButton = class extends PureComponent {
  static displayName = 'AsideProjectButton'

  render() {
    const truncated = Format.truncateText(this.props.name, 26)
    const children = (
      <div
        className='aside__projects-item clickable'
        data-test={this.props['data-test']}
        onClick={this.props.onClick}
      >
        <div className='flex-row justify-content-center'>
          <div className='flex-column'>
            <Button theme='project'>{this.props.projectLetter}</Button>
          </div>
          <div className='flex-column'>
            <p className={`aside__projects-item-title ${this.props.className}`}>
              {truncated}
            </p>
          </div>
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
