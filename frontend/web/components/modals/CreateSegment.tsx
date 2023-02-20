import React, {FC, FormEvent, useEffect, useMemo, useState} from 'react';

import Constants from 'common/constants';
import useSearchThrottle from "common/useSearchThrottle";
import {EdgePagedResponse, Identity, Segment, SegmentRule} from "common/types/responses";
import {Req} from "common/types/requests";
import {useGetIdentitiesQuery} from "common/services/useIdentity";
import {
    useCreateSegmentMutation,
    useGetSegmentQuery,
    useUpdateSegmentMutation
} from "common/services/useSegment";
import IdentitySegmentsProvider from "common/providers/IdentitySegmentsProvider"
import Format from "common/utils/format"
import Utils from "common/utils/utils";

import AssociatedSegmentOverrides from './AssociatedSegmentOverrides';
import Button, {ButtonLink, ButtonOutline} from "../base/forms/Button";
import EnvironmentSelect from '../EnvironmentSelect';
import InfoMessage from '../InfoMessage';
import Input from "../base/forms/Input";
import InputGroup from"../base/forms/InputGroup"
import PanelSearch from "../PanelSearch";
import Rule from './Rule';
import Switch from "../Switch";
import TabItem from '../base/forms/TabItem';
import Tabs from '../base/forms/Tabs';
import ConfigProvider from 'common/providers/ConfigProvider';
import JSONReference from "../JSONReference";



type PageType = {
    number: number,
    pageType: Req['getIdentities']['pageType'],
    pages: Req['getIdentities']['pages']
}

