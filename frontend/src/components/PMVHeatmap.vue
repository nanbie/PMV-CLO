<script setup>
import { ref, onMounted, watch } from 'vue'
import { use } from 'echarts/core'
import { SVGRenderer } from 'echarts/renderers'
import {
  TitleComponent,
  TooltipComponent,
  VisualMapComponent,
  CalendarComponent,
  LegendComponent,
  ToolboxComponent
} from 'echarts/components'
import { HeatmapChart } from 'echarts/charts'
import VChart from 'vue-echarts'
import axios from 'axios'

use([
  SVGRenderer,
  HeatmapChart,
  TitleComponent,
  TooltipComponent,
  VisualMapComponent,
  CalendarComponent,
  LegendComponent,
  ToolboxComponent
])

const props = defineProps({
  startDate: String,
  endDate: String,
  city: String,
  devIds: Array,
  cloStrategy: String,
  manualClo: Number,
  metabolicRate: Number
})

const API_URL = 'http://localhost:8000/api'
const loading = ref(false)
const optionCalendar = ref({})

const fetchData = async () => {
  loading.value = true
  try {
    const params = {
      start_date: props.startDate,
      end_date: props.endDate,
      city: props.city,
      dev_ids: props.devIds,
      clo_strategy: props.cloStrategy,
      manual_clo: props.manualClo,
      metabolic_rate: props.metabolicRate
    }

    const response = await axios.get(`${API_URL}/pmv-heatmap`, { params })
    const { data } = response.data

    // ECharts calendar data format: [[date, value], ...]
    const chartData = data.map(item => [item.day, item.pmv])

    // Get the year for the calendar
    const year = props.startDate ? props.startDate.slice(0, 4) : new Date().getFullYear().toString()

    optionCalendar.value = {
      title: {
        top: 10,
        left: 'center',
        text: '每日平均热感觉指标 (PMV) 分布'
      },
      toolbox: {
        feature: {
          saveAsImage: {
            type: 'svg',
            title: '导出 SVG',
            name: `PMV_Daily_Calendar_${year}`
          }
        },
        right: 20,
        top: 10
      },
      tooltip: {
        formatter: (params) => {
          return `日期: ${params.value[0]}<br/>PMV: ${params.value[1]}`
        }
      },
      visualMap: {
        min: -1.5,
        max: 1.5,
        type: 'piecewise',
        orient: 'horizontal',
        left: 'center',
        top: 50,
        pieces: [
          { gt: 1.0, label: 'Ⅲ级(>1.0)热', color: '#AA6500' },
          { gt: 0.5, lte: 1.0, label: 'Ⅱ级(0.5~1.0)暖', color: '#FF9700' },
          { gte: -0.5, lte: 0.5, label: 'Ⅰ级(±0.5)舒适', color: '#08C708' },
          { gte: -1.0, lt: -0.5, label: 'Ⅱ级(-1.0~-0.5)凉', color: '#159DD3' },
          { lt: -1.0, label: 'Ⅲ级(<-1.0)冷', color: '#14095D' }
        ]
      },
      calendar: {
        top: 120,
        left: 30,
        right: 30,
        cellSize: ['auto', 20],
        range: year,
        itemStyle: {
          borderWidth: 0.5
        },
        yearLabel: { show: false },
        dayLabel: {
            firstDay: 1,
            nameMap: 'cn'
        },
        monthLabel: {
            nameMap: 'cn'
        }
      },
      series: {
        type: 'heatmap',
        coordinateSystem: 'calendar',
        data: chartData
      }
    }
  } catch (err) {
    console.error('Failed to fetch calendar data:', err)
  } finally {
    loading.value = false
  }
}

watch(() => [props.startDate, props.endDate, props.city, props.devIds, props.cloStrategy, props.manualClo, props.metabolicRate], fetchData)

onMounted(fetchData)
</script>

<template>
  <div class="calendar-container">
    <v-chart class="chart" :option="optionCalendar" :loading="loading" autoresize :init-options="{ renderer: 'svg' }" />
  </div>
</template>

<style scoped>
.calendar-container {
  height: 300px;
  width: 100%;
  background: #fff;
  border-radius: 8px;
  padding: 15px;
}
.chart {
  height: 100%;
  width: 100%;
}
</style>
