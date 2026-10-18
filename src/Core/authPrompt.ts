import { ref } from 'vue'

export const authPromptOpen = ref(false)

export function requestAuthPrompt(): void {
    authPromptOpen.value = true
}