type CreateSegmentType = {
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

const CreateSegment: FC<CreateSegmentType> = ({
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
  segment: _segment,
  setEnvironmentId,
  searchInput,
  setSearchInput,
  setPage,
}) => {
    const SEGMENT_ID_MAXLENGTH = Constants.forms.maxLength.SEGMENT_ID;

    const defaultSegment: Omit<Segment, "id" | "uuid" | "project"> & { id?: number, uuid?: string, project?: number } = {
        name: "",
        description: "",
        rules: [{
            type: 'ALL',
            conditions: [],
            rules: [
                {
                    type: 'ANY',
                    conditions: [
                        {...Constants.defaultRule},
                    ],
                    rules: []
                },
            ],
        }],
    };
    const segment = _segment || defaultSegment
    const [createSegment, {isSuccess: createSuccess,data:createSegmentData, isError:createError, isLoading:creating}] = useCreateSegmentMutation()
    const [editSegment, {isSuccess: updateSuccess,data:updateSegmentData, isError:updateError, isLoading:updating}] = useUpdateSegmentMutation()

    const isSaving = creating || updating;
    const [showDescriptions, setShowDescriptions] = useState(false);
    const [description, setDescription] = useState(segment.description);
    const [name, setName] = useState<Segment['name']>(segment.name);
    const [rules, setRules] = useState<Segment['rules']>(segment.rules);
    const [tab, setTab] = useState(0);

    const isError = createError || updateError;

    const addRule = (type = 'ANY') => {
        const newRules = rules.concat([]);
        newRules[0].rules = newRules[0].rules.concat({
            type,
            rules: [],
            conditions: [
                {...Constants.defaultRule},
            ],
        });
        setRules(newRules)
    }

    const updateRule = (rulesIndex: number, elementNumber: number, newValue: SegmentRule) => {
        const newRules = rules.concat([])
        newRules[0].rules[elementNumber] = newValue;
        setRules(newRules);
    }

    const removeRule = (rulesIndex: number, elementNumber: number) => {
        const newRules = rules.concat([])
        newRules[0].rules.splice(elementNumber, 1);
        setRules(newRules);
    }

    const close = () => {
        closeModal();
    }

    const save = (e: FormEvent) => {
        Utils.preventDefault(e);
        const segmentData: Omit<Segment, 'id'|'uuid'> = {
            description,
            project: projectId,
            name,
            rules,
            feature: feature,
        }
        if (name) {
            if (segment.id) {
                editSegment({
                    projectId,
                    segment: {
                        ...segmentData,
                        project: segment.project!,
                        uuid: segment.uuid!,
                        id: segment.id!,
                    }
                })
            } else {
                createSegment({
                    projectId,
                    segment: segmentData
                })
            }
        }
    };

    const isValid = useMemo(()=>{
        if (!rules || !rules[0] || !rules[0].rules) {
            return false;
        }
        const res = rules[0].rules.find(v => v.conditions.find(c => !Utils.validateRule(c)));
        return !res;
    }, [rules])

    useEffect(() => {
        setTimeout(() => {
            document.getElementById("segmentID")?.focus()
        }, 500)
    }, [])
    useEffect(() => {
        if (createSuccess) {
            onComplete?.(createSegmentData!);
        }
    }, [createSuccess])
    useEffect(() => {
        if (updateSuccess) {
            onComplete?.(updateSegmentData!);
        }
    }, [updateSuccess])


    const rulesEl = (
        <div className="overflow-visible">
            <div>
                <div className="mb-2">
                    {rules[0].rules.map((rule, i) => {
                        if(rule.delete) {
                            return null
                        }
                        return (
                            <div key={i}>
                                {i > 0 && (
                                    <Row className="and-divider my-1">
                                        <Flex className="and-divider__line"/>
                                        {rule.type === 'ANY' ? 'AND' : 'AND NOT'}
                                        <Flex className="and-divider__line"/>
                                    </Row>
                                )}
                                <Rule
                                    showDescription={showDescriptions}
                                    readOnly={readOnly}
                                    data-test={`rule-${i}`}
                                    rule={rule}
                                    operators={
                                        Utils.getFlagsmithValue('segment_operators') ? JSON.parse(Utils.getFlagsmithValue('segment_operators')) : null
                                    }
                                    onRemove={() => removeRule(0, i)}
                                    onChange={(v: SegmentRule) => updateRule(0, i, v)}
                                />
                            </div>
                        )
                    })}
                </div>
                <Row className="justify-content-center">
                    {!readOnly && (
                        <div
                            onClick={() => addRule('ANY')} style={{marginTop: 20}}
                            className="text-center"
                        >
                            <ButtonOutline data-test="add-rule" type="button">
                                Add AND Condition
                            </ButtonOutline>
                        </div>
                    )}
                    {!readOnly && Utils.getFlagsmithHasFeature('not_operator') && (
                        <div
                            onClick={() => addRule('NOT')} style={{marginTop: 20}}
                            className="text-center"
                        >
                            {
                                Utils.getFlagsmithValue('not_operator') ? (
                                    <Tooltip title={(
                                        <ButtonOutline className="ml-2 btn--outline-danger" data-test="add-rule"
                                                       type="button"
                                        >
                                            Add AND NOT Condition
                                        </ButtonOutline>
                                    )}
                                    >
                                        {`Note: If using clientside evaluations on your SDK, this feature is only supported by the following SDKs: ${JSON.parse(Utils.getFlagsmithValue('not_operator'))}`}
                                    </Tooltip>
                                ) : (
                                    <ButtonOutline className="ml-2 btn--outline-danger" data-test="add-rule"
                                                   type="button"
                                    >
                                        Add AND NOT Condition
                                    </ButtonOutline>
                                )
                            }
                        </div>
                    )}
                </Row>
            </div>
        </div>
    );

    const Tab1 = (
        <form
            id="create-segment-modal"
            onSubmit={save}
        >
            {!condensed && (
                <div className="mt-4">
                    <InfoMessage>
                        Learn more about rule and trait value type conversions <a
                        href="https://docs-git-improvement-segment-rule-value-typing-flagsmith.vercel.app/basic-features/managing-segments#rule-typing"
                    >here</a>.
                    </InfoMessage>
                </div>
            )}

            {!isEdit && (
                <Row className="mb-4">
                    <label className="mr-2 mb-0" htmlFor="segmentID">
                        ID
                    </label>
                    <Flex>
                        <Input
                            data-test="segmentID"
                            name="id"
                            id="segmentID"
                            readOnly={isEdit}
                            maxLength={SEGMENT_ID_MAXLENGTH}
                            value={name}
                            onChange={(e: InputEvent) => setName(Format.enumeration.set(Utils.safeParseEventValue(e)).toLowerCase())}
                            isValid={name && name.length}
                            type="text" title={isEdit ? 'ID' : 'ID*'}
                            placeholder="E.g. power_users"
                        />
                    </Flex>

                </Row>
            )}

            {!condensed && (
                <FormGroup className="mb-4">
                    <InputGroup
                        value={description}
                        inputProps={{
                            className: 'full-width',
                            readOnly: !!identity || readOnly,
                            name: 'featureDesc',
                        }}
                        onChange={(e: InputEvent) => setDescription(Utils.safeParseEventValue(e))}
                        isValid={name && name.length}
                        type="text" title="Description (optional)"
                        placeholder="e.g. 'People who have spent over $100' "
                    />
                </FormGroup>
            )}

            <div className="form-group ">
                <Row className="mt-2 mb-2">
                    <Flex>
                        <label className="cols-sm-2 control-label">Include users when the following rules apply:</label>
                        <span className="text-small text-muted">Note: Trait names are case sensitive</span>
                    </Flex>
                    <span>
                        {showDescriptions ? "Hide condition descriptions" : "Show condition descriptions"}
                    </span>
                    <Switch checked={!!showDescriptions} onChange={() => {
                        setShowDescriptions(!showDescriptions)
                    }}
                    />
                </Row>
                {
                    rulesEl
                }
            </div>

            {isError
                &&
                <div className="alert alert-danger">Error creating segment, please ensure you have entered a trait and
                    value for each rule.</div>
            }
            {isEdit && (
                <JSONReference title={"Segment"} json={segment}/>
            )}
            {readOnly ? (
                <div className="text-right">
                    <Tooltip
                        html
                        title={(
                            <Button
                                disabled data-test="show-create-feature-btn" id="show-create-feature-btn"
                            >
                                Update Segment
                            </Button>
                        )}
                        place="left"
                    >
                        {Constants.projectPermissions('Admin')}
                    </Tooltip>
                </div>
            ) : (
                <div className="text-right">
                    <Row className="justify-content-end">
                        {condensed && (
                            <ButtonLink type="button" onClick={onCancel} className="mr-4">Cancel</ButtonLink>
                        )}
                        {isEdit ? (
                            <Button
                                type="submit" data-test="update-segment" id="update-feature-btn"
                                disabled={isSaving || !name || !isValid}
                            >
                                {isSaving ? 'Creating' : 'Update Segment'}
                            </Button>
                        ) : (
                            <Button
                                disabled={isSaving || !name || !isValid}
                                type="submit" data-test="create-segment"
                                id="create-feature-btn"
                            >
                                {isSaving ? 'Creating' : 'Create Segment'}
                            </Button>
                        )}
                    </Row>

                </div>
            )}
        </form>
    );

    return (
        <div>
            {isEdit && !condensed ? (
                <Tabs value={tab} onChange={(tab: number) => setTab(tab)}>
                    <TabItem tabLabel="Rules">
                        <div className="mt-4 mr-3 ml-3">
                            {Tab1}
                        </div>
                    </TabItem>
                    <TabItem tabLabel="Features">
                        <div className="mt-4 mr-3 ml-3">
                            <AssociatedSegmentOverrides feature={segment.feature} projectId={projectId}
                                                        id={segment.id}
                            />
                        </div>
                    </TabItem>
                    <TabItem tabLabel="Users">
                        <div className="mt-4 mr-3 ml-3">
                            <InfoMessage>
                                This is a random sample of Identities who are either in or out of this Segment based on
                                the current Segment rules.
                            </InfoMessage>
                            <div className="mt-2">
                                <FormGroup>
                                    <InputGroup
                                        title="Environment"
                                        component={(
                                            <EnvironmentSelect
                                                value={environmentId}
                                                onChange={(environmentId: string) => {
                                                    setEnvironmentId(environmentId)
                                                }}
                                            />
                                        )}
                                    />
                                    <PanelSearch
                                        renderSearchWithNoResults
                                        id="users-list"
                                        title="Segment Users"
                                        className="no-pad"
                                        isLoading={identitiesLoading}
                                        icon="ion-md-person"
                                        items={identities?.results}
                                        paging={identities}
                                        showExactFilter
                                        nextPage={() => {
                                            setPage({
                                                number: page.number + 1,
                                                pageType: 'NEXT',
                                                pages: identities?.last_evaluated_key ? (page.pages || []).concat([identities?.last_evaluated_key]) : undefined
                                            })
                                        }}
                                        prevPage={() => {
                                            setPage({
                                                number: page.number - 1,
                                                pageType: 'PREVIOUS',
                                                pages: page.pages ? Utils.removeElementFromArray(page.pages, page.pages.length - 1) : undefined
                                            })
                                        }}
                                        goToPage={(newPage: number) => {
                                            setPage({
                                                number: newPage,
                                                pageType: undefined,
                                                pages: undefined
                                            })
                                        }}
                                        renderRow={({id, identifier}: {id:string, identifier:string}, index:number) => (
                                            <div key={id}>
                                                <IdentitySegmentsProvider fetch id={id} projectId={projectId}>
                                                    {({ segments }: {segments?:Segment[]}) => {
                                                    let inSegment = false;
                                                    if (segments?.find(v => v.name === name)) {
                                                        inSegment = true;
                                                    }
                                                    return (
                                                        <Row
                                                            space className="list-item clickable" key={id}
                                                            data-test={`user-item-${index}`}
                                                        >
                                                            <strong>
                                                                {identifier}
                                                            </strong>
                                                            <div className={`${inSegment ? 'strong text-primary' : 'text-faint muted faint text-small'} badge`}>
                                                                <span className={`ion mr-1 line ${inSegment ? ' text-primary ion-ios-checkmark-circle' : 'ion-ios-remove-circle'}`}/>
                                                                {inSegment ? 'User in segment' : 'Not in segment'}
                                                            </div>
                                                        </Row>
                                                    );
                                                }}
                                                </IdentitySegmentsProvider>
                                            </div>
                                        )}
                                        filterRow={() => true}
                                        search={searchInput}
                                        onChange={(e:InputEvent) => {
                                            setSearchInput(Utils.safeParseEventValue(e))
                                        }}
                                    />
                                </FormGroup>
                            </div>
                        </div>
                    </TabItem>
                </Tabs>
            ) : <div className="mt-4 mr-3 ml-3">{Tab1}</div>}
        </div>
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
    const [environmentId, setEnvironmentId] = useState(props.environmentId);
    const {data: segmentData, isLoading} = props.segment ?
        useGetSegmentQuery({projectId: `${props.projectId}`, id: `${props.segment}`})
        : {data: null, isLoading: false}


    const [page, setPage] = useState<PageType>({number: 1, pageType: undefined, pages: undefined});

    const {searchInput, search, setSearchInput} = useSearchThrottle(Utils.fromParam().search, () => {
        setPage({
            number: 1,
            pageType: undefined,
            pages: undefined
        });
    });

    const isEdge = Utils.getIsEdge();

    const {data: identities, isLoading: identitiesLoading} = useGetIdentitiesQuery({
        pages: page.pages,
        page: page.number,
        search,
        pageType: page.pageType,
        page_size: 10,
        environmentId,
        isEdge
    })

    return isLoading ? <div className="text-center"><Loader/></div> : (
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

module.exports = ConfigProvider(LoadingCreateSegment);
