import React, {FC, ReactNode} from 'react';
import {useGetPermissionQuery} from "common/services/usePermission"; // we need this to make JSX compile

type PermissionType = {
    id: string
    permission: string
    level: "project" | "organisation" | "environment"
    children: (data:{ permission:boolean, isLoading:boolean })=> ReactNode
}

const Permission: FC<PermissionType> = ({children, id, level, permission}) => {
    const {data, isLoading} = useGetPermissionQuery({level,id});
    const hasPermission = !!data?.[permission] || !!data?.ADMIN

    return children({ permission:hasPermission, isLoading }) || <div>Hi</div> as any
}

export default Permission
