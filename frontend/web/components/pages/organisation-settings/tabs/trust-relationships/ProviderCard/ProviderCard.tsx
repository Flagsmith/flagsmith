import { FC, ReactNode } from 'react'
import { colorIconSecondary } from 'common/theme/tokens'
import BareButton from 'components/base/forms/BareButton'
import Chip from 'components/base/Chip'
import Icon from 'components/icons/Icon'
import './ProviderCard.scss'

export type ProviderCardProps = {
  icon: ReactNode
  title: string
  description: string
  badge?: string
  onClick: () => void
}

const ProviderCard: FC<ProviderCardProps> = ({
  badge,
  description,
  icon,
  onClick,
  title,
}) => (
  <BareButton
    className='provider-card d-flex align-items-center gap-3 w-100 p-3 text-start rounded-xl transition-fast'
    onClick={onClick}
  >
    <span
      className='d-flex align-items-center justify-content-center flex-shrink-0 p-2 rounded-lg bg-surface-muted'
      aria-hidden
    >
      {icon}
    </span>
    <span className='provider-card__body d-flex flex-column gap-1 flex-fill'>
      <span className='d-flex align-items-center gap-2 flex-wrap'>
        <span className='provider-card__title'>{title}</span>
        {!!badge && (
          <Chip size='xs' variant='accent'>
            {badge}
          </Chip>
        )}
      </span>
      <span className='fs-small text-secondary'>{description}</span>
    </span>
    <span className='d-flex align-items-center flex-shrink-0' aria-hidden>
      <Icon name='chevron-right' width={20} fill={colorIconSecondary} />
    </span>
  </BareButton>
)

export default ProviderCard
