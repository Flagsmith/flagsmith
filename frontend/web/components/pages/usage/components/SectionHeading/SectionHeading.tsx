import { FC, ReactNode } from 'react'

export type SectionHeadingProps = {
  title: string
  hint: string
  action?: ReactNode
}

const SectionHeading: FC<SectionHeadingProps> = ({ action, hint, title }) => (
  <Row space className='align-items-end mb-2 mt-4 gap-3'>
    <div>
      <strong>{title}</strong>
      <div className='fs-captionSmall text-secondary'>{hint}</div>
    </div>
    {action}
  </Row>
)

export default SectionHeading
