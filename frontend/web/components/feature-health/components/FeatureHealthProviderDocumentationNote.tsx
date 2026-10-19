import InfoMessage from 'components/InfoMessage'
import Link from 'components/base/link'

interface FeatureHealthProviderDocumentationNoteProps {
  defaultClosed?: boolean
}

const FeatureHealthProviderDocumentationNote: React.FC<
  FeatureHealthProviderDocumentationNoteProps
> = ({ defaultClosed = false }) => {
  return (
    <InfoMessage defaultClosed={defaultClosed}>
      <div>
        <strong>
          Follow the documentation to configure alerting using the supported
          providers.
        </strong>
      </div>
      <div>
        <span>
          Webhook provider:{' '}
          <Link href='https://docs.flagsmith.com/advanced-use/feature-health#webhook-provider'>
            https://docs.flagsmith.com/advanced-use/feature-health#webhook-provider
          </Link>
        </span>
      </div>
      <div>
        <span>
          Grafana provider:{' '}
          <Link href='https://docs.flagsmith.com/integrations/apm/grafana/#in-grafana-1'>
            {' '}
            https://docs.flagsmith.com/integrations/apm/grafana/#in-grafana-1
          </Link>
        </span>
      </div>
    </InfoMessage>
  )
}

export default FeatureHealthProviderDocumentationNote
