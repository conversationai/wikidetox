<template>
    <transition name="fade">
        <div v-if="commentClicked" class="controls-wrapper">
            <div class="controls" v-ripple>
                <i class="material-icons" @click="next(-1)">keyboard_arrow_left</i>
                <i class="material-icons" @click="close()">close</i>
                <i class="material-icons" @click="next(1)">keyboard_arrow_right</i>
            </div>
        </div>
    </transition>
</template>

<script>

import { mapState } from 'vuex'

export default {
  name: 'CommentControls',
  computed: {
    ...mapState({
      commentClicked: state => state.commentClicked
    })
  },
  methods: {
    // next (num) {
    //   console.log('next')
    //   this.$store.commit('NEXT_COMMENT', num)
    // },
    close () {
      this.$store.commit('COMMENT_CLICK', false)
    }
  }
}
</script>

<style scoped lang="scss">
.controls-wrapper {
    position: fixed;
    width: 30vw;
    left: 50%;
    margin-left: -15vw;
    min-width: 400px;
    max-width: 90vw;
    bottom: 36px;
    height: 58px;
    z-index: 2000;
    .controls{
        position: relative;
        width: 100%;
        height: 58px;
        background-color: #fff;
        border-radius: 33px;
        color: $red;
        border: 1px solid $red;
        display: flex;
        justify-content: space-between;
        align-items: center;
        i {
            flex-grow: 1;
            cursor: pointer;
            padding: 8px 12px;
            &:nth-of-type(1) {
                text-align: left;
            }
            &:nth-of-type(2) {
                text-align: center;
            }
            &:nth-of-type(3) {
                text-align: right;
            }
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
