<template>
  <section class="app-main">
    <router-view v-slot="{ Component, route }">
      <transition name="fade-transform" mode="out-in">
        <div :key="route.fullPath" class="page-view">
          <component :is="Component" />
        </div>
      </transition>
    </router-view>
  </section>
</template>

<style scoped>
.app-main {
  position: relative;
  flex: 1;
  width: 100%;
  min-height: 0;
  overflow: hidden;
  background-color: var(--ant-color-bg-layout);
}

.page-view {
  width: 100%;
  height: 100%;
  min-height: 0;
}
</style>
