const Router = require('express').Router;

module.exports = () => {
    const api = Router();

    api.get('/', (req, res) => {
        res.json({message: 'API is up and running!'})
    });

    return api;
};
