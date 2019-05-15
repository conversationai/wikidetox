<template>
  <div :class="['panel-wrapper', {'hidden': commentClicked || !navOpened}]">
    <!-- Title & Description -->
    <div>
      <img src="../../assets/logo.svg" />
      <p>
        Help our <a href="https://meta.wikimedia.org/wiki/Research:Detox" target="_blank"><span>community</span></a> improve the conversations behind Wikipedia. Find and edit comment <a href="https://perspectiveapi.com" target="_blank"><span>toxicity</span></a> on Wikipedia discussions.
      </p>
    </div>

    <!-- Month data -->
    <div>
      <MonthlyMetrics />
    </div>

    <!-- LIST OF METRICS -->
    <div>
      <h4>Toxicity filters</h4>
      <ul>
        <!-- ALL COMMENTS -->
        <li @click="sortClick('all')" v-ripple>
          <span :class="['root', { selected: filter === null}]">All</span>
        </li>

        <!-- TOP TRENDS -->
        <li :class="{ expanded: sort === 'trend'}"
            @click="sortClick('trend')" v-ripple>
          <span class="root"> Trending </span>
          <ul class="nested" :class="{'expand': sort === 'trend'}">
              <li v-for="(item, i) in trends" :key="`trend-${i}`"
                  :class="{selected: filter === item.cat }"
                  @click.stop.prevent="sortSubcategory(item.cat)"
                  >
                  <span>{{item.cat}}</span>
                  <span class="num">
                    {{item.count}}
                    <div class="circle"></div>
                  </span>
              </li>
          </ul>
        </li>

        <!-- PAGE CATEGORY -->
        <li :class="{ expanded: expanded === 'type'}"
            @click="sortClick('type')" v-ripple>
          <span class="root">Page Type</span>
          <ul class="nested" :class="{ expanded: sort === 'type'}">
              <li @click.stop.prevent="sortSubcategory('User page')"
                  :class="{selected: filter === 'User page' }">
                <span>User Page</span>
                <span class="num">
                  {{userpageLength}}
                  <div class="circle"></div>
                </span>
              </li>
              <li @click.stop.prevent="sortSubcategory('Talk page')"
                  :class="{selected: filter === 'Talk page' }" >
                <span>Talk Page</span>
                <span class="num">
                  {{talkpageLength}}
                  <div class="circle"></div>
                </span>
              </li>
          </ul>
        </li>

        <!-- TOXICITY TYPES -->
        <li :class="{ expanded: sort === 'model' }"
            @click="sortClick('model')" v-ripple>
          <span class="root">Toxicity Subtype</span>
          <ul class="nested" :class="{ expanded: sort === 'model'}">
              <li v-for="(item, i) in models" :key="`model-${i}`"
                  @click.stop.prevent="sortSubcategory(item.model)"
                  :class="{selected: filter === item.model }" >
                <span>{{item.name}}</span>
                <span class="num">
                  {{item.length}}
                  <div class="circle"></div>
                </span>
              </li>
          </ul>
        </li>
      </ul>
    </div>

    <!-- <a href="https://jigsaw.google.com" target="_blank">
      <img src="../../assets/jigsaw-logo.svg" />
    </a> -->
  </div>
</template>

