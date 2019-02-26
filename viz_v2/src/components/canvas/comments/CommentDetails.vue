<template>
  <transition name="fade">
    <div v-if = "ifVisible"
      :class = "['detail-circle-wrapper', {'fullScreen': commentClicked, 'white': detoxed}]"
      :style = "{ top: circleTop + 'px', left: circleLeft + 'px' }"
      @mouseup = "commentClick()"
      id="commentCircle"
      >
      <div class="content">
        <h4>
          {{pageType}}:<br>
          {{pageTitle}}
        </h4>
        <p v-if="commentClicked">{{date}}</p>
        <p class="comment">
          {{comment}}
        </p>
        <p v-if="commentClicked">TOXICITY SCORE</p>
        <div v-if="commentClicked" class="score-wrapper">
          <div class="score">
            {{score}}%
          </div>
          <div class="btn" v-ripple>change score</div>
          <div class="btn" v-ripple>view edit</div>
        </div>
      </div>
    </div>
  </transition>
</template>

<script>

import { mapState } from 'vuex'

export default {
  name: 'CommentDetails',
  data () {
    return {
      pageType: '',
      pageTitle: '',
      comment: '',
      score: '',
      date: '',
      detoxed: false,
      circleTop: 0,
      circleLeft: 0,
      scrolled: false
    }
  },
  computed: {
    ...mapState({
      commentData: state => state.selectedComment,
      commentClicked: state => state.commentClicked,
      clickedIndex: state => state.clickedIndex
    }),
    ifVisible () {
      if (this.commentClicked) return true
      return this.commentData !== null
    }
  },
  watch: {
    commentData (newVal, oldVal) {
      if (newVal !== null && !this.commentClicked) {
        const d = newVal.comment
        this.commentIndex = newVal.index

        this.pageType = d.page_title.startsWith('User') ? 'User page' : 'Talk page'
        this.pageTitle = d.page_title.split(':')[1]
        this.comment = d.content
        this.detoxed = d.type === 'DELETION'

        this.score = parseFloat(d['Toxicity']).toFixed(2) * 100
        const day = new Date(parseFloat(d.timestamp) * 1000)
        this.date = day.toLocaleString()
      }
    }
  },
  mounted () {
    this.circleTop = window.innerHeight / 2
    this.circleLeft = window.innerWidth / 2
    window.addEventListener('mousemove', this.onMouseMove, false)
  },
  beforeDestroy () {
    window.removeEventListener('mousemove', this.onMouseMove)
  },
  methods: {
    onMouseMove ($ev) {
      if (this.commentData !== null && !this.commentClicked) {
        this.circleTop = $ev.clientY - (234 / 2)
        this.circleLeft = $ev.clientX - (234 / 2)
      }
    },
    commentClick () {
      if (!this.commentClicked) {
        this.$store.commit('COMMENT_CLICK', {
          bool: true,
          index: this.commentIndex
        })
      }
    }
  }
}
</script>

<style scoped lang="scss">
  .detail-circle-wrapper {
    position: fixed;
    z-index: 2000;
    width: 234px;
    height: 234px;
    border-radius: 50%;
    background-color: tranparent;
    color: #fff;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: .4s all;
    overflow: hidden;
    cursor: pointer;
    // @include box-shadow;

    &.white {
      background-color: tranparent;
      color: $darker-text;
      .score-wrapper {
        border-top: 1px solid $red !important;
      }
    }
    .content {
      max-width: 180px;
      h4 {
        font-size: 14px;
        margin-bottom: 0;
      }
      .comment {
        font-size: 11px;
        max-width: 100%;
        overflow: hidden;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
      }
    }
    &.fullScreen {
      width: 120vh;
      height: 120vh;
      top: 50% !important;
      left: 50% !important;
      margin-right: -50%;
      transform: translate(-50%, -50%);
      align-items: center;
      text-align: left;
      cursor: auto;

      .content {
        width: 78%;
        max-width: 646px;
        padding-bottom: 8em;
        h4 {
          font-size: 24px;
          max-width: 646px;
        }
        .comment {
          font-size: 15px;
          white-space: normal;
          overflow-y: scroll;
          max-width: 646px;
          max-height: 24vh;
          padding: 1.6em 0 2em 0;
        }
        .score-wrapper {
          display: flex;
          justify-content: space-between;
          align-items: center;
          border-top: 1px solid #fff;
          padding-top: 14px;
          .score {
            font-size: 24px;
            flex-grow: 1;
          }
          .btn {
            text-transform: uppercase;
            font-size: 15px;
            margin-left: 20px;
            margin-right: -20px;
            padding: 20px;
            cursor: pointer;
          }
        }
      }
    }
  }

.controls {
  position: fixed;
  width: 100vw;
  height: 100px;
  bottom: 100px;
  left: 0;
  background-color: #fff;
  display: flex;
  cursor: pointer;
  color: $red;
  .material-icons {
    &:nth-of-type() {
      flex-grow: 1;
    }
  }
}

.fade-enter-active,
  .fade-leave-active {
    transition: opacity .4s;
    opacity: 1;
  }

  .fade-enter,
  .fade-leave-to
  /* .fade-leave-active below version 2.1.8 */
  {
    opacity: 0;
  }
</style>
