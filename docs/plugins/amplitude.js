import ExecutionEnvironment from '@docusaurus/ExecutionEnvironment';
import * as amplitude from '@amplitude/analytics-browser';

if (ExecutionEnvironment.canUseDOM) {
    window.addEventListener('load', () => {
        amplitude.init("541e058ce750dcdeb3a39d48a85f3425", {
            defaultTracking: true,
            serverZone: 'EU'
        });
    });
}
