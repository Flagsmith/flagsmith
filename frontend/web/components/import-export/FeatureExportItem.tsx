import React, { FC, useState } from 'react'
import { Environment, FeatureExport } from 'common/types/responses'
import ProjectStore from 'common/stores/project-store'
import moment from 'moment'
import Button from 'components/base/forms/Button'
import Format from 'common/utils/format'
import Tag from 'components/tags/Tag'
import Utils from 'common/utils/utils'
import { getFeatureExport } from 'common/services/useFeatureExport'
import { getStore } from 'common/store'

type FeatureExportItemType = {
  data: FeatureExport
}

const FeatureExportItem: FC<FeatureExportItemType> = ({ data }) => {
  const [isLoading, setIsLoading] = useState(false)

  const environment: Environment | null = ProjectStore.getEnvironmentById(
    data.environment_id,
  ) as Environment | null
  const index = ProjectStore.getEnvs()?.findIndex?.(
    (env) => env.id === data.environment_id,
  )
  const colour = index === -1 ? 0 : index

  const download = () => {
    setIsLoading(true)
    getFeatureExport(getStore(), { id: data.id })
      .then((res) => {
        if (res.data) {
          const blob = new Blob([JSON.stringify(res.data, null, 2)])
          const link = document.createElement('a')
          link.download = `${data.name}.json`
          link.href = window.URL.createObjectURL(blob)
          link.click()
        }
      })
      .finally(() => {
        setIsLoading(false)
      })
  }
  return (
    <Row>
      <div className='table-column fs-small'>
        {moment(data?.created_at).format('Do MMM YYYY HH:mma')}
      </div>
      <Flex className='table-column'>
        <Tag
          tag={{
            color: Utils.getTagColour(colour),
            label: environment?.name,
          }}
          className='chip--sm'
        />
      </Flex>
      <div className='table-column text-right'>
        {data.status === 'SUCCESS' ? (
          <Button disabled={isLoading} onClick={download} size='small'>
            {isLoading ? 'Downloading' : 'Download'}
          </Button>
        ) : (
          <div className='mr-1'>{Format.enumeration.get(data.status)}</div>
        )}
      </div>
    </Row>
  )
}

export default FeatureExportItem
