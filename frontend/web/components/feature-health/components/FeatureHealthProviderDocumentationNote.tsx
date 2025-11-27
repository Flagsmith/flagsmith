import InfoMessage from 'components/InfoMessage'

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
          Generic provider:{' '}
          <a href='https://docs.flagsmith.com/advanced-use/feature-health#generic-provider'>
            https://docs.flagsmith.com/advanced-use/feature-health#generic-provider
          </a>
        </span>
      </div>
      <div>
        <span>
          Grafana provider:{' '}
          <a href='https://docs.flagsmith.com/integrations/apm/grafana/#in-grafana-1'>
            {' '}
            https://docs.flagsmith.com/integrations/apm/grafana/#in-grafana-1
          </a>
        </span>
      </div>
    </InfoMessage>
  )
}

export default FeatureHealthProviderDocumentationNote
