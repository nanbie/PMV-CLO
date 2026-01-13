<script setup>
import { ref, onMounted, watch } from 'vue'
import { use } from 'echarts/core'
import { SVGRenderer } from 'echarts/renderers'
import {
  TitleComponent,
  TooltipComponent,
  GridComponent,
  VisualMapComponent,
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
  GridComponent,
  VisualMapComponent,
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
const optionHeatmap = ref({})

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

    // Call the hourly specific endpoint
    const response = await axios.get(`${API_URL}/pmv-hourly-heatmap`, { params })
    const { days, hours, data, stats } = response.data

    optionHeatmap.value = {
      title: [
        {
          text: '每时刻热感觉指标 (PMV) 分布',
          left: 'center',
          top: 10,
          textStyle: {
            fontSize: 18,
            fontWeight: 'bold'
          }
        },
        {
          text: stats ? `统计结果： I级 (90%感觉满意) ${stats.level1}%    II级 (75%感觉满意) ${stats.level2}%    III级 (低于75%感觉满意) ${stats.level3}%` : '',
          left: 'center',
          top: 45,
          textStyle: {
            fontSize: 14,
            fontWeight: 'normal',
            color: '#666'
          }
        }
      ],
      toolbox: {
        feature: {
          saveAsImage: {
            type: 'svg',
            title: '导出 SVG',
            name: 'PMV_Hourly_Heatmap'
          }
        },
        right: 20,
        top: 10
      },
      tooltip: {
        position: 'top',
        formatter: (params) => {
          const val = params.data[2]
          return `日期: ${days[params.data[0]]}<br/>时间: ${hours[params.data[1]]}<br/>PMV: ${val}`
        }
      },
      grid: {
        top: 85,
        bottom: 80,
        left: 80,
        right: 40
      },
      xAxis: {
        type: 'category',
        data: days.map(d => d.slice(5).replace('-', '/')), // MM/DD format
        axisLabel: {
          interval: days.length > 20 ? Math.floor(days.length / 10) : 0,
          rotate: 0,
          fontSize: 9,
          color: '#666'
        }
      },
      yAxis: {
        type: 'category',
        data: hours,
        axisLabel: {
          fontSize: 10,
          color: '#666'
        },
        name: '时间段',
        nameLocation: 'middle',
        nameGap: 50,
        nameTextStyle: {
          fontWeight: 'bold',
          fontSize: 12,
          color: '#333'
        }
      },
      visualMap: {
        type: 'piecewise',
        orient: 'horizontal',
        left: 'center',
        bottom: 10,
        pieces: [
          { gt: 1.0, label: 'Ⅲ级(>1.0)热', color: '#AA6500' },
          { gt: 0.5, lte: 1.0, label: 'Ⅱ级(0.5~1.0)暖', color: '#FF9700' },
          { gte: -0.5, lte: 0.5, label: 'Ⅰ级(±0.5)舒适', color: '#08C708' },
          { gte: -1.0, lt: -0.5, label: 'Ⅱ级(-1.0~-0.5)凉', color: '#159DD3' },
          { lt: -1.0, label: 'Ⅲ级(<-1.0)冷', color: '#14095D' }
        ]
      },
      series: [
        {
          name: 'PMV',
          type: 'heatmap',
          data: data,
          label: {
            show: data.length < 200,
            fontSize: 9
          },
          emphasis: {
            itemStyle: {
              shadowBlur: 10,
              shadowColor: 'rgba(0, 0, 0, 0.5)'
            }
          }
        }
      ]
    }
  } catch (err) {
    console.error('Failed to fetch hourly heatmap data:', err)
  } finally {
    loading.value = false
  }
}

watch(() => [props.startDate, props.endDate, props.city, props.devIds, props.cloStrategy, props.manualClo, props.metabolicRate], fetchData)

onMounted(fetchData)
</script>

<template>
  <div class="heatmap-container">
    <v-chart class="chart" :option="optionHeatmap" :loading="loading" autoresize :init-options="{ renderer: 'svg' }" />
  </div>
</template>

<style scoped>
.heatmap-container {
  height: 450px;
  width: 100%;
  margin-top: 30px;
  background: #fff;
  border-radius: 8px;
  padding: 15px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.05);
}
.chart {
  height: 100%;
  width: 100%;
}
</style>
