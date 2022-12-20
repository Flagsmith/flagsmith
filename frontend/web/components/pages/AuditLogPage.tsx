import React, { Component, useEffect, useRef, useState } from 'react';
import moment from 'moment';
import { FC } from 'react'; // we need this to make JSX compile

const ConfigProvider = require('common/providers/ConfigProvider');
const PanelSearch = require('../../components/PanelSearch');
const ProjectProvider = require('common/providers/ProjectProvider');
import ToggleChip from '../ToggleChip';
import Utils from 'common/utils/utils';
import { AuditLogItem, Project } from 'common/types/responses';
import { RouterChildContext } from 'react-router';
import { useGetAuditLogsQuery } from 'common/services/useAuditLog';
import useSearchThrottle from 'common/useSearchThrottle';
import AuditLog from "../AuditLog";

type AuditLogType = {
    router: RouterChildContext['router']
    match: {
        params: {
            environmentId: string
            projectId: string
        }
    }
}

const AuditLogPage: FC<AuditLogType> = (props) => {
    const projectId = props.match.params.projectId;

    const [environment, setEnvironment] = useState(Utils.fromParam().env);

    const { env: envFilter } = Utils.fromParam();

    const hasRbacPermission = Utils.getPlansPermission('AUDIT') || !Utils.getFlagsmithHasFeature('scaleup_audit');
    if (!hasRbacPermission) {
        return (
            <div>
                <div className='text-center'>
                    To access this feature please upgrade your account to scaleup or higher.
                </div>
            </div>
        );
    }
    return (
        <div className='app-container container'>
            <div>
                <div>
                    <h3>Audit Log</h3>
                    <p>
                        View all activity that occured generically across the project and specific to this environment.
                    </p>
                    <FormGroup>
                        <div>
                            <div className='audit'>
                                <div className='font-weight-bold mb-2'>
                                    Filter by environments:
                                </div>
                                <ProjectProvider>
                                    {({ project }: { project: Project }) => (
                                        <Row>
                                            {project && project.environments && project.environments.map(env => (
                                                <ToggleChip active={envFilter === `${env.id}`}
                                                            onClick={() => setEnvironment(env.id)}
                                                            className='mr-2 mb-4'>
                                                    {env.name}
                                                </ToggleChip>
                                            ))}
                                        </Row>
                                    )}
                                </ProjectProvider>
                                <FormGroup>
                                    <AuditLog
                                        onSearchChange={(search:string)=>{
                                            props.router.history.replace(`${document.location.pathname}?${Utils.toParam({
                                                env: environment,
                                                search,
                                                })}`);
                                        }}
                                        pageSize={10} environmentId={environment} projectId={projectId}/>
                                </FormGroup>
                            </div>
                        </div>
                    </FormGroup>
                </div>
            </div>
        </div>
    );
};


export default ConfigProvider(AuditLogPage);
