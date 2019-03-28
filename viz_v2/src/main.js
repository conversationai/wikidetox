import Vue from 'vue'
import App from './App.vue'
import store from './store'
import Ripple from 'vue-ripple-directive'

Ripple.color = 'rgba(0, 0, 0, 0.1)'
Ripple.zIndex = 2000
Vue.directive('ripple', Ripple)

Vue.config.productionTip = false

new Vue({
  store,
  render: h => h(App)
}).$mount('#app')
