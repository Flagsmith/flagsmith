import { FC, ReactNode } from 'react'
import Icon from 'components/icons/Icon'

type ChangeRequestLinkProps = {
  projectId: number
  environmentId: string
  changeRequestId: number
  children: ReactNode
}

// A new tab, as leaving the page would drop the modal and anything staged in
// it without the close confirmation.
const ChangeRequestLink: FC<ChangeRequestLinkProps> = ({
  changeRequestId,
  children,
  environmentId,
  projectId,
}) => (
  <a
    href={`/project/${projectId}/environment/${environmentId}/change-requests/${changeRequestId}`}
    target='_blank'
    rel='noopener noreferrer'
    className='d-inline-flex align-items-center gap-1'
  >
    {children}
    <Icon
      name='open-external-link'
      width={12}
      role='img'
      aria-label='opens in a new tab'
    />
  </a>
)

export default ChangeRequestLink
