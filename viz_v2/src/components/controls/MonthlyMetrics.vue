<template>
  <transition name="fade">
    <div v-if="toxLength" :class="['monthly-data', {'fadeOut': commentClicked}]">
      <div class="date-wrapper">
        {{monthName}} {{year}}
      </div>
      <div class="data-wrapper">
        <div class="increase">
          <span v-if="monthlyIncrease < 0">&darr;</span>
          <span v-if="monthlyIncrease > 0">&uarr;</span>
          {{Math.abs(monthlyIncrease)}}%
        </div>
        <div class="num">
          {{toxLength}}
        </div>
        <div class="type">
          <span class="circle"></span>
          <span>TOXIC</span>
        </div>
      </div>
      <div class="data-wrapper">
        <div class="num">
          {{detoxedLength}}
        </div>
        <div class="type">
          <span class="circle"></span>
          <span>DETOXED</span>
        </div>
      </div>
    </div>
  </transition>
</template>

<script>
import {
  mapState
} from 'vuex'

const monthNames = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEPT', 'OCT', 'NOV', 'DEC']

export default {
  name: 'MonthlyMetrics',
  computed: {
    ...mapState({
      month: state => state.SELECTED_MONTH,
      year: state => state.SELECTED_YEAR,
      toxLength: state => state.toxicLength,
      detoxedLength: state => state.detoxedLength,
      monthlyIncrease: state => state.monthlyIncrease,
      commentClicked: state => state.commentClicked
    }),
    monthName () {
      return monthNames[this.month - 1]
    }
  }
}
</script>

<style scoped lang="scss">
  .monthly-data {
    position: fixed;
    top: 3em;
    right: 3em;
    z-index: 1000;
    opacity: 1;
    transition: .2s opacity;
    &.fadeOut {
      opacity: 0;
    }
    .date-wrapper {
      color: $dark-text;
      font-weight: 600;
      margin-bottom: 14px;
    }
    .data-wrapper {
      margin-bottom: 14px;
      .increase {
        color: $red;
        font-size: 14px;
      }
      .num {
        font-size: 32px;
        line-height: 1.2;
        color: $darker-text;
        font-weight: 600;
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
        background: $red;
        margin-right: 15px;
        border: 1px solid $dark-text;
      }
      &:last-of-type {
        .circle {
          background: $white;
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
