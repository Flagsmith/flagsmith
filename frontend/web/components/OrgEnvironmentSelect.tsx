import React, {FC, useMemo, useState} from 'react'
import {useGetOrganisationsQuery} from "common/services/useOrganisation";
import {useGetProjectsQuery} from "common/services/useProject";
import {useGetEnvironmentsQuery} from "common/services/useEnvironment";
import { Environment, Segment } from 'common/types/responses';
import Format from "common/utils/format"
import {sortBy} from "lodash";
import PanelSearch from './PanelSearch';
import {ButtonOutline} from "./base/forms/Button";
import Input from './base/forms/Input';

type OrgProjectSelectType = {
    organisationId?: string | null
    onOrganisationChange: (id:string|null) => void
    projectId?: string | null
    onProjectChange: (id:string|null) => void
    environmentId?: string | null
    useApiKey?: boolean
    onEnvironmentChange: (id:string|null) => void
}

const OrgEnvironmentSelect: FC<OrgProjectSelectType> = ({
    organisationId,
    projectId,
    environmentId,
    onEnvironmentChange,
    onOrganisationChange,
    useApiKey,
    onProjectChange
}) => {
    const [search, setSearch] = useState();

    const {data:organisations, isLoading:organisationsLoading} =  useGetOrganisationsQuery({})
    const {data:projects,isLoading:projectsLoading} =  useGetProjectsQuery({organisationId:organisationId!}, {skip:!organisationId})
    const {data:environments, isLoading:environmentsLoading} =  useGetEnvironmentsQuery({projectId:projectId!}, {skip:!projectId})
    const organisation = useMemo(()=> organisations?.results?.find((v)=>`${v.id}` === organisationId) , [organisations,organisationId])
    const project = useMemo(()=> projects?.find((v)=>`${v.id}` === projectId) , [projects,projectId])
    const environment = useMemo(()=> environments?.results?.find((v)=>`${v.api_key}` === environmentId) , [environments,environmentId])
    let onClick = onEnvironmentChange;
    let items: any = environments?.results;
    let level = "ENVIRONMENT";

    if (!organisation) {
        onClick = onOrganisationChange;
        items = organisations?.results;
        level = "ORGANISATION"
    } else if (!project) {
        onClick = onProjectChange;
        items = projects;
        level = "PROJECT"
    }
    return (
        <>
            <Row className="mb-2 centered-container mb-4">
                {organisation && (
                    <a href={"#"} onClick={()=>onOrganisationChange(null)}>
                        Organisations
                    </a>
                )}
                {organisation && (
                    <>
                        <span className="ion ion-ios-arrow-forward mx-2 d-block"/>
                        <a href={"#"} onClick={()=>onProjectChange(null)}>
                            {organisation.name}
                        </a>
                    </>
                )}
                {project && (
                    <>
                        <span className="ion ion-ios-arrow-forward mx-2 d-block"/>
                        <a href={"#"} onClick={()=>onProjectChange(null)}>
                            {project.name}
                        </a>
                    </>
                )}
                {environment && (
                    <>
                        <span className="ion ion-ios-arrow-forward mx-2 d-block"/>
                        <a href={"#"}>
                            {environment.name}
                        </a>
                    </>
                )}
            </Row>
            {environmentId && projectId? (
                <div>
                    <p>
                        Copy the following values to your widget configuration.
                    </p>
                    <Row className="mb-4">
                        <span style={{width:150}} className="mr-2 text-left">
                            Project ID
                        </span>
                        <Input
                            style={{width:260}}
                            inputProps={{
                                readOnly: true,
                            }}
                            value={
                                projectId
                            }
                        />
                            <ButtonOutline
                                style={{ width: 80 }} className="btn-secondary ml-2 mr-4" onClick={() => {
                                navigator.clipboard.writeText(projectId);
                            }}
                            >Copy
                            </ButtonOutline>
                    </Row>
                    <Row>
                        <span style={{width:150}} className="mr-2 text-left">
                            Environment ID
                        </span>
                        <Input
                            style={{width:260}}
                            inputProps={{
                                readOnly: true,
                            }}
                            value={
                                environmentId
                            }
                        />
                            <ButtonOutline
                                style={{ width: 80 }} className="btn-secondary ml-2 mr-4" onClick={() => {
                                navigator.clipboard.writeText(environmentId);
                            }}
                            >Copy
                            </ButtonOutline>
                    </Row>
                </div>
            ): (
                <PanelSearch
                    renderSearchWithNoResults
                    className="no-pad text-left"
                    isLoading={organisationsLoading||projectsLoading||environmentsLoading}
                    id="segment-list"
                    icon="ion-ios-globe"
                    title={`${Format.camelCase(level)} Search`}
                    items={sortBy(items, (v)=> {
                        return v.name
                    })}
                    filterRow={(row:Environment, search:string) => row.name.toLowerCase().includes(search.toLowerCase())}
                    onChange={setSearch}
                    search={search}
                    renderRow={({ name, id, api_key }:Environment, i:number) => (
                        <a className="list-item clickable" onClick={()=>{
                            onClick(`${useApiKey? api_key||id: id}`)
                        }}>
                            {name}
                        </a>
                    )}
                />
            )}

        </>
    )
}

export default OrgEnvironmentSelect
