import React, { PureComponent, ReactNode } from 'react'

type PanelProps = {
  children?: ReactNode
  title?: ReactNode
  action?: ReactNode
  className?: string
}

class Panel extends PureComponent<PanelProps> {
  static displayName = 'Panel'

  render() {
    const { action, children, className, title } = this.props

    return (
      <div
        className={`panel panel-default ${className || ''} ${
          title ? '' : 'mt-2'
        }`}
      >
        {(title || action) && (
          <div className='panel-heading mb-2'>
            <Row space>
              <Row className='flex-1 mr-3'>
                {title && <h5 className='m-b-0 title'>{title}</h5>}
              </Row>
              {action}
            </Row>
          </div>
        )}

        <div className='panel-content'>{children}</div>
      </div>
    )
  }
}

export default Panel
