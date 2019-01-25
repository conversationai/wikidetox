import Vue from 'vue'
import Vuex from 'vuex'

import * as models from './assets/models.json'
Vue.use(Vuex)
const toxModels = models.default

export default new Vuex.Store({
  state: {
    DATA_START_TIME: '2015-01-01',
    DATA_END_TIME: '2018-06-30',
    SELECTED_YEAR: 2018,
    SELECTED_MONTH: 2,
    sort: 'all',
    datas: [],
    pageTrends: []
  },
  getters: {
    getDataTimeRange: state => {
      const month = state.SELECTED_MONTH
      const year = state.SELECTED_YEAR
      const endMonth = month === 12 ? 1 : month + 1
      const endYear = month === 12 ? year + 1 : year
      const startTime = `${year}-${month}-1`
      const endTime = `${endYear}-${endMonth}-1`
      console.log(startTime)
      console.log(endTime)
      return { startTime, endTime }
    },
    getMonthlyTrendStart: state => {
      const month = state.SELECTED_MONTH
      const year = state.SELECTED_YEAR
      return `${year - 1}-${month}-1`
    },
    getDatalength: state => {
      return state.datas.length
    },
    getDeleted: state => {
      return state.datas.filter(data => data['type'] === 'DELETION')
    },
    getDeletedLength: (state, getters) => {
      return getters.getDeleted.length
    },
    getTalkpage: state => {
      return state.datas.filter(data => data['page_title'].startsWith('Talk:'))
    },
    getTalkpageLength: (state, getters) => {
      return getters.getTalkpage.length
    },
    getUserpage: state => {
      return state.datas.filter(data => data['page_title'].startsWith('User talk:'))
    },
    getUserpageLength: (state, getters) => {
      return getters.getUserpage.length
    },
    getModelsLengths: state => {
      const modelObj = toxModels.map(m => {
        const modelData = state.datas.filter(data => data[m.name] > 0.8)
        return {
          model: m.model,
          name: m.name,
          length: modelData.length
        }
      })
      modelObj.sort((a, b) => {
        return b.length - a.length
      })
      return modelObj
    }
  },
  mutations: {
    CHANGE_SORTBY (state, sortby) {
      state.sort = sortby
    },
    CHANGE_TIME (state, newtime) {
      state.SELECTED_START_TIME = newtime
      state.SELECTED_END_TIME = newtime
    },
    SET_DATA (state, data) {
      state.datas = data
    },
    SET_PAGE_TRENDS (state, data) {
      localStorage.setItem('page_trends', JSON.stringify(data))
      state.pageTrends = data
    }
  }
})
