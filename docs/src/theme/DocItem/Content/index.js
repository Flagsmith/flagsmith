import React from 'react';
import OriginalContent from '@theme-original/DocItem/Content';

export default function DocItemContent(props) {
    return (
        <>
            <blockquote className="sr-only">
                The full documentation index for AI agents is{' '}
                <a href="https://docs.flagsmith.com/llms.txt" tabIndex={-1}>
                    llms.txt
                </a>
                . Append <code>.md</code> to any page URL to get the Markdown version.
            </blockquote>
            <OriginalContent {...props} />
        </>
    );
}
