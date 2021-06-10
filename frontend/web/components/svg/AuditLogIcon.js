import React from "react"

function AuditLogIcon({width, height, fill, className}) {
    return (
        <svg className={className} width={width || '100%'} height={height} viewBox="0 0 26 23">
            <path
                d="M23.2 22.4H2.4A2.4 2.4 0 010 20V2.4A2.4 2.4 0 012.4 0h20.8a2.4 2.4 0 012.4 2.4V20a2.4 2.4 0 01-2.4 2.4zM6.4 4.4a2 2 0 100 4 2 2 0 000-4zm0 4.8a2 2 0 100 4 2 2 0 000-4zm0 4.8a2 2 0 100 4 2 2 0 000-4zm14.4-6.8V5.6a.6.6 0 00-.6-.6h-10a.6.6 0 00-.6.6v1.6a.6.6 0 00.6.6h10a.6.6 0 00.6-.6zm0 4.8v-1.6a.6.6 0 00-.6-.6h-10a.6.6 0 00-.6.6V12a.6.6 0 00.6.6h10a.6.6 0 00.6-.6zm0 4.8v-1.6a.6.6 0 00-.6-.6h-10a.6.6 0 00-.6.6v1.6a.6.6 0 00.6.6h10a.6.6 0 00.6-.6z"
                fill={fill || 'white'}
                fillRule="evenodd"
            />
        </svg>
    )
}

export default AuditLogIcon
