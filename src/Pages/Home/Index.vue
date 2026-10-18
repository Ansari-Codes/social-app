<script lang="ts" setup>
import { RouterView } from 'vue-router';

import CompHeader from './Comps/CompHeader.vue';
import CompFooter from './Comps/CompFooter.vue';

console.log('Home/Index.vue setup ran');
</script>

<template>
    <CompHeader></CompHeader>
        <RouterView></RouterView>
    <CompFooter></CompFooter>
</template>
