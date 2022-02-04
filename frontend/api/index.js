const Project = require('../common/project');

// Some infrastructure (e.g. Kubernetes) needs simple healthchecks
app.get('/health', (req, res) => {
    console.log('Healthcheck complete');
    res.send('OK');
});

app.get('/robots.txt', (req, res) => {
    res.send('User-agent: *\r\nDisallow: /');
});


module.exports = app;
