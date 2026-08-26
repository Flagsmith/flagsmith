import { FC, useEffect, useRef, useState } from 'react'
import Button from 'components/base/forms/Button'
import ProviderCard from 'components/pages/organisation-settings/tabs/trust-relationships/ProviderCard'
import {
  TRUST_RELATIONSHIP_PROVIDERS,
  TrustRelationshipProvider,
} from 'components/pages/organisation-settings/tabs/trust-relationships/providers'
import GithubTrustRelationshipForm from 'components/pages/organisation-settings/tabs/trust-relationships/GithubTrustRelationshipForm'
import TrustRelationshipModal from 'components/pages/organisation-settings/tabs/trust-relationships/TrustRelationshipModal'
import './NewTrustRelationshipModal.scss'

const ICON_SIZE = 40

type NewTrustRelationshipModalProps = {
  organisationId: number
  existingAudiences: string[]
}

const NewTrustRelationshipModal: FC<NewTrustRelationshipModalProps> = ({
  existingAudiences,
  organisationId,
}) => {
  const [provider, setProvider] = useState<TrustRelationshipProvider | null>(
    null,
  )
  const formRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    // Land on the first field, which depends on the provider and, for GitHub, on
    // whether the integration is installed.
    formRef.current
      ?.querySelector<HTMLElement>(
        'input:not([readonly]):not([type=hidden]), textarea',
      )
      ?.focus()
  }, [provider])

  if (!provider) {
    return (
      <div className='p-4'>
        <p className='text-secondary mb-3'>
          Choose how your CI will authenticate.
        </p>
        <div className='d-flex flex-column gap-3'>
          {TRUST_RELATIONSHIP_PROVIDERS.map((option) => (
            <ProviderCard
              key={option.key}
              onClick={() => setProvider(option)}
              icon={option.icon(ICON_SIZE)}
              title={option.label}
              description={option.description}
              badge={option.badge}
            />
          ))}
        </div>
      </div>
    )
  }

  return (
    <>
      <div className='px-4 pt-4'>
        <div className='fs-small text-secondary text-uppercase mb-2'>
          Provider
        </div>
        <div className='new-trust-relationship__provider d-flex align-items-center gap-3 p-3 rounded-lg bg-surface-subtle'>
          <span className='d-flex' aria-hidden>
            {provider.icon(ICON_SIZE - 12)}
          </span>
          <div className='flex-fill fw-semibold'>{provider.label}</div>
          <Button theme='text' onClick={() => setProvider(null)}>
            Change
          </Button>
        </div>
      </div>
      <div ref={formRef}>
        {provider.key === 'github' ? (
          <GithubTrustRelationshipForm
            organisationId={organisationId}
            existingAudiences={existingAudiences}
          />
        ) : (
          <TrustRelationshipModal organisationId={organisationId} />
        )}
      </div>
    </>
  )
}

export default NewTrustRelationshipModal
