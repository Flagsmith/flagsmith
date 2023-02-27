import React, {FC, useState} from 'react'
import InlineModal from "../InlineModal";
import Constants from "common/constants";
import Tag from "./Tag";

type ColourSelectType = {
    value: string
    onChange: (colour:string)=>void
}

const ColourSelect: FC<ColourSelectType> = ({onChange,value:_value}) => {
    const [isOpen, setIsOpen] = useState(false);
    const value = _value || Constants.tagColors[0];

    return (
        <>
            <Tag
                selected
                onClick={() => setIsOpen(true)}
                tag={{color:value}}
            />

            <InlineModal
                title="Select a colour"
                isOpen={isOpen}
                onClose={()=>setIsOpen(false)}
                className="inline-modal--tags"
            >
                <div>
                    <Row className="mb-2">
                        {Constants.tagColors.map(color => (
                            <div key={color} className="tag--select mr-2 mb-2">
                                <Tag
                                    onClick={(tag) => {
                                        onChange(tag.color)
                                        setIsOpen(false)
                                    }}
                                    selected={value === color}
                                    tag={{color}}
                                />
                            </div>

                        ))}
                    </Row>
                </div>
            </InlineModal>
        </>
    )
}

export default ColourSelect
