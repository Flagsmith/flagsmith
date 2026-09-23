import { FC } from 'react'
import Skeleton from 'components/Skeleton'
import './CreateMetricForm.scss'

const FIELD_COUNT = 4

const CreateMetricFormSkeleton: FC = () => (
  <div className='create-metric-form' aria-hidden>
    {Array.from({ length: FIELD_COUNT }).map((_, index) => (
      <div className='create-metric-form__field' key={index}>
        <Skeleton width={140} height={14} className='mb-2' />
        <Skeleton width='100%' height={38} />
      </div>
    ))}
    <div className='d-flex gap-2 mt-3'>
      <Skeleton variant='badge' width={120} height={38} />
      <Skeleton variant='badge' width={88} height={38} />
    </div>
  </div>
)

CreateMetricFormSkeleton.displayName = 'CreateMetricFormSkeleton'
export default CreateMetricFormSkeleton
