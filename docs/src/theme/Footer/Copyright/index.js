import React from 'react';
export default function FooterCopyright({ copyright }) {
    return (
        <div>
            <div
                className="footer__copyright"
                // Developer provided the HTML, so assume it's safe.
                // eslint-disable-next-line react/no-danger
                dangerouslySetInnerHTML={{ __html: copyright }}
            />
            <img
                referrerpolicy="no-referrer-when-downgrade"
                src="https://static.scarf.sh/a.png?x-pxid=3bd13eaa-d37d-454b-b503-322643e72574"
            />
        </div>
    );
}
