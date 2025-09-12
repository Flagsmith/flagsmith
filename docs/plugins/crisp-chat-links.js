// Plugin code based on https://stackoverflow.com/a/74736980

import ExecutionEnvironment from '@docusaurus/ExecutionEnvironment';

const enableCrispLinks = () => {
    document.querySelectorAll('.open-chat').forEach((oc) => {
        oc.style.cursor = 'pointer';
        oc.onclick = ({ target }) => {
            if (typeof $crisp !== 'undefined') {
                $crisp.push(['do', 'chat:open']);
                let dataCrispChatMessage = target.getAttribute('data-crisp-chat-message');
                if (dataCrispChatMessage) {
                    $crisp.push(['set', 'message:text', [dataCrispChatMessage]]);
                }
            }
        };
    });
};

export function onRouteDidUpdate({ location, previousLocation }) {
    // Don't execute if we are still on the same page; the lifecycle may be fired
    // because the hash changes (e.g. when navigating between headings)
    if (location.pathname === previousLocation?.pathname) return;
    enableCrispLinks();
}

if (ExecutionEnvironment.canUseDOM) {
    // We also need to setCodeRevealTriggers when the page first loads; otherwise,
    // after reloading the page, these triggers will not be set until the user
    // navigates somewhere.
    window.addEventListener('load', () => {
        setTimeout(enableCrispLinks, 1000);
    });
}
