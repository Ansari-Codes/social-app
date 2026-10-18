<script setup lang="ts">
import { computed, ref } from 'vue';
import { RouterLink } from 'vue-router';

import AccountSettingsPanel from '@/Pages/_commons/Comps/AccountSettingsPanel.vue';
import AppearanceSettingsPanel from '@/Pages/_commons/Comps/AppearanceSettingsPanel.vue';
import ProfileSettingsPanel from '@/Pages/_commons/Comps/ProfileSettingsPanel.vue';
import SettingsSidebar from '@/Pages/_commons/Comps/SettingsSidebar.vue';
import type { SettingsTab } from '@/Pages/_commons/Types/settings.type';

const tabs = [
	{
		key: 'profile',
		label: 'Profile',
		icon: '👤',
		description: 'Bio, avatar & theme',
	},
	{
		key: 'account',
		label: 'Account',
		icon: '🔐',
		description: 'Credentials & security',
	},
	{
		key: 'appearance',
		label: 'Appearance',
		icon: '🎨',
		description: 'Theme & display mode',
	},
] as const;

const activeTab = ref<SettingsTab>('profile');

const activePanel = computed(() => {
	if (activeTab.value === 'account') return AccountSettingsPanel;
	if (activeTab.value === 'appearance') return AppearanceSettingsPanel;
	return ProfileSettingsPanel;
});
</script>

<template>
	<main class="mx-auto max-w-6xl px-4 py-6 md:py-8">
		<!-- Header / Breadcrumbs -->
		<div class="mb-6 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
			<div>
				<div class="flex items-center gap-2 text-xs font-semibold text-text-muted mb-1">
					<RouterLink
						:to="{ name: 'app' }"
						class="flex items-center gap-1 hover:text-accent transition-colors"
					>
						<span aria-hidden="true">←</span> Back to Feed
					</RouterLink>
					<span>/</span>
					<span class="text-text-h">Settings</span>
				</div>
				<h1 class="text-2xl font-black tracking-tight text-text-h md:text-3xl">
					Settings & Preferences
				</h1>
				<p class="text-xs text-text-muted md:text-sm">
					Manage your identity, account security, and display preferences.
				</p>
			</div>
		</div>

		<!-- Settings Body with Sidebar and Panel -->
		<div class="rounded-3xl border border-border bg-bg-elevated p-4 shadow-card md:p-6">
			<div class="flex flex-col gap-6 md:flex-row">
				<SettingsSidebar :tabs="tabs" :active="activeTab" @change="activeTab = $event" />

				<div class="min-w-0 flex-1">
					<component :is="activePanel" />
				</div>
			</div>
		</div>
	</main>
</template>