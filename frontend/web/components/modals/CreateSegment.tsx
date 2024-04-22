import React, { FC, FormEvent, useEffect, useMemo, useState } from 'react'

import Constants from 'common/constants'
import useSearchThrottle from 'common/useSearchThrottle'
import {
  EdgePagedResponse,
  Identity,
  Operator,
  Segment,
  SegmentRule,
} from 'common/types/responses'
import { Req } from 'common/types/requests'
import { useGetIdentitiesQuery } from 'common/services/useIdentity'
import {
  useCreateSegmentMutation,
  useGetSegmentQuery,
  useUpdateSegmentMutation,
} from 'common/services/useSegment'
import IdentitySegmentsProvider from 'common/providers/IdentitySegmentsProvider'
import Format from 'common/utils/format'
import Utils from 'common/utils/utils'

import AssociatedSegmentOverrides from './AssociatedSegmentOverrides'
import Button from 'components/base/forms/Button'
import EnvironmentSelect from 'components/EnvironmentSelect'
import InfoMessage from 'components/InfoMessage'
import Input from 'components/base/forms/Input'
import InputGroup from 'components/base/forms/InputGroup'
import PanelSearch from 'components/PanelSearch'
import Rule from './Rule'
import Switch from 'components/Switch'
import TabItem from 'components/base/forms/TabItem'
import Tabs from 'components/base/forms/Tabs'
import ConfigProvider from 'common/providers/ConfigProvider'
import JSONReference from 'components/JSONReference'
import { cloneDeep } from 'lodash'
import ErrorMessage from 'components/ErrorMessage'
import ProjectStore from 'common/stores/project-store'
import Icon from 'components/Icon'
import Permission from 'common/providers/Permission'
import classNames from 'classnames'

type PageType = {
  number: number
  pageType: Req['getIdentities']['pageType']
  pages: Req['getIdentities']['pages']
}

type CreateSegmentType = {
  className?: string
  projectId: number | string
  searchInput: string
  environmentId: string
  identitiesLoading: boolean
  setEnvironmentId: (env: string) => void
  setSearchInput: (search: string) => void
  page: PageType
  setPage: (page: PageType) => void
  feature?: number
  identities?: EdgePagedResponse<Identity>
  identity?: boolean
  condensed?: boolean
  isEdit?: boolean
  onCancel?: () => void
  onComplete?: (segment: Segment) => void
  readOnly?: boolean
  segment?: Segment
}

