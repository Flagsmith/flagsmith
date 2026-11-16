import React, { FC, useState } from 'react'
import { Environment, FeatureExport } from 'common/types/responses'
import { getEnvironmentColourById } from 'common/utils/environmentColour'
import moment from 'moment'
import Button from 'components/base/forms/Button'
import Format from 'common/utils/format'
import Chip from 'components/base/Chip'
import { getFeatureExport } from 'common/services/useFeatureExport'
import { getStore } from 'common/store'

type FeatureExportItemType = {
  data: FeatureExport
  // The project's environments, fetched by the export page.
  environments: Environment[]
}

const FeatureExportItem: FC<FeatureExportItemType> = ({
  data,
  environments,
}) => {
  const [isLoading, setIsLoading] = useState(false)

  const environment = environments.find(
    (env) => `${env.id}` === `${data.environment_id}`,
  )
  const colour = getEnvironmentColourById(environments, data.environment_id)

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
        {!!environment && (
          <Chip colour={colour} size='sm'>
            {environment.name}
          </Chip>
        )}
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
