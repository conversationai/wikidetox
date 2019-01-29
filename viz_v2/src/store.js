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
    display: 'all',
    datas: [],
    toxicLength: 0,
    detoxedLength: 0,
    monthlyIncrease: 0,
    pageTrends: []
  },
  getters: {
    getDataTimeRange: state => {
      const month = state.SELECTED_MONTH
      const year = state.SELECTED_YEAR
      const endMonth = month === 12 ? 1 : month + 1
      const monthString = month < 10 ? `0${month}` : `${month}`
      const endMonthString = endMonth < 10 ? `0${endMonth}` : `${endMonth}`
      const endYear = month === 12 ? year + 1 : year
      const startTime = `${year}-${monthString}-01`
      const endTime = `${endYear}-${endMonthString}-01`
      return { startTime, endTime }
    },
    // getMonthlyTrendStart: state => {
    //   const month = state.SELECTED_MONTH
    //   const year = state.SELECTED_YEAR
    //   return `${year - 1}-${month}-1`
    // },
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
      return modelObj.slice(0, 6)
    }
  },
  mutations: {
    CHANGE_SORTBY (state, sortby) {
      state.sort = sortby
    },
    CHANGE_DISPLAY (state, display) {
      state.display = display
    },
    CHANGE_TIME (state, newtime) {
      const monthString = newtime.substr(5, 2)
      state.SELECTED_YEAR = parseInt(newtime.substr(0, 4))
      state.SELECTED_MONTH = monthString.startsWith('0') ? parseInt(monthString.substr(1, 1)) : parseInt(monthString)
    },
    CHANGE_DATA_LENGTH (state, lengths) {
      state.toxicLength = lengths.toxicLength
      state.detoxedLength = lengths.detoxedLength
      state.monthlyIncrease = ((lengths.toxicLength - lengths.lastMonth) / lengths.lastMonth * 100).toFixed(1)
    },
    SET_DATA (state, data) {
      state.datas = data
    },
    SET_PAGE_TRENDS (state, data) {
      // localStorage.setItem('page_trends', JSON.stringify(data))
      state.pageTrends = data
    }
  }
})
