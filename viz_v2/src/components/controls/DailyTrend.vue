<template>
  <div :class = "['timeline-wrapper', {'hide': hide}]" >
    <svg :width="width" :height="20" v-if="bars.length !== 0">
        <text
          v-for="(d, i) in bars"
          :key="`text${i}`"
          :class="{ hover: hoverIndex === i }"
          text-anchor="middle"
          :width="rangeWidth"
          :x="d.x + rangeWidth/2 - 16"
          y="10">
          {{d.label}}
        </text>
    </svg>
    <svg :width="width" :height="height"
          v-if="bars.length !== 0"
          @mouseleave="mouseOut()">
      <line
          v-for="(d, i) in bars"
          :key="`line${i}`"
          :x1="d.x" y1="0" :x2="d.x" y2="0"
          stroke="rgba(0,0,0,0.8)"
          stroke-width="2" />
      <rect
          v-for="(d, i) in bars"
          :key="`rect${i}`"
          :x="d.x - rangeWidth/2" y="0"
          :width="rangeWidth"
          :height="height"
          fill="transparent"
          @mouseenter="mouseOver(i)"
          @mouseleave="hoverIndex = null"
          />
    </svg>
  </div>
</template>

<script>
import { mapState, mapGetters } from 'vuex'
import anime from 'animejs'
import * as d3 from 'd3'
import QueryMixin from '../mixin/QueryMixin.js'
import { setTimeout } from 'timers'
export default {
  name: 'DailyTrend',
  mixins: [QueryMixin],
  data () {
    return {
      width: 0,
      height: 20,
      circleLeft: -20,
      datas: [],
      bars: [],
      hoverIndex: null,
      hide: false
    }
  },
  computed: {
    ...mapState({
      hoveredComment: state => state.selectedComment,
      commentClicked: state => state.commentClicked
    }),
    ...mapGetters({
      dataTimeRange: 'getDataTimeRange'
    }),
    maxY () {
      return d3.max(this.datas, d => parseInt(d.f[1].v))
    },
    scaleX () {
      const domainX = [new Date(this.dataTimeRange.startTime), new Date(this.dataTimeRange.endTime)]
      return d3.scaleTime()
        .domain(domainX)
        .rangeRound([this.width * 0.03 + 28, this.width - 28])
    },
    scaleY () {
      return d3.scaleLinear()
        .domain([this.maxY, 0]).nice()
        .rangeRound([this.height - 18, 0])
    },
    rangeWidth () {
      return this.width / this.datas.length
    }
  },
  watch: {
    commentClicked (clicked, oldVal) {
      if (clicked) {
        this.hoverIndex = null
        this.exitAnimation()
      } else {
        this.loadAnimation()
      }
    },
    hoveredComment (newVal, oldVal) {
      if (!this.commentClicked) {
        if (newVal !== null) {
          const data = newVal.comment
          const date = data.timestamp.toISOString().substr(0, 10)
          const ind = this.bars.findIndex(d => d.label === date)
          this.animateMouseover(ind)
        } else if (newVal === null) {
          this.animateMouseleave()
        }
      }
    },
    dataTimeRange () {
      this.getData()
    }
  },
  mounted () {
    window.addEventListener('resize', this.onResize)
    this.getData()
  },
  beforeDestroy () {
    window.removeEventListener('resize', this.onResize)
  },
  methods: {
    getData () {
      this.getQuery(this.dailyTimelineQuery).then(data => {
        this.datas = data
        this.onResize()
      })
    },
    onResize () {
      this.width = window.innerWidth
      this.height = window.innerHeight * 0.04 > 20 ? window.innerHeight * 0.04 : 80
      this.drawBars()
      if (!this.commentClicked) {
        setTimeout(() => {
          this.loadAnimation()
        }, 100)
      }
    },
    drawBars () {
      this.bars = this.datas.map((d, i) => {
        return {
          x: this.scaleX(new Date(d.f[0].v)),
          label: d.f[0].v
        }
      })
    },
    loadAnimation () {
      anime({
        begin: () => {
          if (this.hide) this.hide = false
        },
        targets: 'line',
        y2: {
          value: (el, i) => {
            return this.scaleY(this.datas[i].f[1].v)
          },
          easing: 'linear',
          delay: (el, i) => {
            return i * 6
          },
          duration: 200
        }
      })
    },
    exitAnimation () {
      anime({
        targets: 'line',
        y2: {
          value: (el, i) => {
            return this.scaleY(0)
          },
          easing: 'linear',
          delay: (el, i) => {
            return i * 6
          },
          duration: 200
        },
        complete: () => {
          this.hide = true
        }
      })
    },
    mouseOver (index) {
      const selectedDate = this.bars[index].label
      this.$store.commit('SELECT_DATE', selectedDate)
      this.animateMouseover(index)
    },
    mouseOut () {
      this.$store.commit('SELECT_DATE', null)
      this.animateMouseleave()
    },
    animateMouseover (index) {
      this.hoverIndex = index
      anime({
        targets: 'line',
        stroke: {
          value: (el, i) => {
            return i === index ? '#FF4B4B' : 'rgba(0,0,0,.8)'
          },
          easing: 'linear',
          duration: 100
        },
        strokeWidth: {
          value: (el, i) => {
            return i === index ? 10 : 2
          },
          easing: 'linear',
          duration: 100
        }
      })
    },
    animateMouseleave () {
      this.hoverIndex = null
      anime({
        targets: 'line',
        stroke: {
          value: 'rgba(0,0,0,.8)',
          easing: 'linear',
          duration: 100,
          delay: 100
        },
        strokeWidth: {
          value: 2,
          easing: 'linear',
          duration: 100,
          delay: 100
        }
      })
    }
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped lang="scss">
  .timeline-wrapper {
    height: 8vh;
    width: 100vw;
    position: fixed ;
    left: 0;
    bottom: $bottom;
    background: transparent;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    z-index: 1000;
    display: block;
    .hide {
      display: none;
    }
    svg {
      rect {
        cursor: pointer;
      }
      text {
        opacity: 0;
        transition: .2s opacity;
        z-index: 1000;
        &.hover {
          opacity: 1;
        }
      }
      &:last-of-type {
        position: absolute;
        bottom: 10px;
        left: 0;
        transform: rotateX(180deg)
      }
    }
  }

</style>
