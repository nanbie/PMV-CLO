<script setup>
import { ref, onMounted, watch } from 'vue'
import { use } from 'echarts/core'
import { SVGRenderer } from 'echarts/renderers'
import { LineChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  GridComponent,
  LegendComponent,
  ToolboxComponent
} from 'echarts/components'
import VChart from 'vue-echarts'
import axios from 'axios'

use([
  SVGRenderer,
  LineChart,
  TitleComponent,
  TooltipComponent,
  GridComponent,
  LegendComponent,
  ToolboxComponent
])

const API_URL = 'http://localhost:8000/api'
const loading = ref(false)
const optionCombined = ref({})
const props = defineProps({
  startDate: String,
  endDate: String,
  city: String,
  devIds: Array,
  cloStrategy: String,
  manualClo: Number,
  metabolicRate: Number
})

const emit = defineEmits(['update:dates'])

const localStartDate = ref(props.startDate)
const localEndDate = ref(props.endDate)

const fetchData = async () => {
  loading.value = true
  try {
    const params = {
      start_date: localStartDate.value,
      end_date: localEndDate.value,
      city: props.city,
      dev_ids: props.devIds,
      clo_strategy: props.cloStrategy,
      manual_clo: props.manualClo,
      metabolic_rate: props.metabolicRate
    }

    const response = await axios.get(`${API_URL}/daily-trend`, { params })
    const data = response.data.data || []
    const days = data.map(item => item.day)
    const temps = data.map(item => item.avg_temp)
    const rhs = data.map(item => item.avg_rh)
    const pmvs = data.map(item => item.pmv)
    const clos = data.map(item => item.clo)

    optionCombined.value = {
      title: {
        text: '每日平均 环境指标与舒适度 趋势',
        left: 'center',
        top: 10
      },
      toolbox: {
        feature: {
          saveAsImage: {
            type: 'svg',
            title: '导出 SVG',
            name: 'PMV_Daily_Trend'
          }
        },
        right: 20,
        top: 10
      },
      tooltip: {
        trigger: 'axis'
      },
      legend: {
        top: 40,
        data: ['温度', '湿度']
      },
      grid: {
        left: '6%',
        right: '6%',
        bottom: '10%',
        top: 80
      },
      xAxis: {
        type: 'category',
        data: days
      },
      yAxis: [
        {
          type: 'value',
          name: '环境指标',
          position: 'left',
          axisLabel: { formatter: '{value}' }
        }
      ],
      series: [
        {
          name: '温度',
          type: 'line',
          data: temps,
          smooth: true,
          lineStyle: { color: '#ee6666' },
          itemStyle: { color: '#ee6666' }
        },
        {
          name: '湿度',
          type: 'line',
          data: rhs,
          smooth: true,
          lineStyle: { color: '#5470c6' },
          itemStyle: { color: '#5470c6' }
        }
      ]
    }
  } catch (err) {
    console.error('Failed to fetch daily trend:', err)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchData()
})

// Watch for prop changes from parent
watch(() => [props.startDate, props.endDate, props.city, props.devIds, props.cloStrategy, props.manualClo, props.metabolicRate], () => {
  localStartDate.value = props.startDate
  localEndDate.value = props.endDate
  fetchData()
})

// Emit changes when local inputs change
watch(() => [localStartDate.value, localEndDate.value], ([newStart, newEnd]) => {
  emit('update:dates', { startDate: newStart, endDate: newEnd })
})
</script>

<template>
  <div class="trend-container">
    <div class="toolbar">
      <div class="toolbar-field">
        <span>开始</span>
        <input type="date" v-model="localStartDate" />
      </div>
      <div class="toolbar-field">
        <span>结束</span>
        <input type="date" v-model="localEndDate" />
      </div>
    </div>
    <div class="chart-wrapper">
      <v-chart class="chart" :option="optionCombined" autoresize :init-options="{ renderer: 'svg' }" />
    </div>
    <div v-if="loading" class="loading-overlay">加载中...</div>
  </div>
</template>

<style scoped>
.trend-container {
  width: 100%;
  background: #ffffff;
  padding: 16px 20px 24px;
  border-radius: 8px;
  box-shadow: 0 2px 5px rgba(0,0,0,0.08);
  position: relative;
  margin-bottom: 20px;
}

.toolbar {
  position: absolute;
  top: 10px;
  right: 16px;
  display: flex;
  gap: 8px;
  font-size: 0.8rem;
  color: #555;
  align-items: center;
  z-index: 10;
}

.toolbar-field {
  display: flex;
  align-items: center;
  gap: 4px;
}

.toolbar-field input {
  padding: 2px 4px;
  border-radius: 4px;
  border: 1px solid #ccc;
  font-size: 0.8rem;
}

.chart-wrapper {
  height: 300px;
  width: 100%;
}

.chart {
  height: 100%;
  width: 100%;
}

.loading-overlay {
  position: absolute;
  inset: 0;
  background: rgba(255,255,255,0.7);
  display: flex;
  justify-content: center;
  align-items: center;
  font-weight: bold;
  color: #333;
  z-index: 100;
}
</style>
