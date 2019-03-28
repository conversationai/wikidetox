const path = require('path')

module.exports = {
  outputDir: path.resolve(__dirname, './build/static'),
  devServer: {
    proxy: 'http://localhost:8080'
  },
  css: {
    loaderOptions: {
      sass: {
        data: `@import "@/variables.scss";`
      }
    }
  }
}
