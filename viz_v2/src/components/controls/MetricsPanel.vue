<template>
  <div class="panel-wrapper">
    <div>
      <h1>Wiki<span>Detox</span></h1>
      <!-- <p>
        There’s a discussion behind every page on Wikipedia. Sometimes the conversation becomes toxic.
      </p>
      <p>
        Find and edit toxic comments, improve the health of Wikipedia.
      </p> -->
    </div>
    <div>
      <ul>
        <li :class="{ selected: sort === 'all' }"
            @click="sortClick('all')">
          All Comments
          <transition name="fade">
            <ul class="nested" v-if="sort === 'all'">
              <li>
                <span>Toxic</span>
                <span class="num">{{toxLength}}</span>
              </li>
              <li>
                <span>Detoxed</span>
                <span class="num">{{detoxedLength}}</span>
              </li>
            </ul>
          </transition>
        </li>
        <li :class="{ selected: sort === 'trend' }"
            @click="sortClick('trend')">
          Top Trends
          <transition name="fade">
            <ul class="nested"  v-if="sort === 'trend'">
              <li v-for="(item, i) in trends" :key="`trend-${i}`">
                <span>{{item.category}}</span>
                <span class="num">{{item.length}}</span>
              </li>
            </ul>
          </transition>
        </li>
        <li :class="{ selected: sort === 'type' }"
            @click="sortClick('type')">
          Page Category
          <transition name="fade">
            <ul class="nested" v-if="sort === 'type'">
              <li>
                <span>Talk Page</span>
                <span class="num">{{talkpageLength}}</span>
              </li>
              <li>
                <span>User Page</span>
                <span class="num">{{userpageLength}}</span>
              </li>
            </ul>
          </transition>
        </li>
        <li :class="{ selected: sort === 'model' }"
            @click="sortClick('model')">
          Toxicity Types
          <transition name="fade">
            <ul class="nested" v-if="sort === 'model'">
              <li v-for="(item, i) in models" :key="`model-${i}`">
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
      sort: state => state.sort
    }),
    ...mapGetters({
      dataLength: 'getDatalength',
      detoxedLength: 'getDeletedLength',
      talkpageLength: 'getTalkpageLength',
      userpageLength: 'getUserpageLength',
      models: 'getModelsLengths'
    }),
    toxLength () {
      return this.dataLength - this.detoxedLength
    }
  },
  methods: {
    sortClick (sortby) {
      this.$store.commit('CHANGE_SORTBY', sortby)
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
    z-index: 10;
    color: $dark-text;

    &>div {
      background-color: $white;
      @include box-shadow;
      margin-bottom: 8px;
      p {
        color: $light-text;
      }
      &:nth-of-type(1) {
        padding: 10px 20px;
        p {
          color: $light-text;
        }
      }
      &:nth-of-type(2) {
        padding: 6px 0;
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
      font-size: 14px;
      li {
        list-style-type: none;
        padding: 12px 12px 12px 18px;
        transition: .2s all;
        cursor: pointer;
        border-left: 3px solid transparent;
        font-weight: 400;
        .nested {
          margin-top: 12px;
          li {
            display: flex;
            justify-content: space-between;
            &:last-of-type {
              padding: 12px 12px 0 18px;
            }
          }
        }
        &:hover {
          font-weight: 600;
        }
        &.selected {
          border-left: 3px solid $red;
          background: $lighter-bg;
          font-weight: 600;
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
  .fade-enter-active, .fade-leave-active {
    transition: all .5s;
    max-height: 650px;
  }
  .fade-enter, .fade-leave-to /* .fade-leave-active below version 2.1.8 */ {
    opacity: 0;
    max-height: 0;
  }
</style>
