import React,{FC, useState} from 'react'
import {Res, Segment} from "../../common/types/responses";
import {useGetSegmentsQuery} from "../../common/services/useSegment";
import {ButtonOutline} from "./base/forms/Button";
import useInfiniteScroll from "../../common/useInfiniteScroll";
import {Req} from "../../common/types/requests"; // we need this to make JSX compile
import {components} from 'react-select'
import {SelectProps} from "@material-ui/core/Select/Select";
type SelectType  = {name:string, label:string, feature?:number}
const Utils = require('common/utils/utils.js')
type SegmentSelectType = {
    projectId: string
    "data-test"?:string
    placeholder?:string
    value: SelectProps['value']
    onChange: SelectProps['onChange']
    filter?: (segments:Segment)=>Segment[]
}

const SegmentSelect: FC<SegmentSelectType> = ({filter, projectId, ...rest}) => {
    const {data, isLoading, searchItems, loadMore} =  useInfiniteScroll<Req['getSegments'], Res['segments']>(useGetSegmentsQuery, {projectId, page_size:100})

    const options =  (data ?
        filter ?
            data.results.filter(filter) as Res['segments']['results'] : data.results
        : [])
        .map(({ name: label, id: value, feature }) => ({ value, label, feature }))

    return (
        //@ts-ignore
        <Select
            data-test={rest['data-test']}
            placeholder={rest.placeholder}
            value={rest.value}
            onChange={rest.onChange}
            onInputChange={(e:any)=>{
                searchItems(Utils.safeParseEventValue(e))
            }}
            components={{
                Menu: ({...props}: any)=> {
                    return (
                        <components.Menu {...props}>
                            <React.Fragment>
                                {props.children}
                                {!!data?.next && (
                                    <div className="text-center mb-4">
                                        <ButtonOutline onClick={()=>{
                                            loadMore()
                                        }} disabled={isLoading}>
                                            Load More
                                        </ButtonOutline>
                                    </div>
                                )
                                }
                            </React.Fragment>
                    </components.Menu>
                    )
                },
                Option: ({ innerRef, innerProps, children, data }:any) => (
                    <div ref={innerRef} {...innerProps} className="react-select__option">
                        {children}{!!data.feature && (
                        <div className="unread ml-2 px-2">
                            Feature-Specific
                        </div>
                    )}
                    </div>
                ),
            }}
            options={
                options
            }
            styles={{
                control: (base:any) => ({
                    ...base,
                    '&:hover': { borderColor: '$bt-brand-secondary' },
                    border: '1px solid $bt-brand-secondary',
                }),
            }}
        />
    )
}

export default SegmentSelect
