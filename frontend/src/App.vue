<template>
  <div id="app">
    <router-view />
  </div>
</template>

<script setup lang="ts">
// @ts-nocheck
// App root component
</script>

<style lang="scss">
@use './styles/variables.scss' as *;

#app {
  font-family: $apple-font-family;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  font-size: $apple-font-body;
  color: $apple-text-primary;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  background-color: $apple-bg-page;
  font-family: $apple-font-family;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}
</style>