<template>
  <transition name="fade" v-if="ifVisible">
    <div 
      :class = "['detail-circle-wrapper', {'transparent': transparent, 'fullScreen': showFullScreen, 'detoxed': detoxed}]"
      :style = "{ top: circleTop + 'px', left: circleLeft + 'px', width: size + 'px', height: size + 'px' }"
      @mouseup = "commentClick()"
      id="commentCircle"
      >
      <div class="title">
        <p>{{pageType}}</p>
        <h4>
          {{pageTitle}}
        </h4>
        <p v-if="showFullScreen">{{date}}</p>
      </div>
      <p class="comment">
        {{comment}}
      </p>
        <div class="score-wrapper">
          <h4 v-if="!detoxed">
            {{score}}% <span v-if="showFullScreen">Toxicity Score</span>
          </h4>
          <h4 v-if="detoxed">
            Detoxed
          </h4>
          <div class="btn" v-if="showFullScreen" v-ripple>Not toxic</div>
          <div class="btn action " v-if="showFullScreen && !detoxed" v-ripple>Detox comment</div>
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
      size: 0,
      showFullScreen: false,
      transparent: false
    }
  },
  computed: {
    ...mapState({
      commentData: state => state.selectedComment,
      commentClicked: state => state.commentClicked
    }),
    ifVisible () {
      if (this.commentClicked) return true
      return this.commentData !== null
    }
  },
  watch: {
    commentData (newVal, oldVal) {
      if (newVal !== null) {
        const d = newVal.comment

        this.pageType = d.page_title.startsWith('User') ? 'User page' : 'Talk page'
        this.pageTitle = d.page_title.split(':')[1]
        this.comment = d.cleaned_content
        this.detoxed = d.type === 'DELETION'
        this.score = parseFloat(d['RockV6_1_TOXICITY']).toFixed(2) * 100
        this.date = (new Date(d.unix)).toLocaleString()

        // this.size = newVal.size * 3.6
        this.size = 266

        this.circleTop = newVal.pos.y - this.size / 2
        this.circleLeft = newVal.pos.x - this.size / 2 + 262 // 262 = left panel size
      }
    },
    commentClicked (clicked, oldVal) {
      if (clicked) {
        this.transparent = true
        setTimeout(() => {
          this.showFullScreen = true
        }, 400)
      } else {
        this.showFullScreen = false
        this.transparent = false
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
    commentClick () {
      this.transparent = true
      if (!this.commentClicked) {
        this.$store.commit('COMMENT_CLICK', true)
      }
    }
  }
}
</script>

<style scoped lang="scss">
  .detail-circle-wrapper {
    position: fixed;
    z-index: 2000;
    border-radius: 50%;
    color: #fff;
    background: rgb(255,60,91);
    background: radial-gradient(rgb(255,60,91), transparent);
    transition: height .3s ease, width .3s ease, opacity 0.1s ease;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    overflow: hidden;
    cursor: pointer;

    &.detoxed {
      color: $red;
      background: radial-gradient($light-red, transparent);

      &.fullScreen {
        .score-wrapper {
          width: 100%;
          border-top: 1px solid $red;
          .btn {
            color: $red;
            border: 1px solid $red !important;
            &.action {
              background-color: $red !important;
              color: #fff !important;
            }
          }
        }
      }
    }

    &.transparent {
      background: none !important;
    }

    .title {
      text-align: center;
      max-width: 180px;
      margin: 0 auto;
      p {
        padding: 0;
        margin: 0;
      }
      h4 {
        font-size: 14px;
        margin: 0;
      }
    }
    
    .comment {
      font-size: 14px;
      max-width: 180px;
      overflow: hidden;
      display: -webkit-box;
      -webkit-line-clamp: 3;
      -webkit-box-orient: vertical;
      text-overflow: ellipsis;
      text-align: center;
    }

    .score-wrapper {
      display: flex;
      justify-content: center;
      align-items: center;
        h4 {
          font-size: 14px;
          margin: 0;
        }
    }

    &.fullScreen {
      width: 120vh !important;
      height: 120vh !important;
      top: 50% !important;
      left: 50% !important;
      margin-right: -50%;
      transform: translate(-50%, -50%);
      align-items: center;
      text-align: left;
      cursor: auto;

      &>div {
        width: 78%;
        max-width: 646px;
      }

      .title {
        h4 {
          font-size: 28px;
          margin-top: 18px;
        }
      }

      .score-wrapper {
        justify-content: space-between;
        border-top: 1px solid #fff;
        padding-top: 14px;
        h4 {
          font-size: 20px;
          flex-grow: 1;
        }
        .btn {
            text-transform: uppercase;
            font-size: 12px;
            padding: 10px 18px;
            border-radius: 20px;
            margin-left: 18px;
            border: 1px solid #fff;
            cursor: pointer;
            background-color: transparent;

            &.action {
              background-color: #fff;
              color: $red;
            }
        }
      }

      .comment {
        font-size: 20px;
        white-space: normal;
        overflow-y: scroll;
        max-width: 646px;
        max-height: 24vh;
        padding: 3em 0 2.6em;
        margin: 0;
        text-align: left;
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
    transition: opacity .2s;
    opacity: 1;
  }

  .fade-enter,
  .fade-leave-to
  /* .fade-leave-active below version 2.1.8 */
  {
    opacity: 0;
  }
</style>
