import React, {FC, ReactNode, useEffect, useRef, useState} from 'react'; // we need this to make JSX compile
import CreateSegmentModal from '../modals/CreateSegment';
import Constants from 'common/constants'
import API from '../../project/api'
import {useDeleteSegmentMutation, useGetSegmentsQuery} from "common/services/useSegment";
import {Segment} from "common/types/responses";
import ConfirmRemoveSegment from '../modals/ConfirmRemoveSegment';
import {find, sortBy} from 'lodash'
import useThrottle from "../../../common/useThrottle";
import Button, {ButtonLink} from "../base/forms/Button";
import {RouterChildContext} from "react-router";
import {useHasPermission} from "../../../common/providers/Permission";
import PanelSearch from '../PanelSearch'

const Utils = require('common/utils/utils')

const Panel = require("../../components/base/grid/Panel")
const CodeHelp = require("../../components/CodeHelp")
type SegmentsPageType = {
    router: RouterChildContext['router']
    match: {
        params: {
            environmentId: string
            projectId: string
        }
    }
}

const HowToUseSegmentsMessage = () => (
    <div className="mt-2">
        <p className="alert alert-info">
            In order to use segments, please set the segment_operators remote config value. <a target="_blank"
                                                                                               href="https://docs.flagsmith.com/deployment/overview#running-flagsmith-on-flagsmith"
        >Learn about self hosting</a>.
        </p>
    </div>
);

type PermissionType = { permission: boolean; isLoading: boolean }

