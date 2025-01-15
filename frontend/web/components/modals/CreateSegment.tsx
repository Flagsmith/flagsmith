import React, {
  FC,
  FormEvent,
  useCallback,
  useEffect,
  useMemo,
  useState,
} from 'react'

import Constants from 'common/constants'
import useSearchThrottle from 'common/useSearchThrottle'
import AccountStore from 'common/stores/account-store'
import {
  ChangeRequest,
  EdgePagedResponse,
  Identity,
  Metadata,
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
import Format from 'common/utils/format'
import Utils from 'common/utils/utils'

import AssociatedSegmentOverrides from './AssociatedSegmentOverrides'
import Button from 'components/base/forms/Button'
import InfoMessage from 'components/InfoMessage'
import InputGroup from 'components/base/forms/InputGroup'
import Rule from './Rule'
import TabItem from 'components/base/forms/TabItem'
import Tabs from 'components/base/forms/Tabs'
import ConfigProvider from 'common/providers/ConfigProvider'
import { cloneDeep } from 'lodash'
import ProjectStore from 'common/stores/project-store'
import classNames from 'classnames'
import AddMetadataToEntity, {
  CustomMetadataField,
} from 'components/metadata/AddMetadataToEntity'
import { useGetSupportedContentTypeQuery } from 'common/services/useSupportedContentType'
import { setInterceptClose } from './base/ModalDefault'
import SegmentRuleDivider from 'components/SegmentRuleDivider'
import { useGetProjectQuery } from 'common/services/useProject'
import ChangeRequestModal from './ChangeRequestModal'
import { useCreateProjectChangeRequestMutation } from 'common/services/useProjectChangeRequest'
import ExistingProjectChangeRequestAlert from 'components/ExistingProjectChangeRequestAlert'
import AppActions from 'common/dispatcher/app-actions'
import CreateSegmentRulesTabForm from './CreateSegmentRulesTabForm'
import CreateSegmentUsersTabContent from './CreateSegmentUsersTabContent'

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

enum UserTabs {
  RULES = 0,
  FEATURES = 1,
  USERS = 2,
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
        rules: [
          {
            conditions: [{ ...Constants.defaultRule }],
            rules: [],
            type: 'ANY',
          },
        ],
        type: 'ALL',
      },
    ],
  }
  const [segment, setSegment] = useState(_segment || defaultSegment)
  const [description, setDescription] = useState(segment.description)
  const [name, setName] = useState<Segment['name']>(segment.name)
  const [rules, setRules] = useState<Segment['rules']>(segment.rules)

  useEffect(() => {
    if (segment) {
      setRules(segment.rules)
      setDescription(segment.description)
      setName(segment.name)
    }
  }, [segment])
  const isEdit = !!segment.id
  const { data: project } = useGetProjectQuery(
    { id: `${projectId}` },
    { skip: !projectId },
  )
  const is4Eyes =
    isEdit &&
    Utils.changeRequestsEnabled(project?.minimum_change_request_approvals)

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
  const [createChangeRequest, { isLoading: isCreatingChangeRequest }] =
    useCreateProjectChangeRequestMutation({})
  const isSaving = creating || updating
  const [showDescriptions, setShowDescriptions] = useState(false)
  const [tab, setTab] = useState(UserTabs.RULES)
  const [metadata, setMetadata] = useState<CustomMetadataField[]>(
    segment.metadata,
  )
  const metadataEnable = Utils.getPlansPermission('METADATA')
  const error = createError || updateError
  const totalSegments = ProjectStore.getTotalSegments() ?? 0
  const maxSegmentsAllowed = ProjectStore.getMaxSegmentsAllowed() ?? 0
  const isLimitReached = totalSegments >= maxSegmentsAllowed

  const THRESHOLD = 90
  const segmentsLimitAlert = Utils.calculateRemainingLimitsPercentage(
    totalSegments,
    maxSegmentsAllowed,
    THRESHOLD,
  )
  const { data: supportedContentTypes } = useGetSupportedContentTypeQuery({
    organisation_id: AccountStore.getOrganisation().id,
  })

  const segmentContentType = useMemo(() => {
    if (supportedContentTypes) {
      return Utils.getContentType(supportedContentTypes, 'model', 'segment')
    }
  }, [supportedContentTypes])

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
    setValueChanged(false)
    setMetadataValueChanged(false)
    const segmentData: Omit<Segment, 'id' | 'uuid'> = {
      description,
      feature: feature,
      metadata: metadata as Metadata[],
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

  const fetchUserIdentityList = () => {
    if (!environmentId) return
    identities?.results.forEach((identity) =>
      AppActions.getIdentitySegments(projectId, identity.id),
    )
  }

  const [valueChanged, setValueChanged] = useState(false)
  const [metadataValueChanged, setMetadataValueChanged] = useState(false)
  const onClosing = useCallback(() => {
    return new Promise((resolve) => {
      if (valueChanged) {
        openConfirm({
          body: 'Closing this will discard your unsaved changes.',
          noText: 'Cancel',
          onNo: () => resolve(false),
          onYes: () => resolve(true),
          title: 'Discard changes',
          yesText: 'Ok',
        })
      } else {
        resolve(true)
      }
    })
  }, [valueChanged, isEdit])
  const onCreateChangeRequest = (changeRequestData: {
    approvals: []
    description: string
    title: string
  }) => {
    closeModal2()
    setValueChanged(false)
    createChangeRequest({
      data: {
        approvals: (changeRequestData.approvals || []).filter((v) => !!v.user),
        committed_by: null,
        conflicts: [],
        description: changeRequestData.description,
        group_assignments: (changeRequestData.approvals || []).filter(
          (v) => !!v.group,
        ),
        is_approved: false,
        is_committed: false,
        segments: [
          {
            description,
            feature: feature,
            metadata: metadata as Metadata[],
            name,
            project: projectId,
            rules,
            segment_id: segment.id!,
          },
        ],
        title: changeRequestData.title,
      },
      project_id: `${projectId}`,
    }).then(() => {
      closeModal()
      toast('Created change request')
    })
  }
  useEffect(() => {
    setInterceptClose(onClosing)
    return () => setInterceptClose(null)
  }, [onClosing])
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
      setSegment(createSegmentData)
      onComplete?.(createSegmentData)
      fetchUserIdentityList()
    }
    //eslint-disable-next-line
  }, [createSuccess])
  useEffect(() => {
    if (updateSuccess && updateSegmentData) {
      setSegment(updateSegmentData)
      onComplete?.(updateSegmentData)
      fetchUserIdentityList()
    }
    //eslint-disable-next-line
  }, [updateSuccess])

  const operators: Operator[] | null = _operators || Utils.getSegmentOperators()
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
  const rulesToShow = rules[0].rules.filter((v) => !v.delete)
  const rulesEl = (
    <div className='overflow-visible'>
      <div>
        <div className='mb-4'>
          {rules[0].rules.map((rule, i) => {
            if (rule.delete) {
              return null
            }
            const displayIndex = rulesToShow.indexOf(rule)
            return (
              <div key={i}>
                <SegmentRuleDivider rule={rule} index={displayIndex} />
                <Rule
                  showDescription={showDescriptions}
                  readOnly={readOnly}
                  data-test={`rule-${displayIndex}`}
                  rule={rule}
                  operators={operators}
                  onRemove={() => {
                    setValueChanged(true)
                    removeRule(0, i)
                  }}
                  onChange={(v: SegmentRule) => {
                    setValueChanged(true)
                    updateRule(0, i, v)
                  }}
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
        </Row>
      </div>
    </div>
  )

  const Tab1 = (
    <form id='create-segment-modal' onSubmit={save}>
      {!condensed && (
        <div className='mt-3'>
          <InfoMessage collapseId={'value-type-conversions'}>
            Learn more about rule and trait value type conversions{' '}
            <a href='https://docs.flagsmith.com/basic-features/segments#rule-typing'>
              here
            </a>
            .
          </InfoMessage>
          {segmentsLimitAlert.percentage &&
            Utils.displayLimitAlert('segments', segmentsLimitAlert.percentage)}
        </div>
      )}

      <div className='mb-3'>
        <label htmlFor='segmentID'>Name*</label>
        <Flex>
          <Input
            data-test='segmentID'
            name='id'
            id='segmentID'
            maxLength={SEGMENT_ID_MAXLENGTH}
            value={name}
            onChange={(e: InputEvent) => {
              setValueChanged(true)
              setName(
                Format.enumeration
                  .set(Utils.safeParseEventValue(e))
                  .toLowerCase(),
              )
            }}
            isValid={name && name.length}
            type='text'
            placeholder='E.g. power_users'
          />
        </Flex>
      </div>
      {!condensed && (
        <InputGroup
          className='mb-3'
          value={description}
          inputProps={{
            className: 'full-width',
            name: 'featureDesc',
            readOnly: !!identity || readOnly,
          }}
          onChange={(e: InputEvent) => {
            setValueChanged(true)
            setDescription(Utils.safeParseEventValue(e))
          }}
          isValid={name && name.length}
          type='text'
          title='Description'
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
            Show condition descriptions
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
              is4Eyes ? (
                <Button
                  onClick={() => {
                    openModal2(
                      'New Change Request',
                      <ChangeRequestModal
                        showAssignees={is4Eyes}
                        hideSchedule
                        onSave={onCreateChangeRequest}
                      />,
                    )
                  }}
                  data-test='update-segment'
                  id='update-feature-btn'
                  disabled={isSaving || !name || !isValid}
                >
                  {isSaving ? 'Creating' : 'Create Change Request'}
                </Button>
              ) : (
                <Button
                  type='submit'
                  data-test='update-segment'
                  id='update-feature-btn'
                  disabled={isSaving || !name || !isValid}
                >
                  {isSaving ? 'Creating' : 'Update Segment'}
                </Button>
              )
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

  const MetadataTab = (
    <FormGroup className='mt-5 setting'>
      <InputGroup
        component={
          <AddMetadataToEntity
            organisationId={AccountStore.getOrganisation().id}
            projectId={projectId}
            entityId={`${segment.id}` || ''}
            entityContentType={segmentContentType?.id}
            entity={segmentContentType?.model}
            onChange={(m: CustomMetadataField[]) => {
              setMetadata(m)
              if (isEdit) {
                setMetadataValueChanged(true)
              }
            }}
          />
        }
      />
    </FormGroup>
  )

  return (
    <>
      <ExistingProjectChangeRequestAlert
        className='m-2'
        projectId={`${projectId}`}
        segmentId={`${segment.id}`}
      />
      {isEdit && !condensed ? (
        <Tabs value={tab} onChange={(tab: UserTabs) => setTab(tab)}>
          <TabItem
            tabLabelString='Rules'
            tabLabel={
              <Row className='justify-content-center'>
                Rules{' '}
                {valueChanged && <div className='unread ml-2 px-1'>{'*'}</div>}
              </Row>
            }
          >
            <div className='my-4'>
              <CreateSegmentRulesTabForm
                save={save}
                condensed={condensed}
                segmentsLimitAlert={segmentsLimitAlert}
                name={name}
                setName={setName}
                setValueChanged={setValueChanged}
                description={description}
                setDescription={setDescription}
                identity={identity}
                readOnly={readOnly}
                showDescriptions={showDescriptions}
                setShowDescriptions={setShowDescriptions}
                allWarnings={allWarnings}
                rulesEl={rulesEl}
                error={error}
                isEdit={isEdit}
                segment={segment}
                isSaving={isSaving}
                isValid={isValid}
                isLimitReached={isLimitReached}
                onCancel={onCancel}
              />
            </div>
          </TabItem>
          <TabItem tabLabel='Features'>
            <div className='my-4'>
              <AssociatedSegmentOverrides
                onUnsavedChange={() => {
                  setValueChanged(true)
                }}
                feature={segment.feature}
                projectId={projectId}
                id={segment.id}
                environmentId={environmentId}
              />
            </div>
          </TabItem>
          <TabItem tabLabel='Users'>
            <CreateSegmentUsersTabContent
              projectId={projectId}
              environmentId={environmentId}
              setEnvironmentId={setEnvironmentId}
              identitiesLoading={identitiesLoading}
              identities={identities}
              page={page}
              setPage={setPage}
              name={name}
              searchInput={searchInput}
              setSearchInput={setSearchInput}
            />
          </TabItem>
          {metadataEnable && segmentContentType?.id && (
            <TabItem
              tabLabelString='Custom Fields'
              tabLabel={
                <Row className='justify-content-center'>
                  Custom Fields
                  {metadataValueChanged && (
                    <div className='unread ml-2 px-1'>{'*'}</div>
                  )}
                </Row>
              }
            >
              <div className={className || 'my-3 mx-4'}>{MetadataTab}</div>
            </TabItem>
          )}
        </Tabs>
      ) : metadataEnable && segmentContentType?.id ? (
        <Tabs value={tab} onChange={(tab: UserTabs) => setTab(tab)}>
          <TabItem
            tabLabelString='Basic configuration'
            tabLabel={'Basic configuration'}
          >
            <div className={className || 'my-3 mx-4'}>{Tab1}</div>
          </TabItem>
          <TabItem
            tabLabelString='Custom Fields'
            tabLabel={
              <Row className='justify-content-center'>Custom Fields</Row>
            }
          >
            <div className={className || 'my-3 mx-4'}>{MetadataTab}</div>
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
  onSegmentRetrieved?: (segment: Segment) => void
  onComplete?: (segment: Segment) => void
  projectId: string
  segment?: number
}

const LoadingCreateSegment: FC<LoadingCreateSegmentType> = (props) => {
  const [environmentId, setEnvironmentId] = useState(props.environmentId)
  const { data: segmentData, isLoading: segmentLoading } = useGetSegmentQuery(
    {
      id: `${props.segment}`,
      projectId: `${props.projectId}`,
    },
    { skip: !props.segment },
  )
  const { isLoading: projectLoading } = useGetProjectQuery(
    { id: `${props.projectId}` },
    { skip: !props.projectId },
  )
  const isLoading = projectLoading || segmentLoading
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

  useEffect(() => {
    if (segmentData) {
      props.onSegmentRetrieved?.(segmentData)
    }
  }, [segmentData])
  const isEdge = Utils.getIsEdge()

  const { data: identities, isLoading: identitiesLoading } =
    useGetIdentitiesQuery(
      {
        environmentId,
        isEdge,
        page: page.number,
        pageType: page.pageType,
        page_size: 10,
        pages: page.pages,
        search,
      },
      {
        skip: !environmentId,
      },
    )

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
