const webpack = require('webpack');
const config = {
    entry:  __dirname + '/map.js',
    output: {
        path: __dirname + '/../goodmap/static',
        filename: 'map.js',
    },
    resolve: {
        extensions: ['.js', '.jsx', '.css']
    },

    module: {
        rules: [
            {
            test: /\.(js|jsx)?/,
                exclude: /node_modules/,
                use: 'babel-loader'
            }
        ]
    }
};
module.exports = config;
