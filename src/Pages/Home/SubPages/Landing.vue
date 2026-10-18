<script lang="ts" setup>
import UiTitle from '@/Ui/UiTitle.vue';
import { APP_NAME } from '@/Core/config';
</script>

<template>
    <div class="fixed inset-0 flex items-center justify-center">
        <UiTitle
            :label="APP_NAME"
            class="text-9xl"
        />
    </div>
</template>