import React from 'react'
import InfoMessage from 'components/InfoMessage'

const UsageAPIDefinitions: React.FC = () => {
  return (
    <div>
      <InfoMessage>
        Please be aware that usage data can be delayed by up to 3 hours.
      </InfoMessage>
      <div>
        <h4>What do these numbers mean?</h4>
        <h5>Flags</h5>
        <p>
          This is a single call to get the Environment Flag defaults, without
          providing an Identity. Note that if you trigger an update of flags via
          the SDK, this will count as an additional call.
        </p>
        <p>
          <a
            href='https://docs.flagsmith.com/basic-features/managing-features'
            target='_blank'
            rel='noreferrer'
          >
            Learn more.
          </a>
        </p>
        <h5>Identities</h5>
        <p>
          This is a single call to get the flags for a specific Identity. If
          this is the first time flags have been requested for that Identity, it
          will be persisted in our datastore. Note that this number is{' '}
          <em>not</em> a total count of Identities in the datastore, but the
          number of times an Identity has requested their flags. Note that if
          you trigger an update of flags via the SDK, this will count as an
          additional call.
        </p>
        <p>
          <a
            href='https://docs.flagsmith.com/basic-features/managing-identities'
            target='_blank'
            rel='noreferrer'
          >
            Learn more.
          </a>
        </p>
        <h5>Environment Document</h5>
        <p>
          This is a single call made by Server-Side SDKs (when running in Local
          Evaluation Mode), and the Edge Proxy to get the entire Environment
          dataset so they can run flag evaluations locally.
        </p>
        <p>
          By default, server-side SDKs refresh this data every 60 seconds, and
          the Edge Proxy every 10 seconds. Each refresh will count as a single
          call. These time periods are configurable.
        </p>
        <p>
          <a
            href='https://docs.flagsmith.com/clients/overview#local-evaluation'
            target='_blank'
            rel='noreferrer'
          >
            Learn more.
          </a>
        </p>
        <h5>Traits</h5>
        <p>
          This is the number of times Traits for an Identity have been written.
        </p>
        <p>
          <a
            href='https://docs.flagsmith.com/basic-features/managing-identities'
            target='_blank'
            rel='noreferrer'
          >
            Learn more.
          </a>
        </p>
        <h5>Total API calls</h5>
        <p>This is a sum of the above.</p>
      </div>
    </div>
  )
}

export default UsageAPIDefinitions
