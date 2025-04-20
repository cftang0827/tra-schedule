<template>
  <div class="home">
    <SearchForm @onResult="handleResult" />
    <TrainResults :trains="trains" />
  </div>
</template>

<script setup>
import SearchForm from './components/SearchForm.vue';
import TrainResults from './components/TrainResults.vue';
import { ref } from 'vue'

const trains = ref([])  // 初始時 trains 為空陣列

// 處理來自 SearchForm 組件的結果
const handleResult = (newTrains) => {
  console.log({newTrains})
  trains.value = newTrains  // 更新 trains 的值
}


// Removed export default as <script setup> already handles it
</script>

<style>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
  margin-top: 60px;
}
</style>
