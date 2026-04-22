import React, { PureComponent, ReactNode, createElement } from 'react'

type PanelProps = {
  children?: ReactNode
  title?: ReactNode
  titleLevel?: 'h1' | 'h2' | 'h3' | 'h4' | 'h5' | 'h6'
  action?: ReactNode
  className?: string
}

class Panel extends PureComponent<PanelProps> {
  static displayName = 'Panel'

  render() {
    const { action, children, className, title, titleLevel = 'h5' } = this.props

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
                {title &&
                  createElement(
                    titleLevel,
                    { className: 'm-b-0 title' },
                    title,
                  )}
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
