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
    next (d) {
      this.$root.$emit('next', d)
      this.$store.commit('COMMENT_CLICK', true)
    },
    close () {
      this.$store.commit('COMMENT_CLICK', false)
    }
  }
}
</script>

<style scoped lang="scss">
.controls-wrapper {
    position: fixed;
    width: 100vw;
    left: 0;
    bottom: 0;
    height: 66px;
    z-index: 2000;

    .controls{
        position: relative;
        width: 100%;
        height: 100%;
        background-color: #fff;
        color: $red;
        display: flex;
        justify-content: center;
        align-items: center;

        i {
            cursor: pointer;
            padding: 28px;

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
