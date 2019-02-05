<template>
  <svg id="bubblesContainer" :width="width" :height="height">
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
      randomizeScale: 18 // smaller number = more position randomization
    }
  },
  computed: {
    ...mapState({
      sortby: state => state.sort,
      month: state => state.SELECTED_MONTH,
      trends: state => state.pageTrends
    }),
    ...mapGetters({
      talkpageLength: 'getTalkpageLength',
      userpageLength: 'getUserpageLength',
      models: 'getModelsLengths'
    }),
    bubbleData (sortby, month) {
      switch (this.sortby) {
        case 'trend':
          return this.trends.map(t => {
            return {
              name: t.category,
              length: parseInt(t.length),
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
  },
  watch: {
    bubbleData (newVal, oldVal) {
      if (newVal.length > 0) {
        this.drawBubbles()
      } else {
        // Go back to all comments
        // TODO: tell particle system to show
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
      this.width = window.innerWidth - 244
      this.height = window.innerHeight - 76
      if (this.bubbleData.length > 0) {
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

      // Updates

      vis.transition()
        .duration(duration)
        .delay((d, i) => {
          return i * 7
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

      // Init

      vis.enter().append('circle')
        .attr('cx', this.width / 2)
        .attr('cy', this.height / 2)
        .transition()
        .attr('cx', d => {
          return (d.x + d.data.randomX) || 0
        })
        .attr('cy', d => {
          return (d.y + d.data.randomY) || 0
        })
        .attr('r', d => {
          return d.r || 0
        })
        .style('opacity', 1)
        .style('fill', '#E63C5B')

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

      vis.exit()
        .transition()
        .duration(duration + delay)
        .style('opacity', 0)
        .remove()

      textNodes.exit()
        .transition()
        .duration(duration + delay)
        .style('opacity', 0)
        .remove()
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
    left: 244px;
    z-index: 100;
    /deep/ circle {
      cursor: pointer;
    }
  }

</style>
