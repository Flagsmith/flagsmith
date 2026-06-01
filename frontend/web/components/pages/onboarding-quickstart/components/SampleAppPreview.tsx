import React, { FC } from 'react'
import Button from 'components/base/forms/Button'

type SampleAppPreviewProps = {
  enabled: boolean
  featureName: string
}

// A believable (but clearly sample) web app whose "New feature" element is
// shown only when the flag is on. Deliberately one visible change, so the
// cause→effect of toggling the flag is unmistakable.
const SampleAppPreview: FC<SampleAppPreviewProps> = ({
  enabled,
  featureName,
}) => (
  <div className='flag-demo__browser rounded-lg border border-default bg-surface-default'>
    <div className='flag-demo__browser-bar d-flex align-items-center gap-2 px-3 py-2'>
      <span className='flag-demo__dot flag-demo__dot--red' />
      <span className='flag-demo__dot flag-demo__dot--amber' />
      <span className='flag-demo__dot flag-demo__dot--green' />
      <span className='flag-demo__url rounded-md bg-surface-subtle text-muted ms-2 px-3 py-1'>
        sample-app.com
      </span>
    </div>

    <div className='d-flex flex-column gap-3 p-4'>
      <div className='d-flex align-items-center justify-content-between'>
        <div className='d-flex align-items-center gap-2'>
          <span className='flag-demo__brand-dot' />
          <span className='text-default fw-bold'>Acme</span>
        </div>
        <div className='d-flex align-items-center gap-3 text-muted'>
          <span>Home</span>
          <span>Pricing</span>
          <span>Docs</span>
        </div>
      </div>

      <h3 className='text-default mb-0'>Welcome back 👋</h3>

      {enabled && (
        <div className='flag-demo__feature rounded-md border border-action bg-surface-action-subtle p-3 d-flex flex-column gap-2'>
          <div className='d-flex align-items-center justify-content-between gap-2'>
            <span className='text-default fw-bold'>✨ New feature</span>
            <span className='flag-demo__tag rounded-pill text-action px-2 py-1'>
              controlled by your flag
            </span>
          </div>
          <span className='text-muted'>
            Only appears when <code className='text-action'>{featureName}</code>{' '}
            is on.
          </span>
          <div>
            <Button theme='primary' size='small'>
              Try it now
            </Button>
          </div>
        </div>
      )}
    </div>
  </div>
)

export default SampleAppPreview
