import ExecutionEnvironment from '@docusaurus/ExecutionEnvironment';
import amplitude from '@amplitude/analytics-browser';

if (ExecutionEnvironment.canUseDOM) {
    amplitude.init('541e058ce750dcdeb3a39d48a85f3425');
}
