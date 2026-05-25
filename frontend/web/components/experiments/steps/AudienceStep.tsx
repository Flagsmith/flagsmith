import { FC } from 'react'
import { IonIcon } from '@ionic/react'
import { peopleOutline } from 'ionicons/icons'
import ContentCard from 'components/base/grid/ContentCard'
import 'components/experiments/wizard.scss'

const SAMPLE_PRESETS = [5, 10, 25, 50, 100]

const AudienceStep: FC = () => {
  return (
    <div className='d-flex flex-column gap-4'>
      <ContentCard title='Targeting'>
        <p className='text-muted fs-small mb-0'>
          Define who is eligible for the experiment using attribute conditions.
          Conditions are AND-joined. Leave empty to run on all identities in the
          environment. Conditions are frozen at launch &mdash; later edits to
          existing Segments cannot drift the experiment audience.
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
              No targeting conditions &mdash; every identity is eligible for the
              experiment. Add a condition to filter the audience.
            </div>
          </div>
        </div>
      </ContentCard>

      <ContentCard title='Sample size'>
        <p className='text-muted fs-small mb-0'>
          What percentage of eligible users enters the experiment? The rest keep
          the flag&apos;s environment default and aren&apos;t part of the
          result.
        </p>
        <div className='d-flex gap-2 flex-wrap'>
          {SAMPLE_PRESETS.map((pct) => (
            <div
              key={pct}
              className={`btn btn-sm ${
                pct === 100 ? 'btn-primary' : 'btn-outline-secondary'
              }`}
              style={{ pointerEvents: 'none' }}
            >
              {pct}%
            </div>
          ))}
          <div
            className='btn btn-sm btn-outline-secondary'
            style={{ pointerEvents: 'none' }}
          >
            Custom
          </div>
        </div>
      </ContentCard>
    </div>
  )
}

export default AudienceStep
