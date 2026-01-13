<script setup>
import PMVHeatmap from './components/PMVHeatmap.vue'
import HourlyPMVHeatmap from './components/HourlyPMVHeatmap.vue'
import DailyTrend from './components/DailyTrend.vue'

import { ref } from 'vue'
import axios from 'axios'

const API_URL = 'http://localhost:8000/api'

const ta = ref(25)
const rh = ref(50)
const vel = ref(0.15)
const tr = ref(25)
const clo = ref(0.5)
const met = ref(1.0)
const pmvResult = ref(null)
const calculating = ref(false)

// Global Date State
const today = new Date()
const endDate = ref(today.toISOString().slice(0, 10))
const startDate = ref(
  new Date(today.getTime() - 90 * 24 * 60 * 60 * 1000)
    .toISOString()
    .slice(0, 10)
)

const handleDateChange = (newDates) => {
  startDate.value = newDates.startDate
  endDate.value = newDates.endDate
}

// Global Calculation Parameters
const selectedCity = ref('beijing')
const selectedFloor = ref('14f')

const floorDevices = {
  'all': [],
  '6f': [
    'SJ-A0-C01-06F-00-CGQ-0001', 'SJ-A0-C01-06F-00-CGQ-0002', 'SJ-A0-C01-06F-00-CGQ-0003',
    'SJ-A0-C01-06F-00-CGQ-0004', 'SJ-A0-C01-06F-00-CGQ-0005', 'SJ-A0-C01-06F-00-CGQ-0006',
    'SJ-A0-C01-06F-00-CGQ-0007', 'SJ-A0-C01-06F-00-CGQ-0008'
  ],
  '7f': [
    'SJ-A0-C01-07F-00-CGQ-0011', 'SJ-A0-C01-07F-00-CGQ-0009', 'SJ-A0-C01-07F-00-CGQ-0010',
    'SJ-A0-C01-07F-00-CGQ-0012', 'SJ-A0-C01-07F-00-CGQ-0013', 'SJ-A0-C01-07F-00-CGQ-0014'
  ],
  '8f': [
    'SJ-A0-C01-08F-00-CGQ-0017', 'SJ-A0-C01-08F-00-CGQ-0015', 'SJ-A0-C01-08F-00-CGQ-0016',
    'SJ-A0-C01-08F-00-CGQ-0018', 'SJ-A0-C01-08F-00-CGQ-0019', 'SJ-A0-C01-08F-00-CGQ-0020'
  ],
  '9f': [
    'SJ-A0-C01-09F-00-CGQ-0023', 'SJ-A0-C01-09F-00-CGQ-0021', 'SJ-A0-C01-09F-00-CGQ-0022',
    'SJ-A0-C01-09F-00-CGQ-0024', 'SJ-A0-C01-09F-00-CGQ-0025', 'SJ-A0-C01-09F-00-CGQ-0026'
  ],
  '12f': [
    'SJ-A0-C01-12F-00-CGQ-0011', 'SJ-A0-C01-12F-00-CGQ-0012', 'SJ-A0-C01-12F-00-CGQ-0013',
    'SJ-A0-C01-12F-00-CGQ-0014', 'SJ-A0-C01-12F-00-CGQ-0015'
  ],
  '14f': [
    'SJ-A0-C01-14F-00-HL-CGQ-0005', 'SJ-A0-C01-14F-00-HL-CGQ-0006', 
    'SJ-A0-C01-14F-00-HL-CGQ-0008', 'SJ-A0-C01-14F-00-HL-CGQ-0007', 
    'SJ-A0-C01-14F-00-HL-CGQ-0009', 'SJ-A0-C01-14F-00-HL-CGQ-0004', 
    'SJ-A0-C01-14F-00-HL-CGQ-0003', 'SJ-A0-C01-14F-00-HL-CGQ-0002', 
    'SJ-A0-C01-14F-00-HL-CGQ-0001', 'SJ-A0-C01-14F-00-HL-CGQ-0010'
  ]
}

const cloStrategy = ref('fourier')
const manualClo = ref(0.7)
const metabolicRate = ref(1.0)

const calculatePMV = async () => {
  calculating.value = true
  try {
    const payload = {
      ta: Number(ta.value),
      rh: Number(rh.value),
      vel: Number(vel.value),
      tr: tr.value === null || tr.value === '' ? Number(ta.value) : Number(tr.value),
      clo: Number(clo.value),
      met: Number(met.value),
    }
    const response = await axios.post(`${API_URL}/calculate-pmv`, payload)
    pmvResult.value = response.data
  } catch (err) {
    console.error('Failed to calculate PMV', err)
    alert('计算失败，请检查参数')
  } finally {
    calculating.value = false
  }
}

