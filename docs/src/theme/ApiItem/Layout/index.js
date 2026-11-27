/**
 * Copyright (c) Palo Alto Networks
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */
import React from 'react';
import clsx from 'clsx';
import { useWindowSize } from '@docusaurus/theme-common';
import { useDoc } from '@docusaurus/plugin-content-docs/client';
import ContentVisibility from '@theme/ContentVisibility';
import DocBreadcrumbs from '@theme/DocBreadcrumbs';
import DocItemContent from '@theme/DocItem/Content';
import DocItemFooter from '@theme/DocItem/Footer';
import DocItemPaginator from '@theme/DocItem/Paginator';
import DocItemTOCDesktop from '@theme/DocItem/TOC/Desktop';
import DocItemTOCMobile from '@theme/DocItem/TOC/Mobile';
import DocVersionBadge from '@theme/DocVersionBadge';
import DocVersionBanner from '@theme/DocVersionBanner';
import styles from './styles.module.css';

function useDocTOC() {
    const { frontMatter, toc } = useDoc();
    const windowSize = useWindowSize();
    const hidden = frontMatter.hide_table_of_contents;
    const canRender = !hidden && toc.length > 0;
    const mobile = canRender ? <DocItemTOCMobile /> : undefined;
    const desktop = canRender && (windowSize === 'desktop' || windowSize === 'ssr') ? <DocItemTOCDesktop /> : undefined;
    return { hidden, mobile, desktop };
}

export default function ApiItemLayout({ children }) {
    const docTOC = useDocTOC();
    const { metadata, frontMatter } = useDoc();
    const api = frontMatter.api;
    const schema = frontMatter.schema;
    const contentWidth = api || schema ? 'col--7' : 'col--12';

    return (
        <div className="row">
            <div className={clsx('col', !docTOC.hidden && styles.docItemCol)}>
                <ContentVisibility metadata={metadata} />
                <DocVersionBanner />
                <div className={styles.docItemContainer}>
                    <article>
                        <blockquote className="sr-only">
                            The full documentation index for AI agents is{' '}
                            <a href="https://docs.flagsmith.com/llms.txt" tabIndex={-1}>
                                llms.txt
                            </a>
                            . Append <code>.md</code> to any page URL to get the Markdown version.
                        </blockquote>
                        <DocBreadcrumbs />
                        <DocVersionBadge />
                        {docTOC.mobile}
                        <DocItemContent>{children}</DocItemContent>
                        <div className="row">
                            <div className={clsx('col', contentWidth)}>
                                <DocItemFooter />
                            </div>
                        </div>
                    </article>
                    <div className="row">
                        <div className={clsx('col', contentWidth)}>
                            <DocItemPaginator />
                        </div>
                    </div>
                </div>
            </div>
            {docTOC.desktop && <div className="col col--3">{docTOC.desktop}</div>}
        </div>
    );
}
