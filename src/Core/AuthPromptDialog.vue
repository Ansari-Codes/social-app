<script setup lang="ts">
import { authPromptOpen } from '@/Core/authPrompt'
import UiDialog from '@/Ui/UiDialog.vue'

function closePrompt() {
    authPromptOpen.value = false
}
</script>

<template>
    <UiDialog
        v-model="authPromptOpen"
        title="Join the conversation"
        description="Sign in or create an account to post, reply, react, or follow people."
        icon="🔐"
        size="sm"
    >
        <div class="flex flex-col gap-2 sm:flex-row">
            <RouterLink
                :to="{ name: 'login' }"
                class="inline-flex h-10 flex-1 items-center justify-center rounded-md bg-accent px-4 text-sm font-semibold text-accent-fg no-underline hover:bg-accent-hover"
                @click="closePrompt"
            >
                Log in
            </RouterLink>
            <RouterLink
                :to="{ name: 'signup' }"
                class="inline-flex h-10 flex-1 items-center justify-center rounded-md border border-border bg-bg-elevated px-4 text-sm font-semibold text-text-h no-underline hover:bg-bg-hover"
                @click="closePrompt"
            >
                Sign up
            </RouterLink>
        </div>
    </UiDialog>
</template>