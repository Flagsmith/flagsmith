import { FC } from 'react'
import DependenciesPanel from 'components/modals/create-feature/tabs/FeatureDependenciesTab/DependenciesPanel'
import Skeleton from 'components/Skeleton'
import './FeatureDependenciesSkeleton.scss'

// Mirrors the tab's real shape so the layout does not jump when data lands.
const ROW_COUNT = 2

const FeatureDependenciesSkeleton: FC = () => (
  <div aria-hidden>
    <Skeleton width={120} height={20} className='mb-2' />
    <Skeleton width='70%' height={14} className='mb-3' />

    <DependenciesPanel>
      <div className='dependencies-skeleton-row px-3 py-2'>
        <Skeleton width={70} height={12} />
        <Skeleton width={44} height={12} />
        <Skeleton width={56} height={12} />
      </div>
      {Array.from({ length: ROW_COUNT }).map((_, index) => (
        <div className='dependencies-skeleton-row px-3 py-2' key={index}>
          <Skeleton width={160} height={14} />
          <Skeleton width={28} height={14} />
          <Skeleton width={52} height={14} />
        </div>
      ))}
    </DependenciesPanel>

    <Skeleton width={128} height={32} className='mt-3' />

    <Skeleton width={150} height={20} className='mt-5 mb-2' />
    <Skeleton width='60%' height={14} className='mb-3' />
    <Skeleton width='100%' height={76} />
  </div>
)

FeatureDependenciesSkeleton.displayName = 'FeatureDependenciesSkeleton'
export default FeatureDependenciesSkeleton
