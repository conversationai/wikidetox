<template>
  <transition name="fade">
    <div :class="['monthly-timeline-wrapper', {'scrollUp': commentClicked}]"
          v-if="monthDatas.length > 0">
        <div v-for = "(d, i) in monthDatas"
            :key="`month-${i}`"
            class="button-wrapper">
          <div :class="['monthly-button', { selected: d.timestamp === dataTimeRange.startTime }]"
              @click="changeMonth(d)"
              v-ripple>
            <span class="percent">{{d.percentage}}%</span>
            <span class="month-name">{{d.month}}</span>
            <svg :width="d.r * 2"
                :height="d.r * 2">
              <circle :cx="d.r" :cy="d.r" :r="d.r" fill="#E73C5B" />
            </svg>
          </div>

           <span class='year' v-if="d.month === 'JAN'">
            <span>{{d.year}}</span>
          </span>

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
        const share = d.share
        const percentage = (share * 100).toFixed(3)
        const r = Math.round(Math.sqrt(percentage * 1000))
        return { timestamp, year, month, percentage, r }
      })
      this.commitDataLength(this.monthDatas[this.monthDatas.length - 1])
    },
    changeMonth (d) {
      if (d.timestamp !== this.selected) {
        this.$store.commit('CHANGE_TIME', d.timestamp)
        this.commitDataLength(d)
      }
    },
    commitDataLength (d) {
      const ind = this.monthDatas.indexOf(d)
      const pert = this.monthDatas[ind].percentage
      const increase = (pert - this.monthDatas[ind - 1].percentage) / this.monthDatas[ind - 1].percentage
      this.$store.commit('MONTHLY_CHANGE', increase.toFixed(3))
    }
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped lang="scss">
  .monthly-timeline-wrapper {
    position: absolute;
    top: 0;
    right: 0;
    height: 52px;
    width: 100%;
    overflow-x: scroll;
    direction: rtl;
    overflow-y: hidden;
    white-space: nowrap;
    transition: .2s bottom;
    z-index: 1000;
    @include box-shadow

    &::-webkit-scrollbar {
      display: none;
    }
    &.scrollUp{
      top: -52px;
    }

    .button-wrapper {
      position: relative;
      display: inline-flex;
      align-items: center;
      cursor: pointer;
      height: 100%;
      font-size: 12px;
      color: $darker-text;

      .year {
        margin: -5px 20px 0 20px;
      }

      .percent {
        color: $red;
      }

      .monthly-button {
        width: 168px;
        height: 100%;
        display: flex;
        align-items: center;
        justify-content: center;
        opacity: 0.6;

        .month-name {
          margin: 0 10px;
        }
        svg {
          display: inline-block;
        }
        &.selected {
          border-bottom: 5px solid $red;
          opacity: 1;
          .month-name {
            font-weight: 600;
          }
        }
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
