<template>
  <div id="app">
    <ParticleSystem />
    <CommentDetails />
    <CommentControls />
    <BubbleChart />
    <MetricsPanel />
    <MonthlyMetrics />
    <DailyTrend />
    <MonthlyTrend />
  </div>
</template>

<script>
import ParticleSystem from './components/canvas/ParticleSystem.vue'
import CommentDetails from './components/canvas/comments/CommentDetails.vue'
import CommentControls from './components/canvas/comments/CommentControls.vue'
import BubbleChart from './components/canvas/BubbleChart.vue'
import MetricsPanel from './components/controls/MetricsPanel.vue'
import MonthlyMetrics from './components/controls/MonthlyMetrics.vue'
import DailyTrend from './components/controls/DailyTrend.vue'
import MonthlyTrend from './components/controls/MonthlyTrend.vue'

import QueryMixin from './components/mixin/QueryMixin.js'
import * as toxModels from './assets/models.json'
import { mapState, mapGetters } from 'vuex'

export default {
  name: 'app',
  mixins: [QueryMixin],
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
      models: toxModels.default
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
  created () {
    if (this.$isAuthenticated() !== true) {
      this.$login()
    }
  },
  mounted () {
    if (this.toxLength === 0) {
      console.log('Datas not saved')
      this.getAllData()
      this.getTopTrends()
    }
  },
  watch: {
    dataTimeRange (oldVal, newVal) {
      console.log('data range changed')
      this.getAllData()
      this.getTopTrends()
    }
  },
  methods: {
    getAllData () {
      this.getQuery(this.dataQuery).then(datas => {
        const allData = datas.map(d => {
          let dataModels = {}
          for (const prop in this.models) {
            dataModels[this.models[prop].name] = d.f[parseInt(prop) + 1].v
          }
          return {
            'Toxicity': d.f[0].v,
            'Category': d.f[13].v,
            'Sub Category': d.f[14].v,
            'page_id': d.f[15].v,
            'page_title': d.f[16].v,
            'id': d.f[17].v,
            'username': d.f[18].v,
            'timestamp': d.f[19].v,
            'content': d.f[20].v,
            'type': d.f[21].v,
            ...dataModels
          }
        })
        allData.sort((a, b) => {
          return a.timestamp - b.timestamp
        })
        // console.log(allData)
        this.$store.commit('SET_DATA', allData)
      })
    },
    getTopTrends () {
      this.getQuery(this.pageTrendQuery).then(datas => {
        const trendData = datas.map(d => {
          const category = d.f[1].v === null ? d.f[0].v : d.f[1].v
          return {
            category: category,
            length: d.f[2].v
          }
        })
        this.$store.commit('SET_PAGE_TRENDS', trendData)
      })
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
