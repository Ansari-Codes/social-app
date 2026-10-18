<script setup lang="ts">
import { onMounted, ref } from 'vue';
import UiSection from '@/Ui/UiSection.vue';
import UiInput from '@/Ui/UiInput.vue';
import UiButton from '@/Ui/UiButton.vue';
import UiChip from '@/Ui/UiChip.vue';
import { updateMyProfile } from '../Services/profileService';
import { useAppDataStore } from '@/Stores/appDataStore';
import type { ProfilePublic } from '../Types/profile.type';

const form = ref({
  about: '',
  powerline: '',
  banner_color: '#e11d48',
  emoji: '🙂',
  phone: '',
  birthday: '',
});

const isSaving = ref(false);
const profile = ref<ProfilePublic | null>(null);
const message = ref('');
const error = ref('');
const appData = useAppDataStore();

const presetEmojis = ['🙂', '🚀', '💻', '🎨', '⚡', '🌟', '🦊', '☕', '🌿', '💡', '🔥', '✨'];
const presetColors = [
  { name: 'Rose', hex: '#e11d48' },
  { name: 'Sky', hex: '#0284c7' },
  { name: 'Emerald', hex: '#10b981' },
  { name: 'Violet', hex: '#8b5cf6' },
  { name: 'Amber', hex: '#f59e0b' },
  { name: 'Obsidian', hex: '#1e293b' },
];

function hydrateProfile(next: ProfilePublic) {
  profile.value = next;
  form.value = {
    about: next.about ?? '',
    powerline: next.powerline ?? '',
    banner_color: next.banner_color ?? '#e11d48',
    emoji: next.emoji ?? '🙂',
    phone: next.phone ?? '',
    birthday: next.birthday ?? '',
  };
}

async function loadProfile() {
  try {
    const next = await appData.loadMyProfile();
    hydrateProfile(next);
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Unable to load profile.';
  }
}

async function saveProfile() {
  isSaving.value = true;
  message.value = '';
  error.value = '';
  try {
    const next = await updateMyProfile({
      about: form.value.about || null,
      powerline: form.value.powerline || null,
      banner_color: form.value.banner_color || null,
      emoji: form.value.emoji || null,
      phone: form.value.phone || null,
      birthday: form.value.birthday || null,
    });
    hydrateProfile(next);
    message.value = 'Profile updated successfully!';
    setTimeout(() => { message.value = ''; }, 4000);
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to save profile changes.';
  } finally {
    isSaving.value = false;
  }
}

onMounted(() => {
  void loadProfile();
});
</script>

