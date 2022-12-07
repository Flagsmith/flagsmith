import React, { Component, useEffect, useRef, useState } from 'react';
import moment from 'moment'
import { FC } from 'react'; // we need this to make JSX compile

const ConfigProvider = require('common/providers/ConfigProvider');
const PanelSearch = require("../../components/PanelSearch")
const ProjectProvider = require('common/providers/ProjectProvider');
import ToggleChip from '../ToggleChip';
import Utils from 'common/utils/utils';
import { AuditLogItem, Project } from 'common/types/responses';
import { RouterChildContext } from 'react-router';
import { useGetAuditLogsQuery } from 'common/services/useAuditLog';
import useSearchThrottle from 'common/useSearchThrottle';

type AuditLogType = {
    router: RouterChildContext['router']
    match: {
        params: {
            environmentId: string
            projectId: string
        }
    }
}

const AuditLog: FC<AuditLogType> = (props) => {
    const projectId = props.match.params.projectId
    const [page, setPage] = useState(1);
    const {searchInput, search, setSearchInput} = useSearchThrottle(Utils.fromParam().search, ()=>{
        setPage(1)
    });

    const hasHadResults = useRef(false)
    const [environment, setEnvironment] = useState(Utils.fromParam().env);

    const {data:auditLog,isLoading} = useGetAuditLogsQuery({
        search,
        project:projectId,
        page,
        page_size:10,
        environments:environment
    })

    if(auditLog?.results) {
        hasHadResults.current = true
    }

    useEffect(()=>{
        props.router.history.replace(`${document.location.pathname}?${Utils.toParam({
            env:environment,
            search
        })}`);

    },[search,environment])
    const renderRow = ({ created_date, log, author }:AuditLogItem) => {
        return (
            <Row space className="list-item audit__item" key={created_date}>
                <Flex>
                    <div
                        className="audit__log"
                    >
                        {log}
                    </div>
                    {!!author && (
                        <div
                            className="audit__author"
                        >
                            {`${author.first_name} ${author.last_name}`}
                        </div>
                    )}

                </Flex>
                <div className="audit__date">{moment(created_date).format('Do MMM YYYY HH:mma')}</div>
            </Row>
        )
    }
    const { env: envFilter } = Utils.fromParam();

    const hasRbacPermission = Utils.getPlansPermission('AUDIT') || !Utils.getFlagsmithHasFeature('scaleup_audit');
    if (!hasRbacPermission) {
        return (
            <div>
                <div className="text-center">
                    To access this feature please upgrade your account to scaleup or higher.
                </div>
            </div>
        );
    }
    return (
        <div className="app-container container">
            <div>
                <div>
                    <h3>Audit Log</h3>
                    <p>
                        View all activity that occured generically across the project and specific to this environment.
                    </p>
                    <FormGroup>
                        <div>
                                        <div className="audit">
                                            <div className="font-weight-bold mb-2">
                                                Filter by environments:
                                            </div>
                                            <ProjectProvider>
                                                {({ project }:{project:Project}) => (
                                                    <Row>
                                                        {project && project.environments && project.environments.map(env => (
                                                            <ToggleChip active={envFilter === `${env.id}`} onClick={() => setEnvironment(env.id)} className="mr-2 mb-4">
                                                                {env.name}
                                                            </ToggleChip>
                                                        ))}
                                                    </Row>
                                                )}
                                            </ProjectProvider>
                                            <FormGroup>
                                                <PanelSearch
                                                    id="messages-list"
                                                    title="Log entries"
                                                    isLoading={isLoading || (!auditLog)}
                                                    className="no-pad"
                                                    icon="ion-md-browsers"
                                                    items={auditLog?.results}
                                                    filter={envFilter}
                                                    search={searchInput}
                                                    onChange={(e:InputEvent) => {
                                                        setSearchInput(Utils.safeParseEventValue(e))
                                                    }}
                                                    paging={auditLog}
                                                    nextPage={() => {
                                                        setPage(page+1)
                                                    }}
                                                    prevPage={() => {
                                                        setPage(page-1)
                                                    }}
                                                    goToPage={(page:number) => {
                                                        setPage(page)
                                                    }}
                                                    filterRow={() => true}
                                                    renderRow={renderRow}
                                                    renderNoResults={(
                                                        <FormGroup className="text-center">
                                                            You have no
                                                            log messages
                                                            for your
                                                            project.
                                                        </FormGroup>
                                                    )}
                                                />
                                            </FormGroup>
                                        </div>
                                    </div>
                    </FormGroup>
                </div>
            </div>
        </div>
    )
};


export default ConfigProvider(AuditLog);
