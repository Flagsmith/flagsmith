import { UseQuery, } from '@reduxjs/toolkit/dist/query/react/buildHooks';
import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {PagedRequest} from "./types/requests";
import {PagedResponse} from "./types/responses";

export const isValidNotEmptyArray = (array: any[]): boolean => {
    return !!(array && array?.length && array?.length > 0)
};

import {throttle} from "lodash";
import {QueryDefinition} from "@reduxjs/toolkit/query";

const useInfiniteScroll = <
    REQ extends PagedRequest<{}>,
    RES extends PagedResponse<{}>
    >(useGetDataListQuery: UseQuery<QueryDefinition<REQ,any,any,RES>>, queryParameters:REQ) => {
    const [localPage, setLocalPage] = useState(1);
    const [combinedData, setCombinedData] = useState<RES|null>(null);
    const [q, setQ] = useState("");

    const queryResponse = useGetDataListQuery({
        ...queryParameters,
        q
    });

    useEffect(() => {
        if (queryResponse?.data) {
            if (localPage === 1) {
                setCombinedData(queryResponse?.data);
            } else { // This is a new page, combine the data
                setCombinedData((prev)=> ({
                    ...queryResponse.data,
                    results: prev?.results ? prev.results.concat(queryResponse!.data!.results) : queryResponse!.data!.results
                } as RES))
            }
        }
    }, [queryResponse])

    const searchItems =  throttle((search:string) => {
        setQ(search);
        setLocalPage(1);
    }, 1000)

    const refresh = useCallback(() => {
        setLocalPage(1);
    }, []);

    const loadMore = () => {
        if (queryResponse?.data?.next) {
            setLocalPage((page) => page + 1);
        }
    };

    return {
        data: combinedData,
        isLoading: queryResponse.isLoading,
        refresh,
        searchItems,
        loadMore,
        response: queryResponse
    };
};

export default useInfiniteScroll;
