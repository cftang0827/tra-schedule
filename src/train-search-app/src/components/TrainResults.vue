<template>
  <div class="p-4 flex justify-center">
    <div v-if="trains.length === 0" class="text-gray-500 text-center mt-4">目前沒有查詢結果</div>

    <!-- 班次卡片：根據螢幕大小調整寬度 -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 w-full">
      <div
        v-for="(train, index) in trains"
        :key="index"
        class="train-card"
      >
        <h3 class="text-lg font-semibold text-gray-800 mb-2">
          🚆 {{ train.train_code }} {{ train.car_name }}
          <span v-if="train.car_alias" class="text-gray-600">({{ train.car_alias }})</span>
        </h3>

        <p class="text-sm text-gray-700 mb-1">
          <span class="font-medium">出發時間：</span>{{ formatTime(train.dep_time) }}
          <span class="font-medium">抵達時間：</span>{{ formatTime(train.lc_arr_time) }}
        </p>

        <p class="text-sm text-gray-700 mb-1">
          <span class="font-medium">車種：</span>{{ train.car_class }}
          <span v-if="train.bike === 'Y'" class="ml-2">🚲 可攜自行車</span>
          <span v-if="train.cripple === 'Y'" class="ml-2">♿ 無障礙座位</span>
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  trains: {
    type: Array,
    default: () => []
  }
})

const formatTime = (isoString) => {
  const date = new Date(isoString)
  return date.toTimeString().substring(0, 5) // e.g. "06:20"
}
</script>

<style scoped>
/* Grid 設定：大螢幕上顯示 1/4 寬度，小螢幕自動填滿 */
.grid {
  margin-top: 1rem;
}

/* 桌面模式：每行顯示 4 個卡片（1/4 寬度） */
@media (min-width: 1024px) {
  .grid {
    grid-template-columns: repeat(4, 1fr); /* 桌面模式每行顯示 4 個卡片 */
  }
}

/* 中型螢幕（平板）：每行顯示 2 個卡片 */
@media (max-width: 1024px) and (min-width: 640px) {
  .grid {
    grid-template-columns: repeat(2, 1fr); /* 每行顯示 2 個卡片 */
  }
}

/* 手機模式：每行顯示 1 個卡片（佔滿整個寬度） */
@media (max-width: 640px) {
  .grid {
    grid-template-columns: 1fr; /* 每行顯示 1 個卡片 */
  }
}

/* 每個班次卡片 */
.train-card {
  background-color: #ffffff; /* 背景顏色 */
  border: 2px solid #ddd;    /* 較淺的邊框顏色 */
  border-radius: 8px;        /* 圓角 */
  padding: 1.5rem;           /* 內邊距 */
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1); /* 輕微的陰影 */
  text-align: left;          /* 文字靠左 */
}

.train-card:hover {
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.2); /* 滑鼠懸停時加強陰影 */
}

/* 標題樣式 */
.train-card h3 {
  font-size: 1.25rem; /* 標題字體大小 */
  color: #333;        /* 標題顏色 */
  margin-bottom: 1rem; /* 底部邊距 */
}

/* 內容文字 */
.train-card p {
  font-size: 0.875rem; /* 小字 */
  color: #555;         /* 文字顏色 */
}

/* 分隔符 */
.train-card span {
  font-weight: 500;     /* 讓 "出發時間"、"車種" 等文字變粗 */
}
</style>
