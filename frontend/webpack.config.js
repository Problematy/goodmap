const webpack = require('webpack');
module.exports = {
    entry:  __dirname + '/src/map.js',
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
