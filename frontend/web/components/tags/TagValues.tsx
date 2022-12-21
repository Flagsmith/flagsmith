import React, {FC} from 'react'
import Button from "../base/forms/Button";
import {Tag as TTag} from "../../../common/types/responses";
import Tag from "./Tag";


type TagValuesType = {
    onAdd?: ()=> void
    value?: number[]
    tags?: TTag[]
}

const TagValues: FC<TagValuesType> = ({
    onAdd,
    tags,
    value
}) => {
    return (
        <>
            {tags?.map(tag => value?.includes(tag.id) && (
                <Tag
                    onClick={onAdd}
                    className="px-2 py-2 mr-2"
                    tag={tag}
                />
            ))}
            {!!onAdd && (
                <Button onClick={onAdd} type="button" className="btn--outline">
                    Add Tag
                </Button>
            ) }
        </>
    )
}

export default TagValues
