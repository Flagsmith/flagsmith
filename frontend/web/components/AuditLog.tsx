import React, {FC, useEffect, useRef, useState} from 'react'; // we need this to make JSX compile
import moment from 'moment';
import Utils from 'common/utils/utils';
import {AuditLogItem} from 'common/types/responses';
import {useGetAuditLogsQuery} from 'common/services/useAuditLog';
import useSearchThrottle from 'common/useSearchThrottle';
import PanelSearch from './PanelSearch'

const ConfigProvider = require('common/providers/ConfigProvider');
const ProjectProvider = require('common/providers/ProjectProvider');

type AuditLogType = {
    environmentId: string
    projectId: string
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

    const {data: auditLog, isLoading} = useGetAuditLogsQuery({
        search,
        project: props.projectId,
        page,
        page_size: props.pageSize,
        environments: props.environmentId,
    });

    if (auditLog?.results) {
        hasHadResults.current = true;
    }

    const renderRow = ({created_date, log, author}: AuditLogItem) => {
        return (
            <Row space className='list-item py-2 audit__item' key={created_date}>
                <Flex>
                    <div
                        className='audit__log mb-1'
                    >
                        {log}
                    </div>
                    {!!author && (
                        <div
                            className='text-small text-muted'
                        >
                            {`${author.first_name} ${author.last_name}`}{" "}
                            {moment(created_date).format('Do MMM YYYY HH:mma')}
                        </div>
                    )}

                </Flex>
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
