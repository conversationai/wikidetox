<template>
  <div id="app">
    <ParticleSystem />
    <CommentDetails />
    <CommentControls />
    <BubbleChart />
    <!-- <MetricsPanel /> -->
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

import * as configFile from './config'
// import { BigQueryData } from './components/bigQuery.js'

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
      models: toxModels.default,
      config: configFile.default,
      bigQuery: null
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
    // this.bigQuery = new BigQueryData(this.config, this.dataTimeRange)
    // console.log(this.bigQuery)

    if (this.$isAuthenticated() !== true) {
      this.$login()
    }
  },
  mounted () {
    if (this.toxLength === 0) {
      this.getAllData()
    }
  },
  watch: {
    dataTimeRange (oldVal, newVal) {
      console.log('data range changed')
      this.getAllData()
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
          const date = new Date(parseFloat(d.f[18].v) * 1000)

          return {
            'Toxicity': d.f[0].v,
            'category1': d.f[8].v,
            'sub_category1': d.f[9].v,
            'category2': d.f[10].v,
            'sub_category2': d.f[11].v,
            'category3': d.f[12].v,
            'sub_category3': d.f[13].v,
            'page_id': d.f[14].v,
            'page_title': d.f[15].v,
            'id': d.f[16].v,
            'username': d.f[17].v,
            'timestamp': date,
            'content': d.f[19].v,
            'type': d.f[20].v,
            ...dataModels
          }
        })
        allData.sort((a, b) => {
          return a.timestamp - b.timestamp
        })
        // console.log(allData)
        this.$store.commit('SET_DATA', allData)
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