let _operators: Operator[] | null = null
const CreateSegment: FC<CreateSegmentType> = ({
  className,
  condensed,
  environmentId,
  feature,
  identities,
  identitiesLoading,
  identity,
  isEdit,
  onCancel,
  onComplete,
  page,
  projectId,
  readOnly,
  searchInput,
  segment: _segment,
  setEnvironmentId,
  setPage,
  setSearchInput,
}) => {
  const SEGMENT_ID_MAXLENGTH = Constants.forms.maxLength.SEGMENT_ID

  const defaultSegment: Omit<Segment, 'id' | 'uuid' | 'project'> & {
    id?: number
    uuid?: string
    project?: number
  } = {
    description: '',
    name: '',
    rules: [
      {
        conditions: [],
        rules: [],
        type: 'ALL',
      },
    ],
  }
  const segment = _segment || defaultSegment
  const [
    createSegment,
    {
      data: createSegmentData,
      error: createError,
      isLoading: creating,
      isSuccess: createSuccess,
    },
  ] = useCreateSegmentMutation()
  const [
    editSegment,
    {
      data: updateSegmentData,
      error: updateError,
      isLoading: updating,
      isSuccess: updateSuccess,
    },
  ] = useUpdateSegmentMutation()

  const isSaving = creating || updating
  const [showDescriptions, setShowDescriptions] = useState(false)
  const [description, setDescription] = useState(segment.description)
  const [name, setName] = useState<Segment['name']>(segment.name)
  const [rules, setRules] = useState<Segment['rules']>(segment.rules)
  const [tab, setTab] = useState(0)

  const error = createError || updateError
  const isLimitReached =
    ProjectStore.getTotalSegments() >= ProjectStore.getMaxSegmentsAllowed()

  const THRESHOLD = 90
  const segmentsLimitAlert = Utils.calculateRemainingLimitsPercentage(
    ProjectStore.getTotalSegments(),
    ProjectStore.getMaxSegmentsAllowed(),
    THRESHOLD,
  )

  const addRule = (type = 'ANY') => {
    const newRules = cloneDeep(rules)
    newRules[0].rules = newRules[0].rules.concat({
      conditions: [{ ...Constants.defaultRule }],
      rules: [],
      type,
    })
    setRules(newRules)
  }

  const updateRule = (
    rulesIndex: number,
    elementNumber: number,
    newValue: SegmentRule,
  ) => {
    const newRules = cloneDeep(rules)
    newRules[0].rules[elementNumber] = newValue
    setRules(newRules)
  }

  const removeRule = (rulesIndex: number, elementNumber: number) => {
    const newRules = cloneDeep(rules)
    newRules[0].rules.splice(elementNumber, 1)
    setRules(newRules)
  }

  const save = (e: FormEvent) => {
    Utils.preventDefault(e)
    const segmentData: Omit<Segment, 'id' | 'uuid'> = {
      description,
      feature: feature,
      name,
      project: projectId,
      rules,
    }
    if (name) {
      if (segment.id) {
        editSegment({
          projectId,
          segment: {
            ...segmentData,
            id: segment.id,
            project: segment.project as number,
            uuid: segment.uuid as string,
          },
        })
      } else {
        createSegment({
          projectId,
          segment: segmentData,
        })
      }
    }
  }

  const isValid = useMemo(() => {
    if (!rules[0]?.rules?.find((v) => !v.delete)) {
      return false
    }
    const res = rules[0].rules.find((v) =>
      v.conditions.find((c) => !Utils.validateRule(c)),
    )
    return !res
  }, [rules])

  useEffect(() => {
    setTimeout(() => {
      document.getElementById('segmentID')?.focus()
    }, 500)
  }, [])
  useEffect(() => {
    if (createSuccess && createSegmentData) {
      onComplete?.(createSegmentData)
    }
    //eslint-disable-next-line
  }, [createSuccess])
  useEffect(() => {
    if (updateSuccess && updateSegmentData) {
      onComplete?.(updateSegmentData)
    }
    //eslint-disable-next-line
  }, [updateSuccess])
  const operators: Operator[] | null =
    _operators || Utils.getFlagsmithValue('segment_operators')
      ? JSON.parse(Utils.getFlagsmithValue('segment_operators'))
      : null
  if (operators) {
    _operators = operators
  }

  const allWarnings = useMemo(() => {
    const warnings: string[] = []
    const parseRules = (
      rules: SegmentRule[] | null,
      _operators: Operator[],
    ) => {
      rules?.map((v) => {
        v?.conditions?.map((condition) => {
          const operatorObj = operators?.find(
            (op) => op.value === condition.operator,
          )
          if (
            operatorObj?.warning &&
            !warnings?.includes(operatorObj.warning)
          ) {
            warnings.push(operatorObj.warning)
          }
        })
        parseRules(v.rules, operators!)
      })
    }
    if (operators) {
      parseRules(rules, operators)
    }
    return warnings
  }, [operators, rules])
  //Find any non-deleted rules
  const hasNoRules = !rules[0]?.rules?.find((v) => !v.delete)

  const rulesEl = (
    <div className='overflow-visible'>
      <div>
        <div className='mb-4'>
          {rules[0].rules
            ?.filter((v) => !v?.delete)
            .map((rule, i) => {
              return (
                <div key={i}>
                  <Row
                    className={classNames('and-divider my-1', {
                      'text-danger': rule.type !== 'ANY',
                    })}
                  >
                    <Flex className='and-divider__line' />
                    {Format.camelCase(
                      `${i > 0 ? 'And ' : ''}${
                        rule.type === 'ANY'
                          ? 'Any of the following'
                          : 'None of the following'
                      }`,
                    )}
                    <Flex className='and-divider__line' />
                  </Row>
                  <Rule
                    showDescription={showDescriptions}
                    readOnly={readOnly}
                    data-test={`rule-${i}`}
                    rule={rule}
                    operators={operators}
                    onRemove={() => removeRule(0, i)}
                    onChange={(v: SegmentRule) => updateRule(0, i, v)}
                  />
                </div>
              )
            })}
        </div>
        {hasNoRules && (
          <InfoMessage>
            Add at least one AND/NOT rule to create a segment.
          </InfoMessage>
        )}
        <Row className='justify-content-end'>
          {!readOnly && (
            <div onClick={() => addRule('ANY')} className='text-center'>
              <Button theme='outline' data-test='add-rule' type='button'>
                Add AND Condition
              </Button>
            </div>
          )}
          {!readOnly && Utils.getFlagsmithHasFeature('not_operator') && (
            <div onClick={() => addRule('NONE')} className='text-center'>
              <Button
                theme='outline'
                className='ml-2 btn--outline-danger'
                data-test='add-rule'
                type='button'
              >
                Add AND NOT Condition
              </Button>
            </div>
          )}
        </Row>
      </div>
    </div>
  )

  const Tab1 = (
    <form id='create-segment-modal' onSubmit={save}>
      {!condensed && (
        <div className='mt-3'>
          <InfoMessage>
            Learn more about rule and trait value type conversions{' '}
            <a href='https://docs.flagsmith.com/basic-features/managing-segments#rule-typing'>
              here
            </a>
            .
          </InfoMessage>
          {segmentsLimitAlert.percentage &&
            Utils.displayLimitAlert('segments', segmentsLimitAlert.percentage)}
        </div>
      )}

      {!isEdit && (
        <div className='mb-3'>
          <label htmlFor='segmentID'>ID</label>
          <Flex>
            <Input
              data-test='segmentID'
              name='id'
              id='segmentID'
              readOnly={isEdit}
              maxLength={SEGMENT_ID_MAXLENGTH}
              value={name}
              onChange={(e: InputEvent) =>
                setName(
                  Format.enumeration
                    .set(Utils.safeParseEventValue(e))
                    .toLowerCase(),
                )
              }
              isValid={name && name.length}
              type='text'
              title={isEdit ? 'ID' : 'ID*'}
              placeholder='E.g. power_users'
            />
          </Flex>
        </div>
      )}
      {!condensed && (
        <InputGroup
          className='mb-3'
          value={description}
          inputProps={{
            className: 'full-width',
            name: 'featureDesc',
            readOnly: !!identity || readOnly,
          }}
          onChange={(e: InputEvent) =>
            setDescription(Utils.safeParseEventValue(e))
          }
          isValid={name && name.length}
          type='text'
          title='Description (optional)'
          placeholder="e.g. 'People who have spent over $100' "
        />
      )}

      <div className='form-group '>
        <Row className='mb-3'>
          <Switch
            checked={showDescriptions}
            onChange={() => {
              setShowDescriptions(!showDescriptions)
            }}
            className={'ml-0'}
          />
          <span
            style={{ fontWeight: 'normal', marginLeft: '12px' }}
            className='mb-0 fs-small text-dark'
          >
            {showDescriptions
              ? 'Hide condition descriptions'
              : 'Show condition descriptions'}
          </span>
        </Row>
        <Flex className='mb-3'>
          <label className='cols-sm-2 control-label mb-1'>
            Include users when all of the following rules apply:
          </label>
          <span className='fs-caption text-faint'>
            Note: Trait names are case sensitive
          </span>
        </Flex>
        {allWarnings?.map((warning, i) => (
          <InfoMessage key={i}>
            <div dangerouslySetInnerHTML={{ __html: warning }} />
          </InfoMessage>
        ))}
        {rulesEl}
      </div>

      <ErrorMessage error={error} />
      {isEdit && <JSONReference title={'Segment'} json={segment} />}
      {readOnly ? (
        <div className='text-right'>
          <Tooltip
            title={
              <Button
                disabled
                data-test='show-create-feature-btn'
                id='show-create-feature-btn'
              >
                Update Segment
              </Button>
            }
            place='left'
          >
            {Constants.projectPermissions('Admin')}
          </Tooltip>
        </div>
      ) : (
        <div className='text-right' style={{ marginTop: '32px' }}>
          <Row className='justify-content-end'>
            {condensed && (
              <Button
                theme='secondary'
                type='button'
                onClick={onCancel}
                className='mr-2'
              >
                Cancel
              </Button>
            )}
            {isEdit ? (
              <Button
                type='submit'
                data-test='update-segment'
                id='update-feature-btn'
                disabled={isSaving || !name || !isValid}
              >
                {isSaving ? 'Creating' : 'Update Segment'}
              </Button>
            ) : (
              <Button
                disabled={isSaving || !name || !isValid || isLimitReached}
                type='submit'
                data-test='create-segment'
                id='create-feature-btn'
              >
                {isSaving ? 'Creating' : 'Create Segment'}
              </Button>
            )}
          </Row>
        </div>
      )}
    </form>
  )

  return (
    <>
      {isEdit && !condensed ? (
        <Tabs value={tab} onChange={(tab: number) => setTab(tab)}>
          <TabItem tabLabel='Rules'>
            <div className='my-4'>{Tab1}</div>
          </TabItem>
          <TabItem tabLabel='Features'>
            <div className='my-4'>
              <Permission
                level='environment'
                permission={'MANAGE_SEGMENT_OVERRIDES'}
                id={environmentId}
              >
                {({ permission: manageSegmentOverrides }) => {
                  const isReadOnly = !manageSegmentOverrides
                  return (
                    <AssociatedSegmentOverrides
                      feature={segment.feature}
                      projectId={projectId}
                      id={segment.id}
                      readOnly={isReadOnly}
                    />
                  )
                }}
              </Permission>
            </div>
          </TabItem>
          <TabItem tabLabel='Users'>
            <div className='my-4'>
              <InfoMessage>
                This is a random sample of Identities who are either in or out
                of this Segment based on the current Segment rules.
              </InfoMessage>
              <div className='mt-2'>
                <FormGroup>
                  <InputGroup
                    title='Environment'
                    component={
                      <EnvironmentSelect
                        projectId={`${projectId}`}
                        value={environmentId}
                        onChange={(environmentId: string) => {
                          setEnvironmentId(environmentId)
                        }}
                      />
                    }
                  />
                  <PanelSearch
                    renderSearchWithNoResults
                    id='users-list'
                    title='Segment Users'
                    className='no-pad'
                    isLoading={identitiesLoading}
                    items={identities?.results}
                    paging={identities}
                    showExactFilter
                    nextPage={() => {
                      setPage({
                        number: page.number + 1,
                        pageType: 'NEXT',
                        pages: identities?.last_evaluated_key
                          ? (page.pages || []).concat([
                              identities?.last_evaluated_key,
                            ])
                          : undefined,
                      })
                    }}
                    prevPage={() => {
                      setPage({
                        number: page.number - 1,
                        pageType: 'PREVIOUS',
                        pages: page.pages
                          ? Utils.removeElementFromArray(
                              page.pages,
                              page.pages.length - 1,
                            )
                          : undefined,
                      })
                    }}
                    goToPage={(newPage: number) => {
                      setPage({
                        number: newPage,
                        pageType: undefined,
                        pages: undefined,
                      })
                    }}
                    renderRow={(
                      { id, identifier }: { id: string; identifier: string },
                      index: number,
                    ) => (
                      <Row
                        key={id}
                        className='list-item list-item-sm clickable'
                      >
                        <IdentitySegmentsProvider
                          fetch
                          id={id}
                          projectId={projectId}
                        >
                          {({ segments }: { segments?: Segment[] }) => {
                            let inSegment = false
                            if (segments?.find((v) => v.name === name)) {
                              inSegment = true
                            }
                            return (
                              <Row
                                space
                                className='px-3'
                                key={id}
                                data-test={`user-item-${index}`}
                              >
                                <div className='font-weight-medium'>
                                  {identifier}
                                </div>
                                <Row
                                  className={`font-weight-medium fs-small lh-sm ${
                                    inSegment ? 'text-primary' : 'faint'
                                  }`}
                                >
                                  {inSegment ? (
                                    <>
                                      <Icon
                                        name='checkmark-circle'
                                        width={20}
                                        fill='#6837FC'
                                      />
                                      <span className='ml-1'>
                                        User in segment
                                      </span>
                                    </>
                                  ) : (
                                    <>
                                      <Icon
                                        name='minus-circle'
                                        width={20}
                                        fill='#9DA4AE'
                                      />
                                      <span className='ml-1'>
                                        Not in segment
                                      </span>
                                    </>
                                  )}
                                </Row>
                              </Row>
                            )
                          }}
                        </IdentitySegmentsProvider>
                      </Row>
                    )}
                    filterRow={() => true}
                    search={searchInput}
                    onChange={(e: InputEvent) => {
                      setSearchInput(Utils.safeParseEventValue(e))
                    }}
                  />
                </FormGroup>
              </div>
            </div>
          </TabItem>
        </Tabs>
      ) : (
        <div className={className || 'my-3 mx-4'}>{Tab1}</div>
      )}
    </>
  )
}