const exporting = ref(false)
const exportCSV = async () => {
  exporting.value = true
  try {
    const params = {
      start_date: startDate.value,
      end_date: endDate.value,
      city: selectedCity.value,
      dev_ids: floorDevices[selectedFloor.value]
    }
    const response = await axios.get(`${API_URL}/export-data`, { 
      params,
      timeout: 60000 // 60 seconds timeout
    })
    const list = response.data?.data
    
    if (!list || list.length === 0) {
      alert('所选日期范围内没有数据')
      return
    }

    console.log(`Exporting ${list.length} rows...`)
    const headers = Object.keys(list[0])
    const csvContent = [
      headers.join(','),
      ...list.map(row => headers.map(h => row[h]).join(','))
    ].join('\n')

    const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    const url = URL.createObjectURL(blob)
    link.setAttribute('href', url)
    link.setAttribute('download', `PMV_Export_${startDate.value}_${endDate.value}.csv`)
    link.style.visibility = 'hidden'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  } catch (err) {
    console.error('Failed to export data', err)
    alert('导出失败，请重试')
  } finally {
    exporting.value = false
  }
}
</script>

<template>
  <div class="container">
    <h1>环境监测与 PMV 参数分析</h1>
    <p class="subtitle">展示 9:00 - 18:00 平均热感觉指标 (PMV) 分布，可输入参数计算 PMV</p>

    <div class="panel-row">
      <div class="panel">
        <h2>PMV 六参数输入</h2>
        <div class="grid-2">
          <div class="form-row">
            <label>温度 Ta (°C)</label>
            <input type="number" v-model.number="ta" step="0.1" />
          </div>
          <div class="form-row">
            <label>相对湿度 RH (%)</label>
            <input type="number" v-model.number="rh" step="1" />
          </div>
          <div class="form-row">
            <label>风速 Vel (m/s)</label>
            <input type="number" v-model.number="vel" step="0.01" />
          </div>
          <div class="form-row">
            <label>辐射温度 Tr (°C)</label>
            <input type="number" v-model.number="tr" step="0.1" />
          </div>
          <div class="form-row">
            <label>服装热阻 CLO</label>
            <input type="number" v-model.number="clo" step="0.05" />
          </div>
          <div class="form-row">
            <label>代谢率 MET</label>
            <input type="number" v-model.number="met" step="0.1" />
          </div>
        </div>
        <button class="pmv-button" @click="calculatePMV" :disabled="calculating">计算 PMV</button>

        <div v-if="pmvResult" class="pmv-result">
          <div class="pmv-row">
            <span class="pmv-label">PMV</span>
            <span class="pmv-value">{{ pmvResult.pmv }}</span>
          </div>
          <div class="pmv-row">
            <span class="pmv-label">PPD (%)</span>
            <span class="pmv-value">{{ pmvResult.ppd }}</span>
          </div>
        </div>
      </div>

      <div class="panel">
        <h2>全局计算策略 (可视化联动)</h2>
        <div class="form-row">
          <label>选择城市</label>
          <select v-model="selectedCity">
            <option value="beijing">北京</option>
          </select>
        </div>
        <div class="form-row">
          <label>选择楼层/分区</label>
          <select v-model="selectedFloor">
            <option value="all">全部楼层</option>
            <option value="6f">6层</option>
            <option value="7f">7层</option>
            <option value="8f">8层</option>
            <option value="9f">9层</option>
            <option value="12f">12层</option>
            <option value="14f">14层</option>
          </select>
        </div>
        <div class="form-row">
          <label>服装热阻策略</label>
          <select v-model="cloStrategy">
            <option value="fourier">傅里叶拟合 (季节性)</option>
            <option value="month">按月固定</option>
            <option value="fixed_summer">夏季固定 (0.5)</option>
            <option value="fixed_winter">冬季固定 (1.0)</option>
            <option value="manual">手动输入</option>
          </select>
        </div>
        <div class="form-row" v-if="cloStrategy === 'manual'">
          <label>手动 CLO 值</label>
          <input type="number" v-model.number="manualClo" step="0.1" min="0.3" max="1.5" />
        </div>
        <div class="form-row">
          <label>代谢率 (Met)</label>
          <input type="number" v-model.number="metabolicRate" step="0.1" min="0.8" max="4.0" />
        </div>
        <div class="info-box">
          <p>此处的设置将影响下方所有可视化图表（趋势图、分布图）的 PMV 计算。</p>
        </div>
      </div>

      <button 
        class="calc-btn export-btn" 
        @click="exportCSV" 
        :disabled="exporting"
      >
        {{ exporting ? '导出中...' : '导出所选日期数据 (CSV)' }}
      </button>
    </div>

    <DailyTrend 
      :startDate="startDate" 
      :endDate="endDate" 
      :city="selectedCity"
      :devIds="floorDevices[selectedFloor]"
      :cloStrategy="cloStrategy"
      :manualClo="parseFloat(manualClo)"
      :metabolicRate="parseFloat(metabolicRate)"
      @update:dates="handleDateChange"
    />
    <!-- 每时刻 PMV 热力分布 -->
    <div class="card full-width">
      <HourlyPMVHeatmap 
        :startDate="startDate" 
        :endDate="endDate"
        :city="selectedCity"
        :devIds="floorDevices[selectedFloor]"
        :cloStrategy="cloStrategy"
        :manualClo="parseFloat(manualClo)"
        :metabolicRate="parseFloat(metabolicRate)"
      />
    </div>

    <!-- 每日 PMV 日历分布 -->
    <div class="card full-width">
      <PMVHeatmap 
        :startDate="startDate" 
        :endDate="endDate"
        :city="selectedCity"
        :devIds="floorDevices[selectedFloor]"
        :cloStrategy="cloStrategy"
        :manualClo="parseFloat(manualClo)"
        :metabolicRate="parseFloat(metabolicRate)"
      />
    </div>
  </div>
