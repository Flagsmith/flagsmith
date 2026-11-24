import { FC, PropsWithChildren, ReactNode } from 'react'
import { HeadingLevel, HeadingText } from './base/typography'

type PageTitleType = PropsWithChildren<{
  title: ReactNode
  cta?: ReactNode
  className?: string
  // Use 2 when the title sits inside a page that already has one.
  level?: HeadingLevel
}>

const PageTitle: FC<PageTitleType> = ({
  children,
  className,
  cta,
  level = 1,
  title,
}) => {
  return (
    <div className={className || 'mb-4'}>
      <div className='flex-row flex-lg-row gap-2 align-items-start align-items-lg-center justify-content-between'>
        <div className='flex flex-fill'>
          <HeadingText
            level={level}
            size='lg'
            className={children ? 'mb-1' : 'mb-0'}
          >
            {title}
          </HeadingText>
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
