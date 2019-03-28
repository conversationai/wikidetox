<template>
  <transition name="fade">
    <div :class="['monthly-timeline-wrapper', {'scrollDown': commentClicked}]"
          v-if="monthDatas.length > 0">
        <div v-for = "(d, i) in monthDatas"
            :key="`month-${i}`"
            :class="['monthly-button', { selected: d.timestamp === dataTimeRange.startTime }]"
            @click="changeMonth(d)"
            v-ripple>
          <span class='year' v-if="d.month === 'JAN'">
            <span class='year-line'></span>
            <span class='year-text'>{{d.year}}</span>
          </span>
          <span class="month-name">{{d.month}}</span>
          <svg :width="d.r * 2"
               :height="d.r * 2">
            <circle :cx="d.r" :cy="d.r" :r="d.r" fill="#E73C5B" />
          </svg>
        </div>
    </div>
  </transition>
</template>

<script>
import { mapState, mapGetters } from 'vuex'

const monthNames = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEPT', 'OCT', 'NOV', 'DEC']

export default {
  name: 'MonthlyTrend',
  props: ['datas'],
  data () {
    return {
      selected: null,
      monthDatas: []
    }
  },
  computed: {
    ...mapState({
      commentClicked: state => state.commentClicked
    }),
    ...mapGetters({
      dataTimeRange: 'getDataTimeRange'
    })
  },
  watch: {
    datas (newVal, oldVal) {
      if (newVal.length > 0) {
        this.initData()
      }
    }
  },
  methods: {
    initData () {
      this.monthDatas = this.datas.map((d, i) => {
        const timestamp = d.month.value
        const year = parseInt(timestamp.substr(0, 4))
        const monthString = timestamp.substr(5, 2)
        const monthNum = monthString.startsWith('0') ? parseInt(monthString.substr(1, 1)) : parseInt(monthString)
        const month = monthNames[monthNum - 1]
        const total = d.cd
        const r = Math.round(Math.sqrt(total) / 3)
        return { timestamp, year, month, total, r }
      })
      const selectedMonth = this.monthDatas.find(d => d.timestamp === this.dataTimeRange.startTime)
      this.commitDataLength(selectedMonth)
    },
    commitDataLength (selectedMonth) {
      this.selected = selectedMonth.timestamp
      const lastMonthInd = this.monthDatas.indexOf(selectedMonth) + 1
      const isFirst = lastMonthInd >= this.monthDatas.length
      const lastToxicLength = isFirst ? 0 : this.monthDatas[lastMonthInd].total
      this.$store.commit('CHANGE_DATA_LENGTH', {
        toxicLength: selectedMonth.total,
        lastToxicLength: lastToxicLength
      })
    },
    changeMonth (d) {
      if (d.timestamp !== this.selected) {
        this.$store.commit('CHANGE_TIME', d.timestamp)
        this.commitDataLength(d)
      }
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
    transition: .2s bottom;
    z-index: 1000;
    &::-webkit-scrollbar {
      display: none;
    }
    &.scrollDown{
      bottom: -78px;
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
