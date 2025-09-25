import { FC, PropsWithChildren, ReactNode } from 'react'
import classNames from 'classnames'

type PageTitleType = PropsWithChildren<{
  title: ReactNode
  cta?: ReactNode
  className?: string
}>

const PageTitle: FC<PageTitleType> = ({ children, className, cta, title }) => {
  return (
    <div className={className || 'mb-4'}>
      <div className='flex-row flex-column flex-lg-row gap-2 align-items-start align-items-lg-center'>
        <Flex>
          <h4 className={children ? 'mb-1' : 'mb-0'}>{title}</h4>
          {children && (
            <Row>
              <div className='col-xl-8 col-12 mt-1'>
                <div>{children}</div>
              </div>
            </Row>
          )}
        </Flex>
        {!!cta && <div className='float-right ms-lg-2'>{cta}</div>}
      </div>
      <hr className='mb-0 mt-3' />
    </div>
  )
}

export default PageTitle
