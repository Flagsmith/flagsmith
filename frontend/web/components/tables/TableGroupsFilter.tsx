import React, { FC, useEffect, useMemo, useRef, useState } from 'react'
import { User } from 'common/types/responses'
import { AsyncStorage } from 'polyfill-react-native'
import { IonIcon } from '@ionic/react'
import { close } from 'ionicons/icons'
import SettingsButton from 'components/SettingsButton'
import UserSelect from 'components/UserSelect'
import OrganisationStore from 'common/stores/organisation-store'
import TableFilter from './TableFilter'
import TableFilterOptions from './TableFilterOptions'
import { sortBy } from 'lodash'
import { useGetGroupSummariesQuery } from 'common/services/useGroupSummary'

type TableFilterType = {
  value: number[]
  onChange: (value: TableFilterType['value']) => void
  className?: string
  useLocalStorage?: boolean
  isLoading?: boolean
  projectId: string
  orgId: string | undefined
}

const TableGroupsFilter: FC<TableFilterType> = ({
  className,
  isLoading,
  onChange,
  orgId,
  projectId,
  useLocalStorage,
  value,
}) => {
  const checkedLocalStorage = useRef(false)
  const { data } = useGetGroupSummariesQuery(
    { orgId: orgId! },
    { skip: !orgId },
  )
  const groups = useMemo(() => {
    return sortBy(
      (data || []).map((item) => ({
        label: `${item.name}`,
        value: item.id,
      })),
      'label',
    )
  }, [data, value])

  useEffect(() => {
    if (checkedLocalStorage.current && useLocalStorage) {
      AsyncStorage.setItem(`${projectId}-owner-groups`, JSON.stringify(value))
    }
  }, [value, projectId, useLocalStorage])
  useEffect(() => {
    const checkLocalStorage = async function () {
      if (useLocalStorage && !checkedLocalStorage.current) {
        checkedLocalStorage.current = true
        const storedValue = await AsyncStorage.getItem(
          `${projectId}-owner-groups`,
        )
        if (storedValue) {
          try {
            const storedValueObject = JSON.parse(storedValue)
            onChange(storedValueObject)
          } catch (e) {}
        }
      }
    }
    checkLocalStorage()
  }, [useLocalStorage, projectId])

  return (
    <TableFilterOptions
      className={className}
      title={
        <Row>
          Groups{' '}
          {!!value?.length && (
            <span className='mx-1 unread d-inline'>{value.length}</span>
          )}
        </Row>
      }
      isLoading={isLoading}
      multiple
      showSearch
      options={groups}
      onChange={onChange as any}
      value={value}
    />
  )
}

export default TableGroupsFilter
