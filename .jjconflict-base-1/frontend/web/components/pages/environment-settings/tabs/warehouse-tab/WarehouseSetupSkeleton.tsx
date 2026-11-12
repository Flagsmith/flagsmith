import { FC } from 'react'
import Skeleton from 'components/Skeleton'
import './WarehouseSetup.scss'
import 'components/base/SelectableCard/SelectableCard.scss'

// Mirrors the WarehouseSetup layout (warehouse-type selector + Flagsmith enable
// card) so the loading state has the same shape as the empty state it resolves
// to, avoiding a layout shift when the connections query settles.
const TYPE_CARD_COUNT = 4

const WarehouseSetupSkeleton: FC = () => (
  <div className='warehouse-setup' aria-hidden>
    <div>
      <div className='warehouse-setup__type-row'>
        {Array.from({ length: TYPE_CARD_COUNT }).map((_, index) => (
          <div className='warehouse-setup__type-card' key={index}>
            <div className='selectable-card'>
              <div className='selectable-card__content'>
                <div className='selectable-card__icon'>
                  <Skeleton variant='circle' width={20} height={20} />
                </div>
                <Skeleton width={80} height={16} />
                <Skeleton width={120} height={12} />
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>

    <div className='warehouse-setup__flagsmith-card'>
      <Skeleton width='60%' height={16} />
      <Skeleton variant='badge' width={88} height={32} />
    </div>
  </div>
)

WarehouseSetupSkeleton.displayName = 'WarehouseSetupSkeleton'
export default WarehouseSetupSkeleton