const SegmentsPage: FC<SegmentsPageType> = (props) => {
    const {projectId, environmentId} = props.match.params;
    const preselect = useRef(Utils.fromParam().id);
    const hasNoOperators = !Utils.getFlagsmithValue('segment_operators');
    const [search, _setSearch] = useState("");
    const [searchInput, setSearchInput] = useState("");

    const [page, setPage] = useState(1);
    const {data, isLoading, error, refetch} = useGetSegmentsQuery({projectId, page, q: search, page_size: 100})
    const [removeSegment] = useDeleteSegmentMutation()
    const hasHadResults = useRef(false)

    useEffect(() => {
        API.trackPage(Constants.pages.FEATURES);
    }, [])
    useEffect(() => {
        if (error) {
            // Kick user back out to projects
            props.router.history.replace('/projects');
        }
    }, [error])
    const newSegment = () => {
        openModal('New Segment', <CreateSegmentModal
            onComplete={() => {
                //todo: remove when CreateSegment uses hooks
                closeModal()
                refetch()
            }}
            environmentId={environmentId}
            projectId={projectId}
        />, null, {className: 'fade side-modal create-new-segment-modal'});
    };
    const confirmRemove = (segment: Segment, cb?: () => void) => {
        openModal('Remove Segment', <ConfirmRemoveSegment
            environmentId={environmentId}
            segment={segment}
            cb={cb}
        />);
    }

    const {permission} = useHasPermission({
        level: "project",
        permission: "ADMIN",
        id: projectId
    })
    const {permission: projectAdmin} = useHasPermission({
        level: "environment",
        permission: "CREATE_SEGMENT",
        id: environmentId
    })

    const createSegmentPermission = (el: (permission: boolean) => ReactNode) => {
        return permission ? el(permission) :
            renderWithPermission(permission, "environment", el(permission))
    }
    const editSegment = (id: number, readOnly?: boolean) => {
        API.trackEvent(Constants.events.VIEW_SEGMENT);
        history.replaceState(
            {},
            "",
            `${document.location.pathname}?id=${id}`,
        );

        openModal(`Edit Segment`, <CreateSegmentModal
            segment={id}
            isEdit
            readOnly={readOnly}
            onComplete={() => {
                refetch()
                closeModal()
            }}
            environmentId={environmentId}
            projectId={projectId}
        />, null, {
            onClose: () => {
                history.replaceState(
                    {},
                    "",
                    `${document.location.pathname}`,
                );
            },
            className: 'fade side-modal create-segment-modal',
        });

    };
    const renderWithPermission = (permission: boolean, name: string, el: ReactNode) => {
        return permission ? (
            el
        ) : (
            <Tooltip
                title={el}
                place="right"
                html
            >
                {Constants.projectPermissions('Manage segments')}
            </Tooltip>
        );
    };

    if (data?.results.length) {
        hasHadResults.current = true
    }
    const setSearch = useThrottle((search: string) => {
        _setSearch(search)
    }, 100)
    useEffect(() => {
        setSearch(searchInput)
    }, [searchInput])
    const segments = data?.results
    return (
        <div data-test="segments-page" id="segments-page" className="app-container container">
            <div className="segments-page">
                {isLoading && !hasHadResults.current && (!segments && !search) &&
                    <div className="centered-container"><Loader/></div>}
                {(!isLoading || (segments || search)) && (
                    <div>
                        {hasHadResults.current || (segments && (segments.length || search)) ? (
                            <div>
                                <Row>
                                    <Flex>
                                        <h3>Segments</h3>
                                        <p>
                                            Create and manage groups of users with similar traits. Segments can be used
                                            to override features within the features page for any environment.
                                            {' '}
                                            <ButtonLink target="_blank"
                                                        href="https://docs.flagsmith.com/basic-features/managing-segments"
                                            >Learn about Segments.</ButtonLink>
                                        </p>
                                    </Flex>
                                    <FormGroup className="float-right">
                                        <div className="text-right">
                                            {projectAdmin ? (
                                                <Button
                                                    disabled={hasNoOperators}
                                                    className="btn-lg btn-primary"
                                                    id="show-create-segment-btn"
                                                    data-test="show-create-segment-btn"
                                                    onClick={newSegment}
                                                >
                                                    Create Segment
                                                </Button>
                                            ) : (
                                                <Tooltip
                                                    html
                                                    title={(
                                                        <Button
                                                            disabled data-test="show-create-feature-btn"
                                                            id="show-create-feature-btn"
                                                        >
                                                            Create Segment
                                                        </Button>
                                                    )}
                                                    place="right"
                                                >
                                                    {Constants.projectPermissions('Manage segments')}
                                                </Tooltip>
                                            )}
                                        </div>
                                    </FormGroup>
                                </Row>
                                {hasNoOperators && <HowToUseSegmentsMessage/>}

                                <FormGroup>
                                    <PanelSearch
                                        renderSearchWithNoResults
                                        className="no-pad"
                                        id="segment-list"
                                        icon="ion-ios-globe"
                                        title="Segments"
                                        items={sortBy(segments, (v) => {
                                            return `${v.feature ? 'z' : 'a'}${v.name}`
                                        })}
                                        renderRow={({name, id, feature, description}: Segment, i: number) => {
                                            if (preselect.current === `${id}`) {
                                                editSegment(preselect.current, !projectAdmin)
                                                preselect.current = null;
                                            }
                                            return (
                                                <Row className="list-item clickable" key={id} space>
                                                    <div
                                                        className="flex flex-1"
                                                        onClick={() => editSegment(id, !projectAdmin)}
                                                    >
                                                        <Row>
                                                            <ButtonLink>
                                                                <span data-test={`segment-${i}-name`}>
                                                                    {name}{feature &&
                                                                    <div className="unread ml-2 px-2">
                                                                        {" "}Feature-Specific
                                                                    </div>
                                                                }
                                                                </span>
                                                            </ButtonLink>
                                                        </Row>
                                                        <div className="list-item-footer faint">
                                                            {description || 'No description'}
                                                        </div>
                                                    </div>
                                                    <Row>
                                                        <Column>
                                                            <button
                                                                disabled={!projectAdmin}
                                                                data-test={`remove-segment-btn-${i}`}
                                                                onClick={() => confirmRemove(find(segments, {id})!, () => {
                                                                    removeSegment({projectId, id});
                                                                })}
                                                                className="btn btn--with-icon"
                                                            >
                                                                <RemoveIcon/>
                                                            </button>
                                                        </Column>
                                                    </Row>
                                                </Row>
                                            );
                                        }}
                                        paging={data}
                                        nextPage={() => setPage(page + 1)}
                                        prevPage={() => setPage(page - 1)}
                                        goToPage={(page: number) => setPage(page)}
                                        search={searchInput}
                                        onChange={(e: any) => {
                                            setSearchInput(Utils.safeParseEventValue(e))
                                        }}
                                        renderNoResults={(
                                            <div className="text-center"/>
                                        )}
                                        filterRow={({
                                                        name,
                                                        feature
                                                    }: Segment, search: string) => name.toLowerCase().indexOf(search) > -1}
                                    />
                                </FormGroup>

                                <div className="mt-2">
                                    Segments require you to identitfy users, setting traits will add users to segments.
                                </div>
                                <FormGroup className="mt-4">
                                    <CodeHelp
                                        title="Using segments"
                                        snippets={Constants.codeHelp.USER_TRAITS(environmentId)}
                                    />
                                </FormGroup>
                            </div>
                        ) : (
                            <div>
                                <h3>Target groups of users with segments.</h3>
                                <FormGroup>
                                    <Panel icon="ion-ios-globe" title="1. creating a segment">
                                        <p>
                                            You can create a segment that targets
                                            {' '}
                                            <ButtonLink
                                                href="https://docs.flagsmith.com/basic-features/managing-identities#identity-traits"
                                                target="_blank"
                                            >User Traits
                                            </ButtonLink>
                                            .
                                            As user's traits are updated they will automatically be added to
                                            the segments based on the rules you create. <ButtonLink
                                            href="https://docs.flagsmith.com/basic-features/managing-segments"
                                            target="_blank"
                                        >Check out the documentation on Segments</ButtonLink>.
                                        </p>
                                    </Panel>
                                </FormGroup>
                                {createSegmentPermission(perm => (
                                    <FormGroup className="text-center">
                                        <Button
                                            disabled={!perm || hasNoOperators}
                                            className="btn-lg btn-primary" id="show-create-segment-btn"
                                            data-test="show-create-segment-btn"
                                            onClick={newSegment}
                                        >
                                            <span className="icon ion-ios-globe"/>
                                            {' '}
                                            Create your first Segment
                                        </Button>
                                    </FormGroup>
                                ))}
                                {hasNoOperators && <HowToUseSegmentsMessage/>}
                            </div>
                        )}
                    </div>
                )}
                <FormGroup>
                    <CodeHelp
                        title="Managing user traits and segments"
                        snippets={Constants.codeHelp.USER_TRAITS(environmentId)}
                    />
                </FormGroup>
            </div>
        </div>
    );
}


module.exports = ConfigProvider(SegmentsPage);
