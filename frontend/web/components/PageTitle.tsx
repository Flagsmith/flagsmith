import { FC, PropsWithChildren, ReactNode } from 'react' // we need this to make JSX compile

type PageTitleType = PropsWithChildren<{
  title: ReactNode
  cta?: ReactNode
  className?: string
}>

const PageTitle: FC<PageTitleType> = ({ children, className, cta, title }) => {
  return (
    <div className={className || 'mb-4'}>
      <div className='flex-row align-items-center'>
        <Flex>
          <h4
            className='mb-0'
            style={{
              lineHeight: children ? '' : '48px',
            }}
          >
            {title}
          </h4>
          {children && (
            <Row>
              <div className='col-xl-8 col-12 mt-1'>
                <div>{children}</div>
              </div>
            </Row>
          )}
        </Flex>
        {!!cta && <div className='float-right ms-2'>{cta}</div>}
      </div>
      <hr className='mb-0 mt-2' />
    </div>
  )
}

export default PageTitle
