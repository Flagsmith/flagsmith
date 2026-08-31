import React, { FC, useMemo, useState } from 'react'
import { useGetEnvironmentsQuery } from 'common/services/useEnvironment'
import Button from 'components/base/forms/Button'
import FieldLabel from 'components/base/forms/FieldLabel'
import CopyField from 'components/CopyField'
import EnvironmentSelect from 'components/EnvironmentSelect'
import ModalHR from 'components/modals/ModalHR'
import CohortSyncKeyStep from './CohortSyncKeyStep'
import ConnectCohortProviderStep from './ConnectCohortProviderStep'
import {
  COHORT_PROVIDERS,
  CohortProviderKey,
  getCohortProviderEndpoint,
} from './providers'
import './ConnectCohortProviderModal.scss'

const SEGMENTS_DOCS_URL = 'https://docs.flagsmith.com/basic-features/segments'

type ConnectCohortProviderModalProps = {
  projectId: number | string
  provider: CohortProviderKey
}

const ConnectCohortProviderModal: FC<ConnectCohortProviderModalProps> = ({
  projectId,
  provider,
}) => {
  const config = COHORT_PROVIDERS[provider]
  const endpointUrl = getCohortProviderEndpoint(provider)
  const [selectedEnvironment, setSelectedEnvironment] = useState('')

  const { data: environments, isLoading } = useGetEnvironmentsQuery({
    projectId: Number(projectId),
  })

  // EnvironmentSelect orders alphabetically, so the default matches its first option.
  const defaultEnvironment = useMemo(
    () =>
      [...(environments?.results || [])].sort((a, b) =>
        a.name.localeCompare(b.name),
      )[0]?.api_key,
    [environments?.results],
  )
  const environmentApiKey = selectedEnvironment || defaultEnvironment || ''

  return (
    <div className='connect-cohort-provider'>
      <div className='modal-body'>
        {isLoading && !environments ? (
          <Loader />
        ) : (
          <div className='d-flex flex-column gap-4'>
            <div>
              <FieldLabel htmlFor='connect-provider-environment-select'>
                Environment
              </FieldLabel>
              <EnvironmentSelect
                inputId='connect-provider-environment-select'
                data-test='connect-provider-env-select'
                projectId={Number(projectId)}
                size='default'
                value={environmentApiKey}
                onChange={(value) => setSelectedEnvironment(`${value}`)}
              />
              <div className='fs-small text-secondary mt-1'>
                Cohort members are synchronised into this environment only.
              </div>
            </div>
            <CohortSyncKeyStep
              key={environmentApiKey}
              environmentApiKey={environmentApiKey}
              index={1}
              projectId={projectId}
              providerLabel={config.label}
            />
            <ConnectCohortProviderStep
              index={2}
              title={config.endpointStepTitle}
            >
              {!!config.endpointStepBody && (
                <p className='fs-small text-secondary lh-sm mb-0'>
                  {config.endpointStepBody}
                </p>
              )}
              {!!endpointUrl && (
                <CopyField
                  title={config.endpoint?.fieldTitle}
                  value={endpointUrl}
                  className='font-monospace'
                  data-test='connect-provider-url'
                />
              )}
              <div className='d-flex flex-column mx-0 gap-1 mt-3'>
                {config.authRows.map((row) => (
                  <div
                    key={row.label}
                    className='d-flex align-items-center fs-small'
                  >
                    <div className='connect-cohort-provider__auth-label text-secondary'>
                      {row.label}
                    </div>
                    {row.mono ? (
                      <span className='font-monospace fs-small text-muted bg-surface-muted rounded-sm px-2 py-1'>
                        {row.value}
                      </span>
                    ) : (
                      <span className='fw-semibold'>{row.value}</span>
                    )}
                  </div>
                ))}
              </div>
              {!!endpointUrl && (
                <div className='fs-small text-secondary mt-3'>
                  This URL is the same for every environment — your key decides
                  where cohort members land.
                </div>
              )}
            </ConnectCohortProviderStep>
            <ConnectCohortProviderStep index={3} title={config.exportStepTitle}>
              <p className='fs-small text-secondary lh-sm mb-0'>
                {config.exportStepBody}
              </p>
            </ConnectCohortProviderStep>
          </div>
        )}
      </div>
      <ModalHR />
      <div className='modal-footer d-flex align-items-center justify-content-between'>
        <Button
          theme='text'
          href={SEGMENTS_DOCS_URL}
          target='_blank'
          className='fw-normal'
        >
          Learn about Segments
        </Button>
        <Button onClick={() => closeModal()} data-test='connect-provider-done'>
          Done
        </Button>
      </div>
    </div>
  )
}

export default ConnectCohortProviderModal
