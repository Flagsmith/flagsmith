import React, {FC, useEffect, useRef, useState} from 'react'; // we need this to make JSX compile
import moment from 'moment';
import Utils from 'common/utils/utils';
import {AuditLogItem} from 'common/types/responses';
import {useGetAuditLogsQuery} from 'common/services/useAuditLog';
import useSearchThrottle from 'common/useSearchThrottle';
import JSONReference from "./JSONReference";

const PanelSearch = require('../components/PanelSearch');
const Format = require('common/format')
type AuditLogType = {
    environmentId: string
    projectId: string
    onErrorChange?:(error:boolean) => void
    pageSize:number
    onSearchChange?:(search:string)=>void
}

const AuditLog: FC<AuditLogType> = (props) => {
    const [page, setPage] = useState(1);
    const {searchInput, search, setSearchInput} = useSearchThrottle(Utils.fromParam().search, () => {
        setPage(1);
    });

    useEffect(()=>{
        if(props.onSearchChange) {
            props.onSearchChange(search)
        }
    },[search])

    const hasHadResults = useRef(false);

    const {data: auditLog, isLoading, isError} = useGetAuditLogsQuery({
        search,
        project: props.projectId,
        page,
        page_size: props.pageSize,
        environments: props.environmentId,
    });

    useEffect(()=>{
       props.onErrorChange?.(isError)
    },[])

    if (auditLog?.results) {
        hasHadResults.current = true;
    }

    const renderRow = ({created_date, log, author, environment, related_object_type}: AuditLogItem) => {
        return (
            <Row space className='list-item py-2 audit__item' key={created_date}>
                <span>
                    {moment(created_date).format('Do MMM YYYY HH:mma')}
                </span>
                <span>
                    {Format.enumeration.get(related_object_type)}
                </span>
                <span>
                    {environment?.name || "Project"}
                </span>
            </Row>
        );
    };
    const {env: envFilter} = Utils.fromParam();

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
        <PanelSearch
            id='messages-list'
            title='Log entries'
            isLoading={isLoading || (!auditLog)}
            className='no-pad'
            icon='ion-md-browsers'
            items={auditLog?.results}
            filter={envFilter}
            search={searchInput}
            onChange={(e: InputEvent) => {
                setSearchInput(Utils.safeParseEventValue(e));
            }}
            paging={auditLog}
            nextPage={() => {
                setPage(page + 1);
            }}
            prevPage={() => {
                setPage(page - 1);
            }}
            goToPage={(page: number) => {
                setPage(page);
            }}
            filterRow={() => true}
            renderRow={renderRow}
            renderFooter={()=><JSONReference className="mt-4 ml-2" title={"Audit"} json={auditLog?.results}/>}
            renderNoResults={(
                <FormGroup className='text-center'>
                    You have no
                    log messages
                    for your
                    project.
                </FormGroup>
            )}
        />
    );
};


export default AuditLog;
