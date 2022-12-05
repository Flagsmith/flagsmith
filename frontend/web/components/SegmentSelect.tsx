import {FC, useState} from 'react'
import {Res, Segment} from "../../common/types/responses";
import {useGetSegmentsQuery} from "../../common/services/useSegments";
import {ButtonOutline} from "./base/forms/Button";
import {Select} from "@material-ui/core";
import useInfiniteScroll from "../../common/useInfiniteScroll";
import {Req} from "../../common/types/requests"; // we need this to make JSX compile

type SelectType  = {name:string, label:string, feature?:number}

type SegmentSelectType = {
    projectId: string
    "data-test"?:string
    placeholder?:string
    filter?: (segments:Segment)=>Segment[]
}

const SegmentSelect: FC<SegmentSelectType> = ({filter, projectId, ...rest}) => {
    const {data, isLoading, searchItems, loadMore} =  useInfiniteScroll<Req['getSegments'], Res['segments']>(useGetSegmentsQuery, {projectId})
    const [page, setPage] = useState();

    const options =  (data ?
        filter ?
            data.results.filter(filter) as Res['segments']['results'] : data.results
        : [])
        .map(({ name: label, id: value, feature }) => ({ value, label, feature }))

    return (
        <Select
            data-test={rest['data-test']}
            placeholder={rest.placeholder}
            value={rest.value}
            onChange={rest.onChange}
            onInputChange={(e)=>{
                searchItems(Utils.safeEvent)
            }}
            components={{
                Menu: ({...props})=> {
                    return     <components.Menu {...props}>
                        {props.children}
                        {!!this.state.next && (
                            <div className="text-center mb-4">
                                <ButtonOutline onClick={()=>{

                                }} disabled={isLoading}>
                                    Load More
                                </ButtonOutline>
                            </div>
                        )
                        }
                    </components.Menu>
                },
                Option: ({ innerRef, innerProps, children, data }) => (
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
                control: base => ({
                    ...base,
                    '&:hover': { borderColor: '$bt-brand-secondary' },
                    border: '1px solid $bt-brand-secondary',
                }),
            }}
        />
    )
}

export default SegmentSelect
