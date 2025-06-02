import React, { FC, useState } from 'react' // we need this to make JSX compile
import ConfigProvider from 'common/providers/ConfigProvider'
import Utils from 'common/utils/utils'
import { SplitTestResult } from 'common/types/responses'
import { useRouteMatch } from 'react-router-dom'
import PageTitle from 'components/PageTitle'
import ConversionEventSelect from 'components/ConversionEventSelect'
import InfoMessage from 'components/InfoMessage'
import PanelSearch from 'components/PanelSearch'
import ErrorMessage from 'components/ErrorMessage'
import useSearchThrottle from 'common/useSearchThrottle'
import { useGetSplitTestQuery } from 'common/services/useSplitTest'
import { IonIcon } from '@ionic/react'
import { chevronDown, chevronForward } from 'ionicons/icons'
import Confidence from 'components/Confidence'
import FeatureValue from 'components/FeatureValue'

interface RouteParams {
  environmentId: string
  projectId: string
}

const pageSize = 10
const widths = [200, 200, 150]
const innerWidths = [200, 150, 150]

const SplitTestPage: FC = () => {
  const match = useRouteMatch<RouteParams>()
  const environmentId = match?.params?.environmentId
  const { search, searchInput, setSearchInput } = useSearchThrottle()
  const [conversion_event_type_id, setConversionEvent] = useState<
    number | null
  >(null)

  const [expanded, setExpanded] = useState(-1)

  const [page, setPage] = useState(1)
  const { data, error, isLoading } = useGetSplitTestQuery(
    {
      conversion_event_type_id: `${conversion_event_type_id}`,
      page,
      page_size: 1000,
    },
    { skip: !conversion_event_type_id },
  )

  const renderRow = (item: SplitTestResult, i: number) => (
    <>
      <div
        onClick={() => {
          setExpanded(expanded === i ? -1 : i)
        }}
        className='flex-row align-items-center space list-item clickable py-2'
      >
        <div className='px-2 user-select-none flex-row d-flex flex-fill'>
          <span
            className='d-flex align-items-end text-center'
            style={{ lineHeight: '24px', width: 24 }}
          >
            <IonIcon icon={expanded === i ? chevronDown : chevronForward} />
          </span>

          {item.feature.name}
        </div>
        <div className='table-column' style={{ width: widths[0] }}>
          {item.max_conversion_count}({item.max_conversion_percentage}%)
        </div>
        <div className='table-column' style={{ width: widths[1] }}>
          {item.conversion_variance}%
        </div>
        <div className='table-column' style={{ width: widths[2] }}>
          <Confidence pValue={item.max_conversion_pvalue} />
        </div>
      </div>
      {expanded === i && (
        <div className='px-2'>
          <Row className='table-header'>
            <div className='table-column flex-fill'>Value</div>
            <div className='table-column' style={{ width: innerWidths[0] }}>
              Conversion Events
            </div>
            <div className='table-column' style={{ width: innerWidths[1] }}>
              Evaluations
            </div>
            <div className='table-column' style={{ width: innerWidths[2] }}>
              Conversion %
            </div>
          </Row>
          {item.results?.map((v, i) => (
            <div
              key={i}
              className='flex-row align-items-center space list-item clickable py-2'
            >
              <div className='table-column flex-fill'>
                <FeatureValue value={Utils.featureStateToValue(v.value_data)} />
              </div>
              <div className='table-column' style={{ width: innerWidths[0] }}>
                {v.conversion_count}
              </div>
              <div className='table-column' style={{ width: innerWidths[1] }}>
                {v.evaluation_count}
              </div>
              <div className='table-column' style={{ width: innerWidths[2] }}>
                {v.conversion_percentage}%
              </div>
            </div>
          ))}
        </div>
      )}
    </>
  )
  return (
    <div className='app-container container'>
      <PageTitle title={'Split Tests'}>
        Monitor conversion events against your multivariate feature flags.
      </PageTitle>
      <div className='flex-row my-4'>
        Conversion Event{' '}
        <div className={'ms-2'} style={{ width: 200 }}>
          <ConversionEventSelect
            environmentId={environmentId}
            onChange={setConversionEvent}
          />
        </div>
      </div>
      {!conversion_event_type_id ? (
        <InfoMessage className='mt-2'>
          Select a conversion event to view split test results
        </InfoMessage>
      ) : (
        <>
          <ErrorMessage>{error}</ErrorMessage>
          <PanelSearch
            title='Split Tests'
            isLoading={isLoading}
            className='no-pad'
            items={data?.results}
            search={searchInput}
            onChange={(e: InputEvent) => {
              setSearchInput(Utils.safeParseEventValue(e))
            }}
            goToPage={(page: number) => {
              setPage(page)
            }}
            filterRow={(value: SplitTestResult, search: string) => {
              return value.feature.name.toLowerCase().includes(search)
            }}
            renderRow={renderRow}
            header={
              <Row className='table-header'>
                <div className='table-column flex-fill'>Feature</div>
                <div className='table-column' style={{ width: widths[0] }}>
                  Max Conversion
                </div>
                <div className='table-column' style={{ width: widths[1] }}>
                  Conversion Variance
                </div>
                <div className='table-column' style={{ width: widths[2] }}>
                  Confidence
                </div>
              </Row>
            }
          />
        </>
      )}
    </div>
  )
}

export default ConfigProvider(SplitTestPage)
