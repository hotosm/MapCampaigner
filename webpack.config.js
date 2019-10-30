const path = require('path')
const MiniCssExtractPlugin = require('mini-css-extract-plugin')

const mode = process.env.NODE_ENV;

module.exports = [
  {
    entry: {
      // These scripts are installed from package.json with npm
      vendor: [
        'jquery/dist/jquery.min.js', // Remove .slim if full version needed
        'bootstrap/dist/js/bootstrap.min.js', // TODO: Only include needed comps
        'metismenu/dist/metisMenu.min.js',
        'leaflet/dist/leaflet.js',
        'mapbox-gl/dist/mapbox-gl.js',
        'gasparesganga-jquery-loading-overlay/src/loadingoverlay.min.js',
        'datatables.net/js/jquery.dataTables.min.js',
        'datatables.net-rowreorder/js/dataTables.rowReorder.min.js',
        'datatables.net-responsive/js/dataTables.responsive.min.js',
        'moment/moment.js',
        'datatables.net-plugins/sorting/datetime-moment.js',
        'chart.js/dist/Chart.bundle.min.js'
      ],
      // These scripts are committed to this repo
      legacy: [
        './flask_project/campaign_manager/static/js/map-campaigner.js',
        './flask_project/campaign_manager/static/libs/geojson-bounds/geojson-bounds.js',
        './flask_project/campaign_manager/static/libs/osmauth.js',
        './flask_project/campaign_manager/static/libs/leaflet-color-markers/leaflet-color-markers.js',
        './flask_project/campaign_manager/static/js/datepicker.min.js',
        './flask_project/campaign_manager/static/js/datepicker.en.js',
        './flask_project/campaign_manager/static/libs/leaflet-search.js',
        './flask_project/campaign_manager/static/libs/js.cookie-2.1.4.min.js',
        './flask_project/campaign_manager/static/libs/jquery-file-upload/jquery.ui.widget.js',
        './flask_project/campaign_manager/static/libs/jquery-file-upload/jquery.fileupload.js'
      ]
    },
    output: {
      filename: '[name].js',
      path: path.resolve(__dirname, 'flask_project/campaign_manager/static/dist'),
    },
    module: { rules: [{ test: /\.js$/, use: 'script-loader' }] },
    mode
  },
  {
    entry: {
      main: [
        './flask_project/campaign_manager/index.js',
        './flask_project/campaign_manager/styles/index.scss'
      ]
    },
    output: {
      filename: '[name].js',
      path: path.resolve(__dirname, 'flask_project/campaign_manager/static/dist'),
    },
    plugins: [
      new MiniCssExtractPlugin({
        // Options similar to the same options in webpackOptions.output
        filename: '[name].css',
        chunkFilename: '[id].css',
        ignoreOrder: false, // Enable to remove warnings about conflicting order
      })
    ],
    module: {
      rules: [
        {
          test: /\.m?js$/,
          exclude: /(node_modules|bower_components)/,
          use: [{
            loader: 'babel-loader',
            options: {
              presets: ['@babel/preset-env']
            }
          }]
        },
        {
          test: /\.[s]?css$/,
          use: [
            {
              loader: MiniCssExtractPlugin.loader,
              options: {
                hmr: process.env.NODE_ENV === 'development',
              },
            },
            'css-loader',
            'sass-loader',
          ],
        }
      ],
    },
    mode
  }
];
