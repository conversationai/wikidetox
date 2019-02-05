import Vue from 'vue'
import App from './App.vue'
import store from './store'
import Element from 'element-ui'
import VueGAPI from 'vue-gapi'
import * as config from './config.json'
import 'element-ui/lib/theme-chalk/index.css'
import Ripple from 'vue-ripple-directive'

Ripple.color = 'rgba(0, 0, 0, 0.1)'
Ripple.zIndex = 2000
Vue.directive('ripple', Ripple)

Vue.use(Element, { size: 'large', zIndex: 3000 })

const apiConfig = {
  clientId: config.default.client_id,
  scope: 'https://www.googleapis.com/auth/bigquery'
}

Vue.use(VueGAPI, apiConfig)

Vue.config.productionTip = false

new Vue({
  store,
  render: h => h(App)
}).$mount('#app')
