import React, {FC, ReactNode} from 'react';
import {filter} from 'lodash'
import {Tag as TTag} from "../../../common/types/responses";
import {useGetTagsQuery} from "../../../common/services/useTag";
import Tag from "./Tag";
import Button from "../base/forms/Button";

type TagFilterType = {
    value?: number[]
    onClearAll?: () => void
    showClearAll?: boolean
    showUntagged?: boolean
    projectId: string
    onChange: (value: (number | string)[]) => void
    children?: ReactNode
}

const TagFilter: FC<TagFilterType> = ({
                                          value: _value,
                                          showUntagged,
                                          onClearAll,
                                          showClearAll,
                                          projectId,
                                          onChange,
                                          children
                                      }) => {
    const {data: projectTags, isLoading: tagsLoading} = useGetTagsQuery({projectId})

    const isSelected = (tag: TTag) => _value?.includes(tag.id!)
    const onSelect = (tag: TTag) => {
        const value = _value || [];
        if (value.includes(tag.id)) {
            onChange(filter(value, v => v !== tag.id));
        } else {
            onChange(value.concat([tag.id]));
        }
    }
    const unTagged = !!showUntagged && {color: '#666', label: 'Untagged', id: ''};
    return (
        <Row className="tag-filter mx-2 mt-4">
            <div className="ml-1">
                <Row>
                    <Flex>
                        <Row className="tag-filter-list">
                            {children}
                            {unTagged && (
                                <div className="mr-1">
                                    <Tag
                                        key={unTagged.id}
                                        selected={isSelected(unTagged as any)}
                                        onClick={onSelect}
                                        className="px-2 py-2 mr-2"
                                        tag={unTagged as any}
                                    />
                                </div>
                            )}

                            {projectTags?.map(tag => (
                                <div className="mr-1">
                                    <Tag
                                        key={tag.id}
                                        selected={isSelected(tag)}
                                        onClick={onSelect}
                                        className="px-2 py-2 mr-2"
                                        tag={tag}
                                    />

                                </div>
                            ))}
                        </Row>

                    </Flex>


                    {showClearAll && (
                        <Button
                            onClick={() => {
                                if ((_value?.length || 0) >= (projectTags?.length || 0)) {
                                    onChange([]);
                                } else {
                                    onChange(
                                        // @ts-ignore mixed array type
                                        (showUntagged ? [''] : []).concat((projectTags||[])?.map(v => v.id)));
                                }
                                onClearAll && onClearAll();
                            }} style={{marginBottom: 10}} className="btn--link mr-2"
                        >
                            Clear Filters
                        </Button>
                    )}
                </Row>
            </div>
        </Row>
    );
}

export default TagFilter
