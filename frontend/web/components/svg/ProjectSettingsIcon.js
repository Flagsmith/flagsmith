import React from "react"

function ProjectSettingsIcon({width, height, fill, className}) {
    return (
        <svg className={className} width={width || '100%'} height={height} viewBox="0 0 23 23">
            <path
                d="M20 0H2.4A2.4 2.4 0 000 2.4V20a2.4 2.4 0 002.4 2.4H20a2.4 2.4 0 002.4-2.4V2.4A2.4 2.4 0 0020 0zm-.8 16.2c0 .33-.27.6-.6.6H16V18c0 .665-.535 1.2-1.2 1.2H14c-.665 0-1.2-.535-1.2-1.2v-1.2h-9c-.33 0-.6-.27-.6-.6v-2c0-.33.27-.6.6-.6h9v-1.2c0-.665.535-1.2 1.2-1.2h.8c.665 0 1.2.535 1.2 1.2v1.2h2.6c.33 0 .6.27.6.6v2zm0-8c0 .33-.27.6-.6.6h-9V10c0 .665-.535 1.2-1.2 1.2h-.8c-.665 0-1.2-.535-1.2-1.2V8.8H3.8c-.33 0-.6-.27-.6-.6v-2c0-.33.27-.6.6-.6h2.6V4.4c0-.665.535-1.2 1.2-1.2h.8c.665 0 1.2.535 1.2 1.2v1.2h9c.33 0 .6.27.6.6v2z"
                fill={fill || 'white'}
                fillRule="evenodd"
            />
        </svg>
    )
}

export default ProjectSettingsIcon
