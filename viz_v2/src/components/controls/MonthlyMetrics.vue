<template>
  <transition name="fade">
    <div v-if="toxLength" :class="['monthly-data', {'fadeOut': commentClicked}]">
      <h3>
        {{monthName}}, {{year}}
      </h3>
      <div class="increase">
        <span v-if="monthlyIncrease < 100 && monthlyIncrease > -100">({{Math.abs(monthlyIncrease)}}%)</span>
        &ensp;
        <span v-if="monthlyIncrease < 0 && monthlyIncrease > -100">&darr;</span>
        <span v-if="monthlyIncrease > 0 && monthlyIncrease < 100">&uarr;</span>
      </div>

      <div class="data-wrapper">
        <div>
          <h4 class="toxic">
            {{toxLength}}
          </h4>
          <div class="type">
            <span class="circle"></span>
            <span>TOXIC</span>
          </div>
        </div>
        <div>
          <h4>
            {{detoxedLength}}
          </h4>
          <div class="type">
            <span class="circle detoxed"></span>
            <span>DETOXED</span>
          </div>
        </div>
      </div>

    </div>
  </transition>
</template>

<script>
import {
  mapState,
  mapGetters
} from 'vuex'

const monthNames = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']

export default {
  name: 'MonthlyMetrics',
  computed: {
    ...mapState({
      month: state => state.SELECTED_MONTH,
      year: state => state.SELECTED_YEAR,
      monthlyIncrease: state => state.monthlyIncrease,
      commentClicked: state => state.commentClicked
    }),
    ...mapGetters({
      toxLength: 'getToxLength',
      detoxedLength: 'getDetoxLength'
    }),
    monthName () {
      return monthNames[this.month - 1]
    },
    detoxedLength () {
      return this.$store.getters.dataLength - this.toxLength
    }
  }
}
</script>

<style scoped lang="scss">
  .monthly-data {
    opacity: 1;
    transition: .2s opacity;

    &.fadeOut {
      opacity: 0;
    }

    h3 {
      color: #000;
      font-size: 18px;
      margin: 0 0 34px 0;

      @include tablet {
        font-size: 14px;
        margin: 0 0 24px 0;
      }
    }
    .increase {
      color: $red;
      font-size: 10px;
    }

    .data-wrapper {
      display: flex;
      justify-content: space-between;
      align-items: flex-end;

      &>div {
        padding-right: 20px;

        h4 {
          font-size: 30px;
          line-height: 1.2;
          color: $darker-text;
          margin-top: 0;
          margin-bottom: 14px;

          @include tablet {
            font-size: 24px;
          }

          &.toxic {
            color: $red;
          }
        }

        .type {
          font-size: 12px;
          color: $light-text;
        }

        .circle {
          display: inline-block;
          width: 10px;
          height: 10px;
          border-radius: 50%;
          background-color: $red;
          margin-right: 15px;

          &.detoxed {
            background-color: $light-red;
          }
        }
      }

    }
  }

  .fade-enter-active,
  .fade-leave-active {
    transition: opacity .5s;
    opacity: 1;
  }

  .fade-enter,
  .fade-leave-to
  /* .fade-leave-active below version 2.1.8 */
  {
    opacity: 0;
  }
</style>
