import React, { FC, useState } from 'react'
import Button from 'components/base/forms/Button'
import Icon from 'components/icons/Icon'
import Utils from 'common/utils/utils'
import './PendingSetupState.scss'

type PendingSetupStateProps = {
  /** The server-generated setup SQL the customer needs to run in Snowflake. */
  setupScript: string
  /** The server-generated RSA public key, registered by the setup script. */
  publicKey: string
  /** Customer has run the script in Snowflake and wants Flagsmith to verify. */
  onTestConnection: () => void
  /** Jump back to the config form to change fields. */
  onEdit: () => void
}

const PendingSetupState: FC<PendingSetupStateProps> = ({
  onEdit,
  onTestConnection,
  publicKey,
  setupScript,
}) => {
  const [showPublicKey, setShowPublicKey] = useState(false)

  return (
    <div className='wh-pending-setup'>
      <div className='wh-pending-setup__header'>
        <div className='wh-pending-setup__icon' aria-hidden>
          <Icon name='checkmark-circle' width={28} />
        </div>
        <div>
          <h3 className='wh-pending-setup__title'>
            Connection saved — now set up Snowflake
          </h3>
          <p className='wh-pending-setup__subtitle'>
            Flagsmith generated a service account and an RSA key pair. Run the
            setup script below in your Snowflake console with the{' '}
            <code>SYSADMIN</code> role to register the public key and grant
            Flagsmith the access it needs.
          </p>
        </div>
      </div>

      <section className='wh-pending-setup__script'>
        <div className='wh-pending-setup__script-header'>
          <span className='wh-pending-setup__script-title'>Setup script</span>
          <Button
            theme='outline'
            size='small'
            onClick={() => Utils.copyToClipboard(setupScript)}
          >
            <Icon name='copy' width={14} /> Copy script
          </Button>
        </div>
        <pre className='wh-pending-setup__script-body'>{setupScript}</pre>
      </section>

      <section className='wh-pending-setup__public-key'>
        <button
          type='button'
          className='wh-pending-setup__public-key-toggle'
          onClick={() => setShowPublicKey((v) => !v)}
        >
          <Icon
            name={showPublicKey ? 'chevron-down' : 'chevron-right'}
            width={14}
          />
          <span>RSA public key</span>
          <span className='wh-pending-setup__public-key-hint'>
            already embedded in the script above
          </span>
        </button>
        {showPublicKey && (
          <div className='wh-pending-setup__public-key-body'>
            <pre className='wh-pending-setup__public-key-value'>
              {publicKey}
            </pre>
            <Button
              theme='outline'
              size='small'
              onClick={() => Utils.copyToClipboard(publicKey)}
            >
              <Icon name='copy' width={14} /> Copy public key
            </Button>
          </div>
        )}
      </section>

      <div className='wh-pending-setup__actions'>
        <Button theme='outline' size='small' onClick={onEdit}>
          Edit configuration
        </Button>
        <Button theme='primary' size='small' onClick={onTestConnection}>
          I&apos;ve run the script — Test Connection
        </Button>
      </div>
    </div>
  )
}

PendingSetupState.displayName = 'WarehousePendingSetupState'
export default PendingSetupState
