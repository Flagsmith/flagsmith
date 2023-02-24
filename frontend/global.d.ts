import {Component, FC, ReactNode} from "react";
import _Select from './web/components/Select';
import { Environment, FeatureState, ProjectFlag } from 'common/types/responses';
export declare const openModal: (name?: string) => Promise<void>;
declare global {
    var openModal: (title:ReactNode, body?:ReactNode, footer?:ReactNode, other?: {className:string, onClose?:()=>void})=>void
    var openConfirm: (header:ReactNode, body:ReactNode, onYes:()=>void, onNo?:()=>void, yesText?:string, noText?:string)=>void
    var Row: typeof Component
    var toast: (value:string)=>void
    var Flex: typeof Component
    var isMobile: boolean
    var FormGroup: typeof Component
    var Select: typeof _Select
    var Column: typeof Component
    var RemoveIcon: typeof Component
    var Loader: typeof Component
    var E2E: boolean
    var closeModal: ()=>void
    var toast: (message:string)=>void
    var Tooltip: typeof FC<{title:ReactNode, place?:string, html?:boolean}>
}

export type FeatureListProviderData = {projectFlags:ProjectFlag[]|null, environmentFlags:FeatureState[]|null, isLoading: boolean}
export type FeatureListProviderActions = {
    toggleFlag: (index:number, environments: Environment[], comment:string|null, environmentFlags: FeatureState[], projectFlags:ProjectFlag[]) => void
    removeFlag: (projectId:string, projectFlag:ProjectFlag) => void
}
