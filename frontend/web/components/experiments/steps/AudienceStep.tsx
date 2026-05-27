import { FC } from 'react'
import { IonIcon } from '@ionic/react'
import { peopleOutline } from 'ionicons/icons'
import ContentCard from 'components/base/grid/ContentCard'
import 'components/experiments/wizard.scss'

const AudienceStep: FC = () => {
  return (
    <div className='d-flex flex-column gap-4'>
      <ContentCard title='Targeting'>
        <p className='text-muted fs-small mb-0'>
          Define who is eligible for the experiment using attribute conditions.
          Conditions are AND-joined. Leave empty to run on all identities in the
          environment. Conditions are frozen at launch. Later edits to existing
          Segments cannot drift the experiment audience.
        </p>
        <div className='d-flex align-items-start gap-3 p-3 border rounded'>
          <IonIcon
            icon={peopleOutline}
            style={{ fontSize: 24 }}
            className='text-muted flex-shrink-0 mt-1'
          />
          <div>
            <div className='fw-bold'>All identities in this environment</div>
            <div className='text-muted fs-small'>
              No targeting conditions. Every identity is eligible for the
              experiment. Add a condition to filter the audience.
            </div>
          </div>
        </div>
      </ContentCard>

      {/* Sample size hidden for now — hardcoded to 100% in payload */}
    </div>
  )
}

export default AudienceStep
