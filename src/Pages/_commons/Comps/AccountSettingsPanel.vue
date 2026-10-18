<script setup lang="ts">
import { onMounted, ref } from 'vue';
import UiSection from '@/Ui/UiSection.vue';
import UiInput from '@/Ui/UiInput.vue';
import UiButton from '@/Ui/UiButton.vue';
import { callAPI } from '@/Core/api';
import { useMeStore } from '@/Stores/meStore';

const me = useMeStore();
const account = ref({ username: '', email: '' });
const password = ref({
  current_password: '',
  new_password: '',
  confirm_password: '',
});

const accountMessage = ref('');
const accountError = ref('');
const isSavingAccount = ref(false);

const passwordMessage = ref('');
const passwordError = ref('');
const isChangingPassword = ref(false);

async function loadAccount() {
  if (me.user) account.value = { username: me.user.username, email: me.user.email };
}

async function saveAccount() {
  isSavingAccount.value = true;
  accountMessage.value = '';
  accountError.value = '';
  try {
    await callAPI('/users/me', {
      method: 'PATCH',
      body: {
        username: account.value.username.trim(),
        email: account.value.email.trim(),
      },
    });
    me.updateAccountDetails(account.value.username.trim(), account.value.email.trim());
    accountMessage.value = 'Account credentials updated successfully.';
    setTimeout(() => { accountMessage.value = ''; }, 4000);
  } catch (err) {
    accountError.value = err instanceof Error ? err.message : 'Unable to update account details.';
  } finally {
    isSavingAccount.value = false;
  }
}

async function changePassword() {
  isChangingPassword.value = true;
  passwordMessage.value = '';
  passwordError.value = '';

  try {
    if (password.value.new_password.length < 8) {
      throw new Error('New password must contain at least 8 characters.');
    }
    if (password.value.new_password !== password.value.confirm_password) {
      throw new Error('New password and confirmation do not match.');
    }

    await callAPI('/users/me/password', {
      method: 'POST',
      body: {
        current_password: password.value.current_password,
        new_password: password.value.new_password,
      },
    });

    passwordMessage.value = 'Password updated successfully!';
    password.value = {
      current_password: '',
      new_password: '',
      confirm_password: '',
    };
    setTimeout(() => { passwordMessage.value = ''; }, 4000);
  } catch (err) {
    passwordError.value = err instanceof Error ? err.message : 'Unable to change password.';
  } finally {
    isChangingPassword.value = false;
  }
}

onMounted(() => {
  void loadAccount();
});
</script>

<template>
  <div class="flex flex-col gap-6">
    <!-- ── Account Credentials Section ──────────────────────────── -->
    <UiSection
      title="Account Credentials"
      description="Update your unique handle and verified contact email address"
      bordered
      shadow
      radius="xl"
      padding="lg"
    >
      <div v-if="accountMessage" class="mb-4 rounded-xl border border-success/30 bg-success/10 p-3 text-xs font-semibold text-success flex items-center gap-2">
        <span aria-hidden="true">✓</span> {{ accountMessage }}
      </div>
      <div v-if="accountError" class="mb-4 rounded-xl border border-danger/30 bg-danger/10 p-3 text-xs font-semibold text-danger flex items-center gap-2">
        <span aria-hidden="true">⚠️</span> {{ accountError }}
      </div>

      <form class="flex flex-col gap-4" @submit.prevent="saveAccount">
        <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <UiInput
            v-model="account.username"
            label="Username Handle"
            placeholder="e.g. john_doe"
            hint="Unique handle used for your profile address and @mentions."
            required
          />
          <UiInput
            v-model="account.email"
            type="email"
            label="Email Address"
            placeholder="you@example.com"
            hint="Used for authentication, notifications, and security notices."
            required
          />
        </div>

        <div class="flex items-center justify-end border-t border-border/80 pt-3">
          <UiButton
            type="submit"
            :loading="isSavingAccount"
            class="font-semibold px-4"
          >
            Save Account Details
          </UiButton>
        </div>
      </form>
    </UiSection>

    <!-- ── Security & Password Management Section ──────────────── -->
    <UiSection
      title="Security & Password"
      description="Ensure your account is protected with a salted PBKDF2-HMAC-SHA256 password"
      bordered
      shadow
      radius="xl"
      padding="lg"
    >
      <div v-if="passwordMessage" class="mb-4 rounded-xl border border-success/30 bg-success/10 p-3 text-xs font-semibold text-success flex items-center gap-2">
        <span aria-hidden="true">✓</span> {{ passwordMessage }}
      </div>
      <div v-if="passwordError" class="mb-4 rounded-xl border border-danger/30 bg-danger/10 p-3 text-xs font-semibold text-danger flex items-center gap-2">
        <span aria-hidden="true">⚠️</span> {{ passwordError }}
      </div>

      <form class="flex flex-col gap-4" @submit.prevent="changePassword">
        <UiInput
          v-model="password.current_password"
          type="password"
          label="Current Password"
          placeholder="Enter current password"
          required
        />

        <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <UiInput
            v-model="password.new_password"
            type="password"
            label="New Password"
            placeholder="At least 8 characters"
            hint="Must be at least 8 characters long."
            required
          />
          <UiInput
            v-model="password.confirm_password"
            type="password"
            label="Confirm New Password"
            placeholder="Re-type new password"
            required
          />
        </div>

        <div class="flex items-center justify-end border-t border-border/80 pt-3">
          <UiButton
            type="submit"
            variant="soft"
            :loading="isChangingPassword"
            class="font-semibold px-4"
          >
            <template #leading><span aria-hidden="true">🔐</span></template>
            Update Password
          </UiButton>
        </div>
      </form>
    </UiSection>
  </div>
</template>
