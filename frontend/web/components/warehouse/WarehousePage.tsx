import React, { FC, useCallback, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import Utils from 'common/utils/utils'
import EmptyState from './components/EmptyState'
import ConfigForm from './components/ConfigForm'
import PendingSetupState from './components/PendingSetupState'
import TestingState from './components/TestingState'
import ConnectedState from './components/ConnectedState'
import ErrorState from './components/ErrorState'
import {
  ConnectionState,
  MOCK_CONFIG,
  MOCK_CONNECTION_DETAILS,
  MOCK_ERROR,
  MOCK_PUBLIC_KEY,
  MOCK_SETUP_SCRIPT,
  MOCK_STATS,
  WarehouseConfig,
} from './types'
import './WarehousePage.scss'

const VALID_STATES: ConnectionState[] = [
  'empty',
  'configuring',
  'pending_customer_setup',
  'testing',
  'connected',
  'error',
]

const STATE_LABELS: Record<ConnectionState, string> = {
  configuring: 'Configuring',
  connected: 'Connected',
  empty: 'Empty',
  error: 'Error',
  pending_customer_setup: 'Pending setup',
  testing: 'Testing',
}

type WarehousePageProps = {
  initialState?: ConnectionState
}

const WarehousePage: FC<WarehousePageProps> = ({ initialState }) => {
  const { organisationId } = useParams<{ organisationId?: string }>()
  const integrationsUrl = organisationId
    ? `/organisation/${organisationId}/integrations`
    : undefined
  const params = Utils.fromParam() as Record<string, string | undefined>
  const stateFromUrl = VALID_STATES.includes(params.state as ConnectionState)
    ? (params.state as ConnectionState)
    : undefined
  const showDemoSwitcher = params.demo === '1'
  const [connectionState, setConnectionState] = useState<ConnectionState>(
    initialState ?? stateFromUrl ?? 'empty',
  )
  /**
   * Distinguishes "creating a new connection" from "editing the existing one"
   * while both share the `configuring` state. Used by ConfigForm to lock
   * immutable fields (type + accountIdentifier) on edit per issue #7276.
   */
  const [isEditingExisting, setIsEditingExisting] = useState(false)
  /**
   * Where to return when the user cancels out of the edit form — the state
   * they were in before clicking Edit. `empty` when they're creating fresh.
   */
  const [cancelReturnState, setCancelReturnState] =
    useState<ConnectionState>('empty')

  const handleConnect = useCallback(() => {
    setIsEditingExisting(false)
    setCancelReturnState('empty')
    setConnectionState('configuring')
  }, [])

  const handleConnectSubmit = useCallback((_config: WarehouseConfig) => {
    // Real API: POST returns the generated public_key + setup_script and sets
    // status to pending_customer_setup until the customer runs the SQL and
    // clicks "Test Connection".
    setConnectionState('pending_customer_setup')
  }, [])

  const handleTestConnection = useCallback(() => {
    setConnectionState('testing')
    setTimeout(() => {
      setConnectionState(Math.random() > 0.3 ? 'connected' : 'error')
    }, 3000)
  }, [])

  const handleEdit = useCallback(() => {
    setIsEditingExisting(true)
    setCancelReturnState(connectionState === 'error' ? 'error' : 'connected')
    setConnectionState('configuring')
  }, [connectionState])

  const handleRetry = useCallback(() => {
    setConnectionState('testing')
    setTimeout(() => {
      setConnectionState(Math.random() > 0.3 ? 'connected' : 'error')
    }, 3000)
  }, [])

  const handleDisconnect = useCallback(() => {
    setConnectionState('empty')
  }, [])

  const handleShowSetupScript = useCallback(() => {
    setConnectionState('pending_customer_setup')
  }, [])

  const handleCancel = useCallback(() => {
    setConnectionState(cancelReturnState)
  }, [cancelReturnState])

  const renderState = () => {
    switch (connectionState) {
      case 'empty':
        return <EmptyState onConnect={handleConnect} />
      case 'configuring':
        return (
          <ConfigForm
            onConnect={handleConnectSubmit}
            onCancel={handleCancel}
            isEdit={isEditingExisting}
            initialConfig={isEditingExisting ? MOCK_CONFIG : undefined}
          />
        )
      case 'pending_customer_setup':
        return (
          <PendingSetupState
            setupScript={MOCK_SETUP_SCRIPT}
            publicKey={MOCK_PUBLIC_KEY}
            onTestConnection={handleTestConnection}
            onEdit={handleEdit}
          />
        )
      case 'testing':
        return <TestingState />
      case 'connected':
        return (
          <ConnectedState
            stats={MOCK_STATS}
            details={MOCK_CONNECTION_DETAILS}
            onEdit={handleEdit}
            onDisconnect={handleDisconnect}
          />
        )
      case 'error':
        return (
          <ErrorState
            error={MOCK_ERROR}
            details={MOCK_CONNECTION_DETAILS}
            onRetry={handleRetry}
            onShowSetupScript={handleShowSetupScript}
            onEdit={handleEdit}
          />
        )
      default:
        return null
    }
  }

  return (
    <div className='warehouse-page'>
      <div className='warehouse-page__breadcrumb'>
        {integrationsUrl ? (
          <Link
            className='warehouse-page__breadcrumb-link'
            to={integrationsUrl}
          >
            Organisation Integrations
          </Link>
        ) : (
          <span className='warehouse-page__breadcrumb-item'>
            Organisation Integrations
          </span>
        )}
        <span className='warehouse-page__breadcrumb-sep'>/</span>
        <span className='warehouse-page__breadcrumb-current'>
          Data Warehouse
        </span>
      </div>

      {showDemoSwitcher && (
        <div className='warehouse-page__demo-switcher'>
          <span className='warehouse-page__demo-switcher-label'>
            Demo state
          </span>
          {VALID_STATES.map((s) => (
            <button
              key={s}
              type='button'
              className={`warehouse-page__demo-switcher-pill ${
                connectionState === s
                  ? 'warehouse-page__demo-switcher-pill--active'
                  : ''
              }`}
              onClick={() => setConnectionState(s)}
            >
              {STATE_LABELS[s]}
            </button>
          ))}
        </div>
      )}

      {(connectionState === 'connected' || connectionState === 'error') && (
        <p className='warehouse-page__subtitle'>
          Stream flag evaluation and custom event data to your warehouse for
          experimentation and analysis.
        </p>
      )}

      <div className='warehouse-page__content'>{renderState()}</div>
    </div>
  )
}

WarehousePage.displayName = 'WarehousePage'
export default WarehousePage
