import { PureComponent } from 'react'

const Panel = class extends PureComponent {
  static displayName = 'Panel'

  render() {
    return (
      <div
        className={`panel panel-default ${this.props.className || ''} ${
          this.props.title ? '' : 'mt-2'
        }`}
      >
        {(this.props.title || this.props.action) && (
          <div className='panel-heading mb-2'>
            <Row space>
              {!!this.props.title && (
                <Row className='flex-1 mr-3'>
                  <h5 className='m-b-0 title'>{this.props.title}</h5>{' '}
                </Row>
              )}
              {this.props.action}
            </Row>
          </div>
        )}

        <div className='panel-content'>{this.props.children}</div>
      </div>
    )
  }
}

Panel.displayName = 'Panel'

Panel.propTypes = {
  children: OptionalNode,
  title: oneOfType([OptionalObject, OptionalString]),
}

export default Panel
