import React, { FC, useState } from 'react'
import flagsmith from '@flagsmith/flagsmith'
import classNames from 'classnames'
import AccountStore from 'common/stores/account-store'
import { colorIconAction } from 'common/theme/tokens'
import Button from 'components/base/forms/Button'
import BareButton from 'components/base/forms/BareButton'
import Chip from 'components/base/Chip'
import Icon from 'components/icons/Icon'
import './CreateSegmentSourcesModal.scss'

type SegmentSource = {
  description: string
  image?: string
  key: string
  name: string
}

type SelectedSegmentSource = SegmentSource | null

const SOURCES: SegmentSource[] = [
  {
    description:
      'Upload identifiers to create a managed segment. Update members with a new upload.',
    key: 'csv',
    name: 'From a CSV list',
  },
  {
    description:
      'Sync a behavioural cohort as a managed segment, updated on schedule or real-time.',
    image: '/static/images/integrations/amplitude.svg',
    key: 'amplitude',
    name: 'Amplitude',
  },
  {
    description:
      'A managed segment that updates as users enter and exit your Mixpanel cohort.',
    image: '/static/images/integrations/mp.svg',
    key: 'mixpanel',
    name: 'Mixpanel',
  },
  {
    description:
      'Activate an Adobe audience as a managed segment, refreshed automatically by Adobe.',
    image: '/static/images/integrations/adobe-analytics.png',
    key: 'adobe_journey_manager',
    name: 'Adobe Journey Manager',
  },
]

type CreateSegmentSourcesModalType = {
  onManual: () => void
}

const CreateSegmentSourcesModal: FC<CreateSegmentSourcesModalType> = ({
  onManual,
}) => {
  const [selected, setSelected] = useState<SelectedSegmentSource>(null)
  const [requested, setRequested] = useState<string[]>([])

  const trackSourceEvent = (event: string, source: SegmentSource) => {
    flagsmith.trackEvent(event, {
      metadata: {
        email: AccountStore.getUser()?.email,
        organisation: AccountStore.getOrganisation()?.name,
        source: source.key,
      },
    })
  }

  const openManual = () => {
    closeModal()
    onManual()
  }

  const selectSource = (source: SegmentSource) => {
    if (selected?.key === source.key) {
      return
    }
    setSelected(source)
    trackSourceEvent('segment_source_clicked', source)
  }

  const requestAccess = () => {
    if (!selected) {
      return
    }
    trackSourceEvent('segment_source_beta_requested', selected)
    setRequested((prev) => [...prev, selected.key])
  }

  const hasRequested = !!selected && requested.includes(selected.key)

  return (
    <div className='p-4'>
      <p className='h6 fw-semibold text-muted mb-3'>
        How do you want to define your segment?
      </p>
      <BareButton
        data-test='create-segment-manually'
        onClick={openManual}
        className='create-segment-sources__manual w-100 rounded border-1 border-primary p-3 d-flex align-items-start gap-3 mb-3'
      >
        <span className='mt-1 flex-shrink-0 d-inline-flex'>
          <Icon name='options-2' width={24} fill={colorIconAction} />
        </span>
        <div>
          <div className='fw-semibold'>Manually</div>
          <div className='fs-small text-muted'>
            Build rules based on traits and context values
          </div>
        </div>
      </BareButton>
      <div className='row g-0'>
        {SOURCES.map((source) => {
          const isSelected = selected?.key === source.key
          return (
            <div key={source.key} className='col-md-6 p-1'>
              <BareButton
                data-test={`segment-source-${source.key}`}
                aria-pressed={isSelected}
                onClick={() => selectSource(source)}
                className={classNames(
                  'create-segment-sources__source w-100 rounded border-1 p-3 h-100 d-flex align-items-start gap-3',
                  { 'border-primary bg-primary-opacity-5': isSelected },
                )}
              >
                {source.image ? (
                  <img
                    alt={source.name}
                    src={source.image}
                    width={24}
                    height={24}
                    className='mt-1 flex-shrink-0'
                  />
                ) : (
                  <span className='mt-1 flex-shrink-0 d-inline-flex'>
                    <Icon
                      name='cloud-upload'
                      width={24}
                      fill={colorIconAction}
                    />
                  </span>
                )}
                <div className='flex-fill'>
                  <div className='fw-semibold'>{source.name}</div>
                  <div className='fs-small text-muted'>
                    {source.description}
                  </div>
                </div>
                <Chip size='xs' variant='accent' className='fw-semibold'>
                  <Icon name='rocket' width={12} />
                  Beta
                </Chip>
              </BareButton>
            </div>
          )
        })}
      </div>
      {!!selected && (
        <div className='d-flex justify-content-end align-items-center gap-3 mt-4'>
          {hasRequested && (
            <span className='text-muted'>
              Thank you! 🎉 We&apos;ll be in touch.
            </span>
          )}
          <Button
            data-test='request-beta-access'
            disabled={hasRequested}
            onClick={requestAccess}
          >
            Request access to the beta
          </Button>
        </div>
      )}
    </div>
  )
}

export default CreateSegmentSourcesModal
