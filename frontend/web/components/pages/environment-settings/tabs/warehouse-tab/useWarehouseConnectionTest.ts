import { useRef, useState } from 'react'
import { useTestWarehouseConnectionConfigMutation } from 'common/services/useWarehouseConnection'
import { Req } from 'common/types/requests'
import { WarehouseType } from 'common/types/responses'
import {
  isMissingEventsTableDetail,
  isWarehouseStartingDetail,
} from './warehouseFormUtils'

export type WarehouseTestState = 'idle' | 'connected' | 'errored' | 'starting'

type TestPayload = Pick<
  Req['testWarehouseConnectionConfig'],
  'config' | 'credentials'
>

const useWarehouseConnectionTest = (
  environmentId: string,
  warehouseType: WarehouseType,
) => {
  const [testState, setTestState] = useState<WarehouseTestState>('idle')
  const [testDetail, setTestDetail] = useState<string | null>(null)
  const [showSetupSql, setShowSetupSql] = useState(false)
  const testRevision = useRef(0)

  const [testConnectionConfig, { isLoading: isTesting }] =
    useTestWarehouseConnectionConfigMutation()

  const resetTest = () => {
    testRevision.current += 1
    setTestState('idle')
    setTestDetail(null)
  }

  const withTestReset =
    <T>(setter: (value: T) => void) =>
    (value: T) => {
      setter(value)
      resetTest()
    }

  const runTest = async ({ config, credentials }: TestPayload) => {
    const revision = testRevision.current
    try {
      const result = await testConnectionConfig({
        config,
        credentials,
        environmentId,
        warehouse_type: warehouseType,
      }).unwrap()
      if (revision !== testRevision.current) return
      if (result.status === 'connected') {
        setTestState('connected')
        setTestDetail(null)
        toast('Connection verified')
      } else if (isWarehouseStartingDetail(result.status_detail)) {
        setTestState('starting')
        setTestDetail(result.status_detail)
      } else {
        setTestState('errored')
        setTestDetail(result.status_detail)
        setShowSetupSql(isMissingEventsTableDetail(result.status_detail))
      }
    } catch {
      if (revision !== testRevision.current) return
      setTestState('errored')
      setTestDetail(null)
    }
  }

  return {
    hasTestResult: testState !== 'idle',
    isTesting,
    runTest,
    showSetupSql,
    testDetail,
    testState,
    withTestReset,
  }
}

export default useWarehouseConnectionTest
