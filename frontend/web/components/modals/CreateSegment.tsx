import React, {
  FC,
  FormEvent,
  useCallback,
  useEffect,
  useMemo,
  useState,
} from 'react'

import Constants from 'common/constants'
import AccountStore from 'common/stores/account-store'
import {
  EdgePagedResponse,
  Identity,
  Metadata,
  Operator,
  Segment,
  SegmentRule,
  SegmentConditionsError,
} from 'common/types/responses'
import { Req } from 'common/types/requests'
import { useGetIdentitiesQuery } from 'common/services/useIdentity'
import {
  useCreateSegmentMutation,
  useGetSegmentQuery,
  useGetSegmentsQuery,
  useUpdateSegmentMutation,
} from 'common/services/useSegment'
import Utils from 'common/utils/utils'
import AssociatedSegmentOverrides from './AssociatedSegmentOverrides'
import Button from 'components/base/forms/Button'
import InfoMessage from 'components/InfoMessage'
import InputGroup from 'components/base/forms/InputGroup'
import Rule from 'components/segments/Rule/Rule'
import TabItem from 'components/navigation/TabMenu/TabItem'
import Tabs from 'components/navigation/TabMenu/Tabs'
import ConfigProvider from 'common/providers/ConfigProvider'
import { cloneDeep } from 'lodash'
import ProjectStore from 'common/stores/project-store'
import AddMetadataToEntity from 'components/metadata/AddMetadataToEntity'
import { useGetSupportedContentTypeQuery } from 'common/services/useSupportedContentType'
import { setInterceptClose } from './base/ModalDefault'
import SegmentRuleDivider from 'components/SegmentRuleDivider'
import { useGetProjectQuery } from 'common/services/useProject'
import { useCreateProjectChangeRequestMutation } from 'common/services/useProjectChangeRequest'
import ExistingProjectChangeRequestAlert from 'components/ExistingProjectChangeRequestAlert'
import CreateSegmentRulesTabForm from './CreateSegmentRulesTabForm'
import CreateSegmentUsersTabContent from './CreateSegmentUsersTabContent'
import useDebouncedSearch from 'common/useDebouncedSearch'
import API from 'project/api'

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
type CreateSegmentError = {
  status: number
  data: {
    rules: [
      {
        rules: Array<{
          conditions: SegmentConditionsError[]
        }>
      },
    ]
  }
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
    metadata: [],
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
  const { data: segments } = useGetSegmentsQuery({
    include_feature_specific: true,
    projectId,
  })
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
  const [metadata, setMetadata] = useState<Metadata[]>(segment.metadata)
  const metadataEnable = Utils.getPlansPermission('METADATA')
  const error: CreateSegmentError = createError || updateError
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

  const save = async (e: FormEvent) => {
    try {
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
          await editSegment({
            projectId,
            segment: {
              ...segmentData,
              id: segment.id,
              project: segment.project as number,
              uuid: segment.uuid as string,
            },
          }).unwrap()
        } else {
          const res = await createSegment({
            projectId,
            segment: segmentData,
          }).unwrap()
          if (!segments?.results?.length) {
            API.trackEvent(Constants.events.CREATE_FIRST_SEGMENT)
          }
        }
      }
    } catch (error: any) {
      toast(error?.data?.metadata?.[0] || 'Error creating segment', 'danger')
    }
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
  const onCreateChangeRequest = async (changeRequestData: {
    approvals: []
    description: string
    title: string
  }) => {
    closeModal2()
    setValueChanged(false)

    try {
      await createChangeRequest({
        data: {
          approvals: (changeRequestData.approvals || []).filter(
            (v) => !!v.user,
          ),
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
              feature,
              metadata: metadata as Metadata[],
              name,
              project: projectId,
              rules,
              version_of: segment.id!,
            },
          ],
          title: changeRequestData.title,
        },
        project_id: `${projectId}`,
      })

      toast('Created change request')
    } catch (error) {
      console.error('Failed to create change request:', error)
      toast('Failed to create change request')
    }
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
      toast('Created segment')
      onComplete?.(createSegmentData)
    }
    //eslint-disable-next-line
  }, [createSuccess])
  useEffect(() => {
    if (updateSuccess && updateSegmentData) {
      setSegment(updateSegmentData)
      toast('Updated segment')
      onComplete?.(updateSegmentData)
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
                  index={i}
                  operators={operators!}
                  onChange={(v: SegmentRule) => {
                    setValueChanged(true)
                    updateRule(0, i, v)
                  }}
                  errors={error?.data?.rules?.[0]?.rules?.[i]?.conditions}
                  projectId={projectId}
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
            onChange={(m) => {
              setMetadata(m as Metadata[])
              // Need to fix this to be more robust and handle post save
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
            <div className='my-4 col-lg-8'>
              <CreateSegmentRulesTabForm
                is4Eyes={is4Eyes}
                onCreateChangeRequest={onCreateChangeRequest}
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
            <div className='my-4 col-lg-8'>
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
            <div className='my-4 col-lg-8'>
              <CreateSegmentUsersTabContent
                projectId={projectId}
                environmentId={environmentId}
                setEnvironmentId={setEnvironmentId}
                identitiesLoading={identitiesLoading}
                identities={identities!}
                page={page}
                setPage={setPage}
                name={name}
                searchInput={searchInput}
                setSearchInput={setSearchInput}
              />
            </div>
          </TabItem>
          {metadataEnable && segmentContentType?.id && (
            <TabItem
              tabLabelString='Custom Fields'
              tabLabel={
                <Row className='justify-content-center'>
                  Custom Fields
                  {metadataValueChanged && (
                    <div className='unread ml-2 px-1 pt-2'>{'*'}</div>
                  )}
                </Row>
              }
            >
              <div className='my-4 col-lg-8'>{MetadataTab}</div>
            </TabItem>
          )}
        </Tabs>
      ) : metadataEnable && segmentContentType?.id ? (
        <Tabs value={tab} onChange={(tab: UserTabs) => setTab(tab)}>
          <TabItem
            tabLabelString='Basic configuration'
            tabLabel={'Basic configuration'}
          >
            <div className={className || 'my-3 mx-4'}>
              <CreateSegmentRulesTabForm
                save={save}
                is4Eyes={is4Eyes}
                onCreateChangeRequest={onCreateChangeRequest}
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
                isEdit={isEdit}
                segment={segment}
                isSaving={isSaving}
                isValid={isValid}
                isLimitReached={isLimitReached}
                onCancel={onCancel}
              />
            </div>
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
        <div className={className || 'my-3 mx-4'}>
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
            isEdit={isEdit}
            segment={segment}
            isSaving={isSaving}
            isValid={isValid}
            isLimitReached={isLimitReached}
            onCancel={onCancel}
          />
        </div>
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

  const { search, searchInput, setSearchInput } = useDebouncedSearch('')

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
        q: search,
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
