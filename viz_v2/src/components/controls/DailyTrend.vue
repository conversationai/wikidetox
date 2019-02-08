<template>
  <div class="timeline-wrapper">
    <svg :width="width" :height="20" v-if="bars.length !== 0">
        <text
          v-for="(d, i) in bars"
          :key="`text${i}`"
          :class="{ hover: hoverIndex === i }"
          text-anchor="middle"
          :width="rangeWidth"
          :x="d.x + rangeWidth/2 - 10"
          y="10">
          {{d.label}}
        </text>
    </svg>
    <svg :width="width" :height="height-20"
          v-if="bars.length !== 0"
          @mouseleave="animateMouseleave()">
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
          @mouseenter="animateMouseover(i)"
          @mouseleave="hoverIndex = null"
          />
    </svg>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'
import anime from 'animejs'
import * as d3 from 'd3'

import QueryMixin from '../mixin/QueryMixin.js'

export default {
  name: 'DailyTrend',
  mixins: [QueryMixin],
  data () {
    return {
      width: 0,
      height: 20,
      datas: [],
      bars: [],
      hoverIndex: null
    }
  },
  computed: {
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
        .rangeRound([this.height - 24, 0])
    },
    rangeWidth () {
      return this.width / this.datas.length
    }
  },
  watch: {
    dataTimeRange (oldVal, newVal) {
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
        // localStorage.setItem('daily_trends', JSON.stringify(data))
        this.onResize()
      })
    },
    onResize () {
      this.width = window.innerWidth > 1000 ? 800 : window.innerWidth
      this.height = window.innerHeight * 0.06
      this.drawBars()
      setTimeout(() => {
        this.loadAnimation()
      }, 100)
    },
    drawBars () {
      this.bars = this.datas.map((d, i) => {
        // console.log(d.f[0].v)
        return {
          x: this.scaleX(new Date(d.f[0].v)),
          label: d.f[0].v
        }
      })
    },
    loadAnimation () {
      anime({
        targets: 'line',
        y2: {
          value: (el, i) => {
            return this.scaleY(this.datas[i].f[1].v)
          },
          easing: 'linear',
          delay: (el, i) => {
            return i * 6
          },
          duration: 100
        }
      })
    },
    animateMouseover (index) {
      this.hoverIndex = index
      anime({
        targets: 'line',
        stroke: {
          value: (el, i) => {
            const dist = Math.abs(index - i)
            const finaldist = dist > 10 ? 10 : dist
            const gradient = `rgba(0,0,0, ${0.8 - (finaldist * 0.06)})`
            return i === index ? '#FF4B4B' : gradient
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
    width: 94vw;
    position: fixed ;
    left: 6vw;
    bottom: 90px;
    background: transparent;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    z-index: 1000;
    svg {
      rect {
        cursor: pointer;
      }
      text {
        opacity: 0;
        transition: .2s opacity;
        &.hover {
          opacity: 1;
        }
      }
      &:last-of-type {
        transform: rotateX(180deg)
      }
    }
  }
</style>
