import { FC, PropsWithChildren, ReactNode } from 'react'
import Text from './base/Text'

type PageTitleType = PropsWithChildren<{
  title: ReactNode
  cta?: ReactNode
  className?: string
}>

const PageTitle: FC<PageTitleType> = ({ children, className, cta, title }) => {
  return (
    <div className={className || 'mb-4'}>
      <div className='flex-row flex-lg-row gap-2 align-items-start align-items-lg-center justify-content-between'>
        <div className='flex flex-fill'>
          <Text variant='h4' level={1} className={children ? 'mb-1' : 'mb-0'}>
            {title}
          </Text>
          {children && (
            <Row>
              <div className='col-xl-8 col-12 mt-1'>
                <div>{children}</div>
              </div>
            </Row>
          )}
        </div>
        {!!cta && <div className='float-end'>{cta}</div>}
      </div>
      <hr className='mb-0 mt-3' />
    </div>
  )
}

export default PageTitle
