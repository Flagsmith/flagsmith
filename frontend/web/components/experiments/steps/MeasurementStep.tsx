import { FC } from 'react'
import Button from 'components/base/forms/Button'
import { IonIcon } from '@ionic/react'
import { addOutline, searchOutline } from 'ionicons/icons'
import ContentCard from 'components/base/grid/ContentCard'

const MeasurementStep: FC = () => {
  return (
    <div className='d-flex flex-column gap-4'>
      <ContentCard title='Metrics'>
        <div className='d-flex align-items-center gap-3 mb-3'>
          <div className='position-relative flex-fill'>
            <IonIcon
              icon={searchOutline}
              className='position-absolute text-muted'
              style={{
                fontSize: 18,
                left: 12,
                top: '50%',
                transform: 'translateY(-50%)',
              }}
            />
            <input
              type='text'
              className='form-control'
              placeholder='Search metrics...'
              disabled
              style={{ paddingLeft: 40 }}
            />
          </div>
          <Button disabled theme='outline'>
            <IonIcon icon={addOutline} className='me-1' />
            Create Metric
          </Button>
        </div>
      </ContentCard>
    </div>
  )
}

export default MeasurementStep
