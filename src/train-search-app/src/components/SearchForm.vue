<template>
    <div class="search-form">
      <h2>查詢列車班次</h2>
      <form @submit.prevent="submit">
        <div>
          <label>起站：</label>
          <select v-model="departure">
            <option disabled value="">請選擇</option>
            <option v-for="station in stations" :key="station.station_id" :value="station.station_id">
              {{ station.station_name }}
            </option>
          </select>
        </div>
  
        <div>
          <label>到站：</label>
          <select v-model="arrival">
            <option disabled value="">請選擇</option>
            <option v-for="station in stations" :key="station.station_id" :value="station.station_id">
              {{ station.station_name }}
            </option>
          </select>
        </div>
  
        <div>
          <label>日期：</label>
          <input type="date" v-model="travelDate" />
        </div>
  
        <div>
          <label>時間：</label>
          <input type="time" v-model="travelTime" />
        </div>
  
        <button type="submit">查詢班次</button>
      </form>
    </div>
  </template>
  
  <script setup>
  import { ref, onMounted } from 'vue'
  import axios from 'axios'
  
  const stations = ref([])
  const departure = ref('1040')
  const arrival = ref('1000')
  const travelDate = ref('2025-04-18')
  const travelTime = ref('00:00:00')
  
  onMounted(async () => {
    const response = await axios.get('/stations')
    stations.value = response.data
  })

  const emit = defineEmits(['onResult'])
  
  const submit = async () => {
    if (!departure.value || !arrival.value || !travelDate.value || !travelTime.value) {
      alert('請完整填寫欄位')
      return
    }
  
    const res = await axios.get('/timetable', {
      params: {
        departure_station: departure.value,
        arrival_station: arrival.value,
        travel_day: travelDate.value,
        travel_time: travelTime.value + ':00' // 確保有秒
      }
    })

    emit('onResult', res.data)
    // TODO: 你可以 emit 給外層處理，或存在本地 state
  }
  </script>
  
  <style scoped>
  .search-form {
    max-width: 400px;
    margin: 2rem auto;
    padding: 1rem;
    border: 1px solid #ccc;
    border-radius: 0.5rem;
  }
  .search-form div {
    margin-bottom: 1rem;
  }
  </style>
  