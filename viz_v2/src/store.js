/*
Copyright 2019 Google Inc.
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at
    http://www.apache.org/licenses/LICENSE-2.0
Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
*/

import Vue from 'vue'
import Vuex from 'vuex'

import * as models from './assets/models.json'
Vue.use(Vuex)
const toxModels = models.default

export default new Vuex.Store({
  state: {
    SELECTED_YEAR: 2019,
    SELECTED_MONTH: 3,
    filterby: null,
    sortby: 'all',
    datas: [],
    toxicLength: 0,
    monthlyIncrease: 0,
    selectedComment: null, // hovered object
    commentClicked: false,
    nextComment: null,
    selectedDate: null,
    detoxedID: ''
  },
  getters: {
    dataLength: state => {
      return state.datas.length
    },
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
    getToxLength: state => {
      const data = state.datas.filter(data => {
        return data['type'] !== 'DELETION'
      })
      return data.length
    },
    getDetoxLength: state => {
      const data = state.datas.filter(data => {
        return data['type'] === 'DELETION'
      })
      return data.length
    },
    getTalkpage: state => {
      return state.datas.filter(data => {
        return data['page_title'].startsWith('Talk:') && data['type'] !== 'DELETION'
      })
    },
    getTalkpageLength: (state, getters) => {
      return getters.getTalkpage.length
    },
    getUserpage: state => {
      return state.datas.filter(data => {
        return data['page_title'].startsWith('User') && data['type'] !== 'DELETION'
      })
    },
    getUserpageLength: (state, getters) => {
      return getters.getUserpage.length
    },
    getPageTrend: state => {
      const categories = ['category1', 'category2', 'category3']

      const datas = state.datas.filter(d => d['type'] !== 'DELETION')
      const trends = datas.reduce((pageTrend, d) => {
        if (d['page_title'].startsWith('Talk:')) {
          for (const c of categories) {
            if (d[c] !== null) {
              const cat = d[`sub_${c}`] === null ? d[c] : d[`sub_${c}`]
              const existingName = pageTrend.find(trend => trend.cat === cat)
              if (existingName) {
                existingName.count++
              } else {
                pageTrend.push({
                  cat: cat,
                  count: 1
                })
              }
            }
          }
        }
        return pageTrend
      }, [])
      trends.sort((a, b) => {
        return b.count - a.count
      })
      return trends.slice(1, 5)
    },
    getModelsLengths: state => {
      const modelObj = toxModels.map(m => {
        const modelData = state.datas.filter(data => data[m.model] > 0.8 && data['type'] !== 'DELETION')
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
      state.sortby = sortby
    },
    CHANGE_DISPLAY (state, display) {
      state.display = display
    },
    CHANGE_TIME (state, newtime) {
      const monthString = newtime.substr(5, 2)
      state.SELECTED_YEAR = parseInt(newtime.substr(0, 4))
      state.SELECTED_MONTH = monthString.startsWith('0') ? parseInt(monthString.substr(1, 1)) : parseInt(monthString)
    },
    MONTHLY_CHANGE (state, newChange) {
      state.monthlyIncrease = newChange
    },
    SET_DATA (state, data) {
      state.datas = data
    },
    DETOX_COMMENT (state, id) {
      state.detoxedID = id
      const detoxedInd = state.datas.findIndex(d => {
        return d.id === id
      })
      state.datas[detoxedInd].type = 'DELETION'
    },
    CHANGE_FILTERBY (state, data) {
      state.filterby = data
    },
    CHANGE_COMMENT (state, data) {
      state.selectedComment = data
    },
    COMMENT_CLICK (state, data) {
      state.commentClicked = data
    },
    SELECT_DATE (state, date) {
      state.selectedDate = date
    }
  }
})
