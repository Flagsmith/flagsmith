const Project = require('../common/project');

const app = require('express')();

// Some infrastructure (e.g. Kubernetes) needs simple healthchecks
app.get('/health', (req, res) => {
    console.log('Healthcheck complete');
    res.send('OK');
});

app.get('/robots.txt', (req, res) => {
    res.send('User-agent: *\r\nDisallow: /');
});

const port = process.env.PORT || 8080;

app.listen(port, () => {
    console.log(`Server listening on: ${port}`);
    
});

module.exports = app;
