<template>
  <transition name="fade">
    <div class="monthly-timeline-wrapper"
        v-if="datas.length !== 0">
        <div v-for = "(d, i) in datas.slice(0, datas.length-1)"
            :key="`month-${i}`"
            :class="['monthly-button', { selected: d.timestamp === dataTimeRange.startTime }]"
            @click="changeMonth(d)"
            v-ripple>

          <span class='year' v-if="d.month === 'JAN'">
            <span class='year-line'></span>
            <span class='year-text'>{{d.year}}</span>
          </span>
          <span class="month-name">{{d.month}}</span>
          <svg :width="d.r * 2 + 2"
               :height="d.r * 2 + 2">
            <defs>
              <linearGradient id="gradient" x1="0%" x2="0%" y1="100%" y2="0%">
                <stop :offset="d.percentage" stop-color="#E73C5B"></stop>
                <stop :offset="d.percentage" stop-color="#ffffff"></stop>
              </linearGradient>
            </defs>
            <circle :cx="d.r" :cy="d.r" :r="d.r" stroke-width="1" stroke="#E73C5B" fill="url(#gradient)" />
          </svg>
        </div>
    </div>
  </transition>
</template>

<script>
import { mapGetters } from 'vuex'
import QueryMixin from '../mixin/QueryMixin.js'

const monthNames = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEPT', 'OCT', 'NOV', 'DEC']

export default {
  name: 'MonthlyTrend',
  mixins: [QueryMixin],
  data () {
    return {
      datas: [],
      selected: null,
      circleScale: 16
    }
  },
  computed: {
    ...mapGetters({
      dataTimeRange: 'getDataTimeRange'
    })
  },
  mounted () {
    // window.addEventListener('resize', this.onResize)
    this.getData()
  },
  beforeDestroy () {
    //  window.removeEventListener('resize', this.onResize)
  },
  methods: {
    getData () {
      this.getQuery(this.monthlyTimelineQuery).then(results => {
        const monthDatas = results.map(async d => {
          const timestamp = d.f[0].v
          const year = parseInt(timestamp.substr(0, 4))
          const monthString = timestamp.substr(5, 2)
          const monthNum = monthString.startsWith('0') ? parseInt(monthString.substr(1, 1)) : parseInt(monthString)
          const month = monthNames[monthNum - 1]
          const detoxed = parseInt(d.f[2].v)
          const total = parseInt(d.f[1].v)
          const toxic = total - detoxed
          const percentage = detoxed / total
          const r = Math.round(Math.sqrt(total) / 5)
          return { timestamp, year, month, total, toxic, detoxed, percentage, r }
        })
        Promise.all(monthDatas).then(datas => {
          this.datas = datas
          const selected = this.datas.find(data => data.timestamp === this.dataTimeRange.startTime)
          const lastMonth = this.datas[this.datas.indexOf(selected) - 1]
          this.$store.commit('CHANGE_DATA_LENGTH', {
            toxicLength: selected.toxic,
            detoxedLength: selected.detoxed,
            lastMonth: lastMonth.toxic
          })
        })
      })
    },
    changeMonth (d) {
      this.$store.commit('CHANGE_TIME', d.timestamp)
      const lastMonth = this.datas[this.datas.indexOf(d) + 1]
      this.$store.commit('CHANGE_DATA_LENGTH', {
        toxicLength: d.toxic,
        detoxedLength: d.detoxed,
        lastMonth: lastMonth ? lastMonth.toxic : 0
      })
    }
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped lang="scss">
  .monthly-timeline-wrapper {
    position: fixed;
    bottom: 0;
    left: 0;
    background: $white;
    height: 76px;
    width: 100vw;
    overflow-x: scroll;
    direction: rtl;
    overflow-y: hidden;
    white-space: nowrap;
    &::-webkit-scrollbar {
      display: none;
    }
    .monthly-button {
      position: relative;
      display: inline-block;
      cursor: pointer;
      max-width: 168px;
      min-width: 108px;
      width: 8.8vw;
      height: 76px;
      display: inline-flex;
      align-items: center;
      justify-content: center;

      &.selected {
        border-top: 3px solid $red;
        .month-name {
          color: $darker-text;
          font-weight: 600;
        }
      }
      .year {
        position: absolute;
        top: 0;
        left: 0;
        .year-line {
          display: block;
          position: absolute;
          width: 2px;
          height: 50px;
          background: $light-border;
          top: 24px;
          left: 0;
        }
        .year-text {
          display: block;
          position: absolute;
          top: 2px;
          left: -15px;
        }
      }
      svg {
        display: inline-block;
        margin-right: 10px;
      }
    }
  }
  .fade-enter-active,
  .fade-leave-active {
    transition: opacity .5s;
    opacity: 1;
  }

  .fade-enter,
  .fade-leave-to
  /* .fade-leave-active below version 2.1.8 */
  {
    opacity: 0;
  }
</style>
