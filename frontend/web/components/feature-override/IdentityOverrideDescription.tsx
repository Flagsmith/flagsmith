import { FC } from 'react'
import UsersIcon from 'components/svg/UsersIcon'

type IdentityOverrideDescriptionType = {}

const IdentityOverrideDescription: FC<
  IdentityOverrideDescriptionType
> = ({}) => {
  return (
    <div className='list-item-subtitle text-primary d-flex align-items-center'>
      <UsersIcon fill='#6837fc' width={16} className='me-1' />
      This feature is being overridden for this identity
    </div>
  )
}

export default IdentityOverrideDescription
