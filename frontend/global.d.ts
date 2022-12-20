import {Component, FC, ReactNode} from "react";

export declare const openModal: (name?: string) => Promise<void>;
declare global {
    var openModal: (title:ReactNode, body?:ReactNode, footer?:ReactNode, other?: {className:string, onClose?:()=>void})=>void
    var openConfirm: (header:ReactNode, body:ReactNode, onYes:()=>void, onNo?:()=>void, yesText?:string, noText?:string)=>void
    var Row: typeof Component
    var toast: (value:string)=>void
    var Flex: typeof Component
    var FormGroup: typeof Component
    var Column: typeof Component
    var RemoveIcon: typeof Component
    var ConfigProvider: (Component:typeof Component)=> typeof Component
    var Loader: typeof Component
    var closeModal: ()=>void
    var Tooltip: typeof FC<{title:ReactNode, place?:string, html?:boolean}>
}
