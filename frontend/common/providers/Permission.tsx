import React, { FC, ReactNode } from 'react';
import { useGetPermissionQuery } from "common/services/usePermission";
import { PermissionLevel } from "common/types/requests";
import AccountStore from '../stores/account-store'; // we need this to make JSX compile

type PermissionType = {
    id: string
    permission: string
    level: PermissionLevel
    children: (data:{ permission:boolean, isLoading:boolean })=> ReactNode
}

export const useHasPermission = ({ id, level, permission }:Omit<PermissionType,"children">) => {
    const { data, isLoading } = useGetPermissionQuery({ level,id });
    const hasPermission = !!data?.[permission] || !!data?.ADMIN
    return { permission:hasPermission, isLoading };
}

const Permission: FC<PermissionType> = ({ children, id, level, permission }) => {
    const { permission:hasPermission, isLoading } = useHasPermission({ id,level,permission })
    return <>{children({ permission:hasPermission||AccountStore.isAdmin(), isLoading }) || <div/>}</>
}

export default Permission
