import React, { FC, useCallback, useState } from 'react'
import EmptyState from './components/EmptyState'
import ConfigForm from './components/ConfigForm'
import TestingState from './components/TestingState'
import ConnectedState from './components/ConnectedState'
import ErrorState from './components/ErrorState'
import {
  ConnectionState,
  MOCK_CONNECTION_DETAILS,
  MOCK_ERROR,
  MOCK_STATS,
  WarehouseConfig,
} from './types'
import './WarehousePage.scss'

type WarehousePageProps = {
  initialState?: ConnectionState
}

const WarehousePage: FC<WarehousePageProps> = ({ initialState = 'empty' }) => {
  const [connectionState, setConnectionState] =
    useState<ConnectionState>(initialState)

  const handleConnect = useCallback(() => {
    setConnectionState('configuring')
  }, [])

  const handleTestConnection = useCallback((_config: WarehouseConfig) => {
    setConnectionState('testing')
    // Simulate testing delay — in real app this would be an API call
    setTimeout(() => {
      // Randomly succeed or fail for demo purposes
      setConnectionState(Math.random() > 0.3 ? 'connected' : 'error')
    }, 3000)
  }, [])

  const handleEdit = useCallback(() => {
    setConnectionState('configuring')
  }, [])

  const handleRetry = useCallback(() => {
    setConnectionState('testing')
    setTimeout(() => {
      setConnectionState(Math.random() > 0.3 ? 'connected' : 'error')
    }, 3000)
  }, [])

  const handleDisconnect = useCallback(() => {
    setConnectionState('empty')
  }, [])

  const handleCancel = useCallback(() => {
    setConnectionState('empty')
  }, [])

  const renderState = () => {
    switch (connectionState) {
      case 'empty':
        return <EmptyState onConnect={handleConnect} />
      case 'configuring':
        return (
          <ConfigForm
            onTestConnection={handleTestConnection}
            onCancel={handleCancel}
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
        <span className='warehouse-page__breadcrumb-item'>Settings</span>
        <span className='warehouse-page__breadcrumb-sep'>/</span>
        <span className='warehouse-page__breadcrumb-current'>
          Data Warehouse
        </span>
      </div>

      <div className='warehouse-page__header'>
        <div className='warehouse-page__title-col'>
          <h1 className='warehouse-page__title'>Data Warehouse</h1>
          {(connectionState === 'connected' || connectionState === 'error') && (
            <p className='warehouse-page__subtitle'>
              Stream flag evaluation and custom event data to your warehouse for
              experimentation and analysis.
            </p>
          )}
        </div>
      </div>

      <div className='warehouse-page__content'>{renderState()}</div>
    </div>
  )
}

WarehousePage.displayName = 'WarehousePage'
export default WarehousePage