<script>
import { mapState, mapGetters } from 'vuex'
import MonthlyMetrics from './MonthlyMetrics.vue'
export default {
  name: 'MetricsPanel',
  components: {
    MonthlyMetrics
  },
  data () {
    return {
      expanded: '',
      navOpened: false
    }
  },
  computed: {
    ...mapState({
      sort: state => state.sortby,
      filter: state => state.filterby,
      commentClicked: state => state.commentClicked
    }),
    ...mapGetters({
      talkpageLength: 'getTalkpageLength',
      userpageLength: 'getUserpageLength',
      models: 'getModelsLengths',
      trends: 'getPageTrend',
      dataTime: 'getDataTimeRange'
    })
  },
  watch: {
    dataTime () {
      this.$store.commit('CHANGE_SORTBY', 'all')
      this.$store.commit('CHANGE_FILTERBY', null)
    }
  },
  mounted () {
    this.resize()
    window.addEventListener('resize', this.resize)
  },
  beforeDestroy () {
    window.removeEventListener('resize', this.resize)
  },
  methods: {
    resize () {
      const breakPoint = 768
      if (window.innerWidth > breakPoint) {
        this.navOpened = true
      }
    },
    sortClick (sortby) {
      this.$store.commit('CHANGE_SORTBY', sortby)
      if (sortby === 'all') {
        this.$store.commit('CHANGE_FILTERBY', null)
      } else {
        this.expanded = sortby
      }
    },
    sortSubcategory (selected) {
      this.$store.commit('CHANGE_FILTERBY', selected)
    },
    openNav (ifOpen) {
      this.navOpened = ifOpen
    }
  }
}
</script>

<style scoped lang="scss">
  .panel-wrapper{
    width: $panel-width;
    min-width: $panel-width;
    height: 100vh;
    z-index: 2000;
    margin-left: 0;
    color: $dark-text;
    background-color: #fff;
    transition: .2s margin-left;
    overflow: scroll;
    @include box-shadow;

    @include tablet {
      -webkit-box-shadow: 0px 0px 42px 4px rgba(0,0,0,0.2);
      -moz-box-shadow: 0px 0px 42px 4px rgba(0,0,0,0.2);
      box-shadow: 0px 0px 42px 4px rgba(0,0,0,0.2);
      position: fixed;
    }

    &.hidden {
      margin-left: calc(-#{$panel-width});
      box-shadow: none;
    }
    &>div {
      p {
        color: $light-text;

        @include tablet {
          font-size: 12px;
        }
      }
      &:first-of-type {
        padding: 22px 16px;
        font-family: $merriweather;
        border-bottom: 1px solid $light-border;

        a {
          color: #000;
          text-decoration: none;
        }

        img {
          margin-bottom: 34px;

          @include tablet {
            margin-bottom: 12px;
          }
        }
      }
      &:nth-of-type(2) {
        padding: 16px;
        border-bottom: 1px solid $light-border;
      }
      &:nth-of-type(3) {
        h4 {
          padding: 4px 16px 0;
          font-size: 10px;
          font-weight: 600;
          text-transform: uppercase;
          font-family: $libre;
        }
      }
    }

    &>a img{ // jigsaw logo
      padding: 58px 16px 16px;
      width: 119px;
      height: autp;

      @include tablet {
        padding: 28px 16px 16px;
        width: 99px;
      }
    }
    /* LIST OF METRICS */
    ul {
      padding: 0;
      margin: 0;
      font-size: 16px;
      font-family: $merriweather;
      overflow-y: scroll;

      @include tablet {
        font-size: 13px;
      }

      li {
        list-style-type: none;
        padding: 0;
        transition: .2s all;
        cursor: pointer;
        font-weight: 400;
        width: 100%;
        position: relative;
        display: inline-block;
        span {
          padding: 14px 12px 14px 16px;
          display: inline-block;
        }
        .root {
          width: 100%;
          border-left: 3px solid transparent;
          &.selected {
            color: $red;
            border-left: 3px solid $red;
          }
        }
        .nested {
          max-height: 0;
          overflow: hidden;
          opacity: 0;
          transition: all .2s;
          will-change: opacity, max-height;
          li {
            display: flex;
            justify-content: space-between;
            border-left: 3px solid transparent;
            padding-left: 12px;
            .num {
              color: $red;
              opacity: .4;
              .circle {
                display: inline-block;
                width: 8px;
                height: 8px;
                margin: 0 4px;
                border-radius: 50%;
                background-color: $red;
              }
            }
            &.selected {
              color: $red;
              border-left: 3px solid $red;
              .num {
                opacity: 1;
              }
            }
          }
        }
        &.expanded {
          background: $lighter-bg;
          padding-bottom: 0;
          .nested {
            max-height: 650px;
            opacity: 1;
          }
        }
      }
    }
  }
</style>
