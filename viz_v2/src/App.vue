<template>
  <div id="app">
    <ParticleSystem />
    <CommentDetails />
    <CommentControls />
    <BubbleChart />
    <MetricsPanel />
    <MonthlyMetrics />
    <MonthlyTrend :datas="monthlyTrendsData" />
    <DailyTrend :datas="dailyTrendsData" />
  </div>
</template>

<script>
import ParticleSystem from './components/canvas/ParticleSystem.vue'
import CommentDetails from './components/canvas/comments/CommentDetails.vue'
import CommentControls from './components/canvas/comments/CommentControls.vue'
import BubbleChart from './components/canvas/BubbleChart.vue'
import MetricsPanel from './components/controls/MetricsPanel.vue'
import MonthlyMetrics from './components/controls/MonthlyMetrics.vue'
import MonthlyTrend from './components/controls/MonthlyTrend.vue'
import DailyTrend from './components/controls/DailyTrend.vue'

import { mapState, mapGetters } from 'vuex'

export default {
  name: 'app',
  components: {
    ParticleSystem,
    CommentDetails,
    CommentControls,
    BubbleChart,
    MetricsPanel,
    MonthlyMetrics,
    MonthlyTrend,
    DailyTrend
  },
  data () {
    return {
      dataService: null,
      dailyTrendsData: [],
      monthlyTrendsData: [],
      dataStart: '2017-01-01'
    }
  },
  computed: {
    ...mapState({
      toxLength: state => state.toxicLength
    }),
    ...mapGetters({
      dataTimeRange: 'getDataTimeRange'
    })
  },
  mounted () {
    this.getDatas()
    this.getMonthlyTrends()
  },
  watch: {
    dataTimeRange (newVal, oldVal) {
      this.getDatas()
    }
  },
  methods: {
    getDatas () {
      const params = { st: this.dataTimeRange.startTime, end: this.dataTimeRange.endTime }

      this.postDatas(params, '/monthsdata').then(rows => {
        const datas = rows.map(row => {
          const unix = (new Date(row.timestamp.value)).getTime()
          return {
            unix: unix,
            ...row
          }
        })
        const sortedDatas = datas.sort((a, b) => {
          return a.unix - b.unix
        })
        this.$store.commit('SET_DATA', sortedDatas)
      })

      this.postDatas(params, 'dailytrends').then(rows => {
        this.dailyTrendsData = rows
      })
    },
    getMonthlyTrends () {
      const params = { st: this.dataStart }
      this.postDatas(params, 'monthlytrends').then(rows => {
        this.monthlyTrendsData = rows
      })
    },
    postDatas (params, url) {
      return fetch(url, {
        method: 'POST',
        mode: 'cors',
        cache: 'no-cache',
        credentials: 'same-origin',
        headers: {
          'Content-Type': 'application/json'
        },
        redirect: 'follow',
        body: JSON.stringify(params)
      }).then(res => {
        if (res.ok) {
          return res.json()
        } else {
          throw Error(`Request rejected with status ${res.status}`)
        }
      })
        .catch(error => console.error(error))
    }
  }
}
</script>

<style lang="scss">
  * {
    box-sizing: border-box;
  }

  html,
  body {
    margin: 0;
    padding: 0;
    width: 100vw;
    height: 100vh;
    overflow: hidden;
  }

  #app {
    width: 100vw;
    height: 100vh;
    font-size: 13px;
    font-family: 'Roboto Mono', sans-serif;
    overflow: hidden;
    position: relative;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
    background: $light-bg;
    color: $dark-text;
    line-height: 1.5;
  }
</style>