</template>

<style scoped>
.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px;
  font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
  color: #333;
}

h1 {
  text-align: center;
  color: #2c3e50;
  margin-bottom: 8px;
}

.subtitle {
  text-align: center;
  color: #7f8c8d;
  margin-bottom: 30px;
  font-size: 1rem;
}

.panel-row {
  display: flex;
  gap: 20px;
  margin-bottom: 30px;
  align-items: flex-start;
}

.panel {
  flex: 1;
  background: #f8f9fa;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

.grid-2 {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 15px;
}

.form-row {
  display: flex;
  flex-direction: column;
  gap: 5px;
  margin-bottom: 10px;
}

.form-row label {
  font-size: 0.85rem;
  color: #555;
  font-weight: bold;
}

.form-row input, .form-row select {
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.pmv-button {
  width: 100%;
  padding: 10px;
  background: #4a90e2;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  margin-top: 10px;
  font-weight: bold;
}

.pmv-button:hover {
  background: #357abd;
}

.pmv-result {
  margin-top: 20px;
  padding-top: 15px;
  border-top: 1px solid #ddd;
}

.pmv-row {
  display: flex;
  justify-content: space-between;
  margin-bottom: 5px;
}

.pmv-label {
  color: #666;
}

.pmv-value {
  font-weight: bold;
  color: #333;
}

.info-box {
  margin-top: 15px;
  padding: 10px;
  background: #e7f3ff;
  border-left: 4px solid #4a90e2;
  border-radius: 4px;
}

.info-box p {
  margin: 0;
  font-size: 0.8rem;
  color: #4a6a8e;
  line-height: 1.4;
}

.card {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.05);
  margin-bottom: 24px;
  padding: 20px;
}

.full-width {
  width: 100%;
}

.export-btn {
  background: #28a745;
  color: white;
  padding: 12px 20px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: bold;
  align-self: center;
}

.export-btn:hover {
  background: #218838;
}

.export-btn:disabled {
  background: #6c757d;
  cursor: not-allowed;
}

.panel-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 16px;
  margin-bottom: 20px;
}

.panel {
  background: #ffffff;
  border-radius: 8px;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.05);
  padding: 16px 18px 18px;
}

h2 {
  margin: 0 0 12px;
  font-size: 1rem;
  border-bottom: 1px solid #eee;
  padding-bottom: 8px;
  color: #333;
}

.form-row {
  display: flex;
  flex-direction: column;
  margin-bottom: 10px;
}

.form-row label {
  font-size: 0.85rem;
  color: #555;
  margin-bottom: 4px;
}

.form-row input {
  padding: 6px 8px;
  border-radius: 4px;
  border: 1px solid #ccc;
  font-size: 0.9rem;
}

.grid-2 {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px 12px;
}

.hint {
  font-size: 0.8rem;
  color: #888;
  margin-top: 4px;
}

.pmv-button {
  margin-top: 8px;
  padding: 8px 12px;
  border-radius: 4px;
  border: none;
  background-color: #007bff;
  color: #fff;
  font-size: 0.9rem;
  cursor: pointer;
}

.pmv-button:disabled {
  background-color: #9abcf0;
  cursor: not-allowed;
}

.pmv-result {
  margin-top: 10px;
  padding-top: 8px;
  border-top: 1px solid #eee;
}

.pmv-row {
  display: flex;
  justify-content: space-between;
  margin-bottom: 4px;
}

.pmv-label {
  font-size: 0.9rem;
  color: #555;
}

.pmv-value {
  font-weight: bold;
  color: #222;
}
.export-btn {
  background: #08C708;
  margin-top: 15px;
  width: 100%;
}

.export-btn:hover {
  background: #06a306;
}

.export-btn:disabled {
  background: #ccc;
}
</style>
