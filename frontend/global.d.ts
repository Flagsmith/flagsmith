import {Component, FC, ReactNode} from "react";

export declare const openModal: (name?: string) => Promise<void>;
declare global {
    var openModal: (title:string, body:ReactNode, footer?:ReactNode, other?: {className:string, onClose?:()=>void})=>void
    var Row: typeof Component
    var Flex: typeof Component
    var FormGroup: typeof Component
    var Column: typeof Component
    var RemoveIcon: typeof Component
    var ConfigProvider: (Component:typeof Component)=> typeof Component
    var Loader: typeof Component
    var Tooltip: typeof FC<{title:ReactNode, place?:string, html?:boolean}>
}
