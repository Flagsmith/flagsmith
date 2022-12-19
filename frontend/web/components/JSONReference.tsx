import React, {FC, useMemo, useState} from 'react'
import {isArray, isObject} from "lodash";

import Highlight from "./Highlight";
import Button from "./base/forms/Button";
import Switch from "./Switch"
import flagsmith from "flagsmith";

type JSONReferenceType = {
    title: string
    json: any
    showNamesButton?: boolean
    hideCondensedButton?: boolean
    condenseInclude?: string[]
    className?:string
}

function pickProperties(obj: any, idsOnly:boolean, condenseInclude?:string[]): any {
    const propertyCheck = (key:string)=>{
        if (condenseInclude?.includes(key)) {
            return true
        }
        if (key === 'id' || key.includes("uuid")) {
            return true
        }
        if(idsOnly) {
            return false
        }
        if (key.includes('name')|| key === "email") {
            return true
        }
    }
    var retObj: any = {};
    if (isArray(obj)) {
        return obj.map(function (arrayObj: any[]) {
            return pickProperties(arrayObj, idsOnly, condenseInclude);
        });
    }
    Object.keys(obj).forEach(function (key) {
        if (propertyCheck(key)) {
            if (isArray(obj[key])) {
                if (!obj[key].length) {
                    return
                }
                retObj[key] = obj[key].map(function (arrayObj: any[]) {
                    return pickProperties(arrayObj, idsOnly, condenseInclude);
                });
            } else if (isObject(obj[key])) {
                retObj[key] = pickProperties(obj[key], idsOnly, condenseInclude);
            } else {
                retObj[key] = obj[key];
            }
        }
    });
    return retObj;
}

const JSONReference: FC<JSONReferenceType> = ({title, json, className, hideCondensedButton, showNamesButton, condenseInclude}) => {
    const [visible, setVisible] = useState(false);
    const [condensed, setCondensed] = useState(false);
    const [useIdsOnly, setUseIdsOnly] = useState(true);

    const value = useMemo(() => {
        return json && JSON.stringify(json, null, 2)
    }, [json])
    const idsOnly = useMemo(() => {
        return json && JSON.stringify(pickProperties(json, useIdsOnly, condenseInclude), null, 2)
    }, [json,condensed,useIdsOnly])
    if(!flagsmith.getTrait("json_inspect")|| !json || json?.length === 0) {
        return null
    }
    return (
        <>
            <div className={className}>
                <Row
                    style={{cursor: 'pointer'}} onClick={() => {
                    setVisible(!visible);
                }}
                >
                    <Flex style={isMobile ? {overflowX: 'scroll'} : {}}>
                        <div>
                                    <pre className="hljs-header">
                                        <span className="ion-md-document"/>
                                        {' '}
                                        JSON data:
                                        {' '}
                                        <span className="hljs-description">
                                            {title}
                                            {' '}
                                        </span>
                                        <span
                                            className={visible ? 'icon ion-ios-arrow-down' : 'icon ion-ios-arrow-forward'}
                                        />
                                    </pre>
                        </div>
                    </Flex>
                </Row>
                {visible && (
                    <div className="hljs mb-2">
                        <Row space>
                            <div>
                                <Row>
                                    {!hideCondensedButton && (
                                        <div className="ml-2">
                                            <label className="text-small text-white">Condensed</label>
                                            <Switch checked={condensed} onChange={() => setCondensed(!condensed)}
                                            />
                                        </div>
                                    )}
                                    {condensed && showNamesButton && (
                                        <div className="ml-2">
                                            <label className="text-small text-white">Show names</label>
                                            <Switch checked={!useIdsOnly} onChange={() => setUseIdsOnly(!useIdsOnly)}
                                            />
                                        </div>
                                    )}
                                </Row>

                            </div>
                            <Button onClick={() => {
                                navigator.clipboard.writeText(condensed ? idsOnly : value)
                                toast("Copied")
                            }} className="btn btn-primary"
                            >
                                Copy JSON
                            </Button>
                        </Row>
                        <div className="hljs-container">
                            <Highlight forceExpanded preventEscape className={"json"}>
                                {condensed ? idsOnly : value}
                            </Highlight>
                        </div>
                    </div>

                )}
            </div>
        </>
    )
}

export default JSONReference
