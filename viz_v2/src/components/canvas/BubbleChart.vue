<template>
  <svg id="bubblesContainer"
        :style="{ zIndex: zindex }"
        :width="width" :height="height" ref="bubblesContainer">
    <defs>
      <radialGradient spreadMethod="reflect"
      cx="50%" cy="50%" r="50%" fx="50%" fy="50%" fr="1%"
      id="flameGradient">
        <stop offset="0%" stop-color="#E896A8"/>
        <stop offset="100%" stop-color="#E63C5B"/>
      </radialGradient>
    </defs>
  </svg>
</template>

<script>
import {
  mapState,
  mapGetters
} from 'vuex'
import * as d3 from 'd3'

export default {
  name: 'ParticleSystem',
  data () {
    return {
      width: 0,
      height: 0,
      zindex: 1,
      randomizeScale: 18 // smaller number = more position randomization
    }
  },
  computed: {
    ...mapState({
      sortby: state => state.sortby,
      filterby: state => state.filterby,
      month: state => state.SELECTED_MONTH
    }),
    ...mapGetters({
      canvasState: 'getCanvas',
      talkpageLength: 'getTalkpageLength',
      userpageLength: 'getUserpageLength',
      models: 'getModelsLengths',
      trends: 'getPageTrend'
    }),
    bubbleData (sortby, month) {
      if (sortby === 'all') {
        d3.selectAll('.bubbles').remove()
        d3.selectAll('.bubbleContent').remove()
      } else {
        switch (this.sortby) {
          case 'trend':
            return this.trends.map(t => {
              return {
                name: t.cat,
                length: parseInt(t.count),
                randomX: this.random(this.width / this.randomizeScale),
                randomY: this.random(this.height / this.randomizeScale)
              }
            })
          case 'model':
            return this.models.map(m => {
              return {
                randomX: this.random(this.width / this.randomizeScale),
                randomY: this.random(this.height / this.randomizeScale),
                ...m
              }
            })
          case 'type':
            return [
              {
                name: 'Talk page',
                length: this.talkpageLength,
                randomX: this.random(this.width / this.randomizeScale),
                randomY: this.random(this.height / this.randomizeScale)
              },
              {
                name: 'User page',
                length: this.userpageLength,
                randomX: this.random(this.width / this.randomizeScale),
                randomY: this.random(this.height / this.randomizeScale)
              }
            ]
          default:
            return []
        }
      }
    }
  },
  watch: {
    canvasState (newVal, oldVal) {
      if (newVal === 'bubbles') {
        this.zindex = 100
      } else {
        this.zindex = 1
      }
    },
    filterby (newVal, oldVal) {
      if (newVal !== null) {
        d3.selectAll('.bubbles').remove()
        d3.selectAll('.bubbleContent').remove()
      } else {
        this.drawBubbles()
      }
    },
    bubbleData (newVal, oldVal) {
      if (this.filterby === null) {
        if (newVal.length > 0) {
          this.drawBubbles()
        } else {
          d3.selectAll('.bubbles').remove()
          d3.selectAll('.bubbleContent').remove()
        }
      }
    }
  },
  mounted () {
    window.addEventListener('resize', this.onResize, false)
    this.onResize()
  },
  beforeDestroy () {
    window.removeEventListener('resize', this.onResize)
  },
  methods: {
    onResize () {
      this.width = window.innerWidth * 0.9
      this.height = window.innerHeight - 106
      if (this.bubbleData.length > 0 && this.canvasState === 'bubbles') {
        this.drawBubbles()
      }
    },
    drawBubbles () {
      const data = {
        'children': this.bubbleData
      }
      const svg = d3.select(this.$el)
      const bubble = d3.pack(data)
        .size([this.width * 0.8, this.height * 0.8])
        .padding(-3)
      const nodes = d3.hierarchy(data)
        .sum(d => {
          return d.length
        })
      const vis = svg.selectAll('circle')
        .data(bubble(nodes).leaves())
      const textNodes = svg.selectAll('text')
        .data(bubble(nodes).leaves())

      const duration = 200
      let delay = 0

      // Init Bubbles

      vis.enter().append('circle')
        .on('mouseover', this.handleMouseOver)
        .on('mouseout', this.handleMouseOut)
        .on('click', this.handleClick)
        .attr('cx', d => {
          return (d.x + d.data.randomX) || 0
        })
        .attr('cy', d => {
          return (d.y + d.data.randomY) || 0
        })
        .transition()
        // .delay((d, i) => {
        //   return i * 70
        // })
        .attr('fill', '#E63C5B')
        .attr('r', d => {
          return d.r || 0
        })
        .attr('class', 'bubbles')

      // Init text

      textNodes.enter().append('text')
        .attr('transform', d => {
          return `translate(${d.x + d.data.randomX}, ${d.y + d.data.randomY})`
        })
        .style('text-anchor', 'middle')
        .text(d => {
          return d.data.name || ''
        })
        .attr('font-family', 'Roboto Mono')
        .attr('font-size', function (d) {
          return (d.r / 8) || 0
        })
        .attr('fill', '#fff')
        .attr('class', 'bubbleContent')

      // Update Bubbles

      vis.transition()
        .duration(duration)
        .delay((d, i) => {
          return i * 50
        })
        .attr('cx', d => {
          return (d.x + d.data.randomX) || 0
        })
        .attr('cy', d => {
          return (d.y + d.data.randomY) || 0
        })
        .attr('r', d => {
          return d.r || 0
        })

      // Update text

      textNodes.transition()
        .duration(duration)
        .delay((d, i) => {
          return i * 7
        })
        .attr('transform', d => {
          return `translate(${d.x + d.data.randomX}, ${d.y + d.data.randomY})`
        })
        .text(d => {
          return d.data.name || ''
        })
        .attr('font-size', function (d) {
          return d.r / 8 || 0
        })

      // Bubbles exit

      vis.exit()
        .transition()
        .duration(duration + delay)
        .style('opacity', 0)
        .remove()

      // Text exit

      textNodes.exit()
        .transition()
        .duration(duration + delay)
        .style('opacity', 0)
        .remove()
    },
    handleMouseOver (d, i) {
      const selectedBubble = d3.selectAll('.bubbles')
        .filter((data, ind) => { return ind === i })
      selectedBubble.style('fill', 'url(#flameGradient)')
    },
    handleMouseOut (d, i) {
      const selected = d3.selectAll('.bubbles')
        .filter((data, ind) => { return ind === i })
      selected.style('fill', '#E63C5B')
    },
    handleClick (d, i) {
      this.$store.commit('CHANGE_FILTERBY', d.data.name)
    },
    random (num) {
      return Math.floor(Math.random() * num) + num
    }
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped lang="scss">
  #bubblesContainer {
    position: fixed;
    top: 0;
    left: 10vw;
    /deep/ .bubbles {
     // cursor: pointer;
    }
    /deep/ .bubbleContent {
      pointer-events: none;
    }
  }

</style>