<template>
  <div class="flex flex-col gap-6">
    <!-- ── Live Profile Card Preview ────────────────────────────── -->
    <UiSection
      title="Profile Preview"
      description="How your identity appears across the community feed and discussions"
      bordered
      shadow
      radius="xl"
      padding="md"
    >
      <div class="overflow-hidden rounded-2xl border border-border bg-bg-elevated shadow-card">
        <!-- Banner Bar -->
        <div
          class="h-20 w-full transition-colors duration-200"
          :style="{ backgroundColor: form.banner_color }"
        />
        <!-- User Identity Row -->
        <div class="relative -mt-8 flex items-end justify-between px-5 pb-4">
          <div class="flex items-end gap-3.5">
            <span
              class="grid h-16 w-16 place-items-center rounded-2xl border-2 border-bg-elevated bg-bg-sunken text-3xl shadow-md"
              aria-hidden="true"
            >
              {{ form.emoji || '🙂' }}
            </span>
            <div class="pb-1">
              <h3 class="text-base font-bold text-text-h">
                {{ profile?.display_name || profile?.username || 'Your Name' }}
              </h3>
              <p class="text-xs text-text-muted">@{{ profile?.username || 'username' }}</p>
            </div>
          </div>
          <UiChip size="sm" variant="accent" :clickable="false">Live Preview</UiChip>
        </div>

        <div v-if="form.powerline || form.about" class="border-t border-border/60 px-5 py-3 text-xs">
          <p v-if="form.powerline" class="font-semibold text-accent mb-1">{{ form.powerline }}</p>
          <p v-if="form.about" class="text-text-muted leading-relaxed line-clamp-2">{{ form.about }}</p>
        </div>
      </div>
    </UiSection>

    <!-- ── Profile Form Section ─────────────────────────────────── -->
    <UiSection
      title="Personal Details & Bio"
      description="Customize your public presence, status headline, and contact details"
      bordered
      shadow
      radius="xl"
      padding="lg"
    >
      <!-- Feedback Alerts -->
      <div v-if="message" class="mb-4 rounded-xl border border-success/30 bg-success/10 p-3 text-xs font-semibold text-success flex items-center gap-2">
        <span aria-hidden="true">✓</span> {{ message }}
      </div>
      <div v-if="error" class="mb-4 rounded-xl border border-danger/30 bg-danger/10 p-3 text-xs font-semibold text-danger flex items-center gap-2">
        <span aria-hidden="true">⚠️</span> {{ error }}
      </div>

      <form class="flex flex-col gap-5" @submit.prevent="saveProfile">
        <!-- Avatar Emoji & Presets -->
        <div class="flex flex-col gap-2">
          <label class="text-sm font-semibold text-text-h">Avatar Emoji</label>
          <div class="flex flex-wrap items-center gap-2">
            <input
              v-model="form.emoji"
              maxlength="4"
              class="h-10 w-16 text-center text-xl rounded-xl border border-border bg-bg text-text outline-none focus:border-accent"
              placeholder="🙂"
            />
            <button
              v-for="e in presetEmojis"
              :key="e"
              type="button"
              class="grid h-9 w-9 place-items-center rounded-xl border transition-transform hover:scale-110 active:scale-95"
              :class="form.emoji === e ? 'border-accent bg-accent/15' : 'border-border bg-bg-sunken hover:border-border-strong'"
              @click="form.emoji = e"
            >
              {{ e }}
            </button>
          </div>
          <span class="text-[11px] text-text-muted">Choose a quick preset or type any custom emoji.</span>
        </div>

        <!-- Banner Accent Color -->
        <div class="flex flex-col gap-2">
          <label class="text-sm font-semibold text-text-h">Banner Theme Accent</label>
          <div class="flex flex-wrap items-center gap-2.5">
            <button
              v-for="color in presetColors"
              :key="color.hex"
              type="button"
              class="flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-semibold transition-transform hover:scale-105"
              :class="form.banner_color === color.hex ? 'border-accent bg-accent/10 text-accent ring-2 ring-accent/30' : 'border-border bg-bg text-text-muted'"
              @click="form.banner_color = color.hex"
            >
              <span class="h-3 w-3 rounded-full" :style="{ backgroundColor: color.hex }" />
              <span>{{ color.name }}</span>
            </button>
            <div class="flex items-center gap-2 ml-1">
              <input v-model="form.banner_color" type="color" class="h-8 w-8 cursor-pointer rounded-lg border-0 bg-transparent p-0" />
              <span class="font-mono text-xs text-text-muted">{{ form.banner_color }}</span>
            </div>
          </div>
        </div>

        <!-- Headline / Powerline -->
        <UiInput
          v-model="form.powerline"
          label="Headline & Status Line"
          placeholder="e.g. Building open-source tools · Exploring silence"
          hint="A brief tagline shown directly beneath your handle."
        />

        <!-- Bio / About -->
        <UiInput
          v-model="form.about"
          textarea
          :rows="4"
          label="Bio / About Yourself"
          placeholder="Share your interests, philosophies, or what brings you to SilenceBook..."
          hint="Supports markdown formatting. Visible to all users visiting your profile."
        />

        <!-- Contact & Birthday -->
        <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <UiInput
            v-model="form.phone"
            type="tel"
            label="Phone Number"
            placeholder="+1 (555) 012-3456"
            hint="Private field — visible only to you on your profile."
          />
          <UiInput
            v-model="form.birthday"
            type="date"
            label="Birthday"
            hint="Optional birthdate for your profile."
          />
        </div>

        <!-- Action Submit Bar -->
        <div class="flex items-center justify-end gap-3 border-t border-border/80 pt-4">
          <UiButton
            type="submit"
            :loading="isSaving"
            class="font-semibold px-5"
          >
            <template #leading><span aria-hidden="true">💾</span></template>
            Save Profile Changes
          </UiButton>
        </div>
      </form>
    </UiSection>
  </div>
</template>
