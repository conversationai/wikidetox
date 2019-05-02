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
          <span v-if="showFullScreen" class="btn-wrapper">
            <div class="btn" v-if="feedbackSent === ''" @click="sendFeedbacks()" v-ripple>Not toxic</div>
            <div class="feedbacks" v-if="feedbackSent === 'success'">Thanks for your feedback :)</div>
            <div class="feedbacks" v-if="feedbackSent === 'failed'">Oops! Something went wrong :(</div>
            <div class="btn action " v-if="!detoxed" v-ripple>Detox comment</div>
          </span>
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
      transparent: false,
      feedbackSent: ''
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
        this.feedbackSent = ''
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
    },
    sendFeedbacks () {
      const params = { comment: this.comment }
      return fetch('suggest_score', {
        method: 'POST',
        mode: 'cors',
        cache: 'no-cache',
        credentials: 'same-origin',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(params)
      }).then(res => {
        if (res.ok) {
          this.feedbackSent = 'success'
        } else {
          this.feedbackSent = 'failed'
          throw Error(`Request rejected with status ${res.status}`)
        }
      })
        .catch(error => console.error(error))
    }
  }
}
</script>

<style scoped lang="scss">
  $max-fullscreen-w: 596px;

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

    @include tablet {
      border-radius: 0;
    }

    &.detoxed {
      color: $red;
      background: radial-gradient($light-red, transparent);

      &.fullScreen {
        .score-wrapper {
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

      @include tablet {
        font-size: 12px;
      }
    }

    .score-wrapper {
      display: flex;
      justify-content: center;
      align-items: center;
      max-width: $max-fullscreen-w;
      width: 100%;

      .btn-wrapper {
        display: flex;
        align-items: center;

        @include tablet {
          margin-top: 20px;
        }
      }

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

      @include tablet {
        width: 100vw !important;
        height: 100vh !important;
      }

      .title {
        width: 78%;
        max-width: $max-fullscreen-w;

        @include tablet {
          width: 90%;
        }

        h4 {
          font-size: 28px;
          margin-top: 18px;

          @include tablet {
            font-size: 22px;
          }
        }
      }

      .score-wrapper {
        justify-content: space-between;
        border-top: 1px solid #fff;
        padding: 14px 0 0 0;

        @include tablet {
          width: 100vw;
          padding: 14px 20px;
          max-width: $max-fullscreen-w;
          flex-direction: column;
        }

        h4 {
          font-size: 20px;
          flex-grow: 1;

          @include tablet {
            font-size: 14px;
          }
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

            @include tablet {
              padding: 10px 18px;
            }

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
        max-width: $max-fullscreen-w;
        max-height: 24vh;
        padding: 0 0 3.6em;
        margin: 3em 0 0 0;
        text-align: left;

        @include tablet {
          font-size: 14px;
        }

        @include tablet {
          height: 50vh;
          padding: 0 20px 2.6em;
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