type LoadingCreateSegmentType = {
  condensed?: boolean
  environmentId: string
  isEdit?: boolean
  readOnly?: boolean
  onComplete?: () => void
  projectId: string
  segment?: number
}

const LoadingCreateSegment: FC<LoadingCreateSegmentType> = (props) => {
  const [environmentId, setEnvironmentId] = useState(props.environmentId)
  const { data: segmentData, isLoading } = useGetSegmentQuery(
    {
      id: `${props.segment}`,
      projectId: `${props.projectId}`,
    },
    { skip: !props.segment },
  )

  const [page, setPage] = useState<PageType>({
    number: 1,
    pageType: undefined,
    pages: undefined,
  })

  const { search, searchInput, setSearchInput } = useSearchThrottle(
    Utils.fromParam().search,
    () => {
      setPage({
        number: 1,
        pageType: undefined,
        pages: undefined,
      })
    },
  )

  const isEdge = Utils.getIsEdge()

  const { data: identities, isLoading: identitiesLoading } =
    useGetIdentitiesQuery({
      environmentId,
      isEdge,
      page: page.number,
      pageType: page.pageType,
      page_size: 10,
      pages: page.pages,
      search,
    })

  return isLoading ? (
    <div className='text-center'>
      <Loader />
    </div>
  ) : (
    <CreateSegment
      {...props}
      segment={segmentData || undefined}
      identities={identities}
      setPage={setPage}
      searchInput={searchInput}
      setSearchInput={setSearchInput}
      identitiesLoading={identitiesLoading}
      page={page}
      environmentId={environmentId}
      setEnvironmentId={setEnvironmentId}
    />
  )
}

export default LoadingCreateSegment

module.exports = ConfigProvider(LoadingCreateSegment)
