import { FC } from 'react'
import Button from 'components/base/forms/Button'
import Icon from 'components/icons/Icon'
import ContentCard from 'components/base/grid/ContentCard'

const MeasurementStep: FC = () => {
  return (
    <div className='d-flex flex-column gap-4'>
      <ContentCard title='Metrics'>
        <div className='d-flex align-items-center gap-3'>
          <div className='flex-fill'>
            <Input
              type='text'
              placeholder='Search metrics...'
              disabled
              search
              size='small'
            />
          </div>
          <Button disabled theme='outline'>
            <Icon name='plus' width={16} />
            Create Metric
          </Button>
        </div>
      </ContentCard>
    </div>
  )
}

export default MeasurementStep
