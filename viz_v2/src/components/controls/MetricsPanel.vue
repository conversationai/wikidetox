<template>
  <div class="panel-wrapper">
    <!-- Title & Description -->
    <div>
      <h1>Wiki<span>Detox</span></h1>
      <p>
        There’s a discussion behind every page on Wikipedia. Sometimes the conversation becomes toxic.
        Find and edit toxic comments, improve the health of Wikipedia.
      </p>
    </div>

    <!-- LIST OF METRICS -->
    <div>
      <ul>
        <li @click="sortClick('all')" v-ripple>
          <span :class="['root', { selected: selected === 'all' }]">All Comments</span>
        </li>
        <li :class="{ expanded: sort === 'trend', selected: selected === 'trend' }"
            @click="sortClick('trend')" v-ripple>
          <span :class="['root', {selected: selected === 'trend' }]"> Top Trends </span>

          <ul class="nested" :class="{'expand': sort === 'trend'}">
              <li v-for="(item, i) in trends" :key="`trend-${i}`"
                  :class="{selected: selected === item.category }"
                  @click.stop.prevent="sortSubcategory(item.category)"
                  >
                  <span>{{item.category}}</span>
                  <span class="num">{{item.length}}</span>
              </li>
          </ul>
        </li>
        <li :class="{ expanded: sort === 'type'}"
            @click="sortClick('type')" v-ripple>
          <span :class="['root', {selected: selected === 'type' }]">Page Category</span>

          <ul class="nested" :class="{ expanded: sort === 'type'}">
              <li @click.stop.prevent="sortSubcategory('talk_page')"
                  :class="{selected: selected === 'talk_page' }" >
                <span>Talk Page</span>
                <span class="num">{{talkpageLength}}</span>
              </li>
              <li @click.stop.prevent="sortSubcategory('user_page')"
                  :class="{selected: selected === 'user_page' }">
                <span>User Page</span>
                <span class="num">{{userpageLength}}</span>
              </li>
          </ul>
          </transition>
        </li>
        <li :class="{ expanded: sort === 'model'}"
            @click="sortClick('model')" v-ripple>
          <span :class="['root', {selected: selected === 'model' }]">Toxicity Types</span>

          <ul class="nested" :class="{ expanded: sort === 'model'}">
              <li v-for="(item, i) in models" :key="`model-${i}`"
                  @click.stop.prevent="sortSubcategory(item.name)"
                  :class="{selected: selected === item.name }" >
                <span>{{item.name}}</span>
                <span class="num">{{item.length}}</span>
              </li>
          </ul>
          </transition>
        </li>
      </ul>
    </div>
  </div>
</template>

<script>

import { mapState, mapGetters } from 'vuex'

export default {
  name: 'MetricsPanel',
  computed: {
    ...mapState({
      trends: state => state.pageTrends,
      sort: state => state.sort,
      selected: state => state.display
    }),
    ...mapGetters({
      talkpageLength: 'getTalkpageLength',
      userpageLength: 'getUserpageLength',
      models: 'getModelsLengths'
    })
  },
  methods: {
    sortClick (sortby) {
      this.$store.commit('CHANGE_SORTBY', sortby)
      this.sortSubcategory(sortby)
    },
    sortSubcategory (selected) {
      this.$store.commit('CHANGE_DISPLAY', selected)
    }
  }
}
</script>

<style scoped lang="scss">
  .panel-wrapper{
    position: fixed;
    top: 2em;
    left: 2em;
    width: 262px;
    height: auto;
    z-index: 100;
    color: $dark-text;
    @include box-shadow;

    &>div {
      background-color: $white;
      p {
        color: $light-text;
      }
      &:nth-of-type(1) {
        padding: 22px;
        background-color: $red;
        font-size: 12px;
        p {
          color: $white;
        }
      }
      &:nth-of-type(2) {
        text-transform: uppercase;
        font-size: 14px;
        p {
          color: $light-text;
        }
      }
    }

    h1 {
      margin-bottom: 48px;
      font-size: 18px;
      font-weight: 400;
      span {
        color: $red;
      }
    }

    ul {
      padding: 0;
      margin: 0;
      font-size: 14px;
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
          padding: 18px 12px 18px 20px;
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
            &.selected {
              color: $red;
              border-left: 3px solid $red;
            }
          }
        }
        &:hover {
          font-weight: 600;
        }
        &.expanded {
          background: $lighter-bg;
          font-weight: 600;
          padding-bottom: 0;
          .nested {
            max-height: 650px;
            opacity: 1;
          }
        }
      }
    }

    .metrics {
      display: flex;
      justify-content: space-between;
      margin: 20px auto;
      .tox-num {
        color: $red;
      }
    }
  }
  // .expand-enter-active, .expand-leave-active {
  //   transition: all .5s;
  //   max-height: 650px;
  // }
  // .expand-enter, .expand-leave-to /* .fade-leave-active below version 2.1.8 */ {
  //   opacity: 0;
  //   max-height: 0;
  // }
</style>
