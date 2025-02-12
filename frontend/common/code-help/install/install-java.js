import Utils from 'common/utils/utils'

module.exports = () => `// Maven
${Utils.escapeHtml('<dependency>')}
    ${Utils.escapeHtml('<groupId>com.flagsmith</groupId>')}
    ${Utils.escapeHtml('<artifactId>flagsmith-java-client</artifactId>')}
    ${Utils.escapeHtml('<version>7.4.1</version>')}
${Utils.escapeHtml('</dependency>')}

// Gradle
implementation 'com.flagsmith:flagsmith-java-client:7.4.1'
`
