import React, { PureComponent, ReactNode } from 'react'
import Text from 'components/base/Text'

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
                {title && (
                  <Text variant='h5' level={3} className='m-b-0 title'>
                    {title}
                  </Text>
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
