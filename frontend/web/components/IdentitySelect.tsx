import React, {FC, useMemo, useState} from 'react'
import {FeatureState, Identity, Res} from "common/types/responses"; // we need this to make JSX compile
import {filter, find} from "lodash";
import {useGetIdentitiesQuery} from "../../common/services/useIdentity";
import useInfiniteScroll from "../../common/useInfiniteScroll";
import {Req} from "../../common/types/requests";
import {components} from "react-select";
import {ButtonOutline} from "./base/forms/Button";
import Utils from "common/utils/utils";
type IdentitySelectType = {
    value: Identity['id'] | null | undefined
    ignoreIds?: Identity['id'][]
    isEdge: boolean
    onChange: (v:Identity)=> void
    environmentId: string
}

const IdentitySelect: FC<IdentitySelectType> = ({value, isEdge, environmentId, ignoreIds,onChange}) => {

    const {data, searchItems, loadMore, isLoading} = useInfiniteScroll<Req['getIdentities'], Res['identities']>(
        useGetIdentitiesQuery, {
        environmentId,
        isEdge,
        page_size:10
    })
    const identityOptions = useMemo(() => {
        return filter(
            data?.results, identity => !ignoreIds?.length || !find(ignoreIds, v => v === identity.id),
        ).map(({ identifier: label, id: value }) => ({ value, label })).slice(0, 10);
    },[
        ignoreIds,
        data
    ])
    return (
        <Flex className="text-left">
            <Select
                onInputChange={(e:InputEvent)=>{
                    searchItems(Utils.safeParseEventValue(e))
                }}
                data-test="select-identity"
                placeholder="Create an Identity Override..."
                value={value}
                components={{
                    Menu: ({...props}: any) => {
                        return (
                            <components.Menu {...props}>
                                <React.Fragment>
                                    {props.children}
                                    {!!data?.next && (
                                        <div className="text-center mb-4">
                                            <ButtonOutline onClick={() => {
                                                loadMore()
                                            }} disabled={isLoading}
                                            >
                                                Load More
                                            </ButtonOutline>
                                        </div>
                                    )
                                    }
                                </React.Fragment>
                            </components.Menu>
                        )
                    }
                }}
                onChange={onChange}
                options={identityOptions}
                styles={{
                    control: (base:any) => ({
                        ...base,
                        '&:hover': { borderColor: '$bt-brand-secondary' },
                        border: '1px solid $bt-brand-secondary',
                    }),
                }}
            />
        </Flex>
    )
}

export default IdentitySelect
