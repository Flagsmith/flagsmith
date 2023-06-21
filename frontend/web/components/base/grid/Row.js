/**
 * Created by kylejohnson on 24/07/2016.
 */
import { PureComponent } from 'react'
import cn from 'classnames'

class Row extends PureComponent {
  static displayName = 'Row'

  static propTypes = {
    children: OptionalNode,
    className: OptionalString,
    space: OptionalBool,
    style: propTypes.any,
  }

  render() {
    const { noWrap, space, ...rest } = this.props

    return (
      <div
        {...rest}
        className={cn(
          {
            'flex-row': true,
            noWrap,
            space,
          },
          this.props.className,
        )}
      >
        {this.props.children}
      </div>
    )
  }
}

module.exports = Row
