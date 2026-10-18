<template>
    <main class="mx-auto w-full max-w-3xl px-4 py-10 sm:px-6 sm:py-14">
        <p class="text-xs font-semibold uppercase tracking-wider text-accent">Legal</p>
        <h1 class="mt-2 text-3xl font-bold text-text-h sm:text-4xl">Terms and Conditions</h1>
        <p class="mt-3 text-sm text-text-muted">Effective October 17, 2026</p>

        <div class="mt-8 space-y-8 border-t border-border pt-8 text-sm leading-relaxed text-text-muted">
            <section>
                <h2 class="text-base font-bold text-text-h">Using the service</h2>
                <p class="mt-2">By accessing {{ appName }}, you agree to these terms. If you do not agree, do not use the service. You must use the service only where doing so is permitted by applicable law.</p>
            </section>
            <section>
                <h2 class="text-base font-bold text-text-h">Your account</h2>
                <p class="mt-2">Keep your sign-in credentials private and provide accurate account information. You are responsible for activity performed through your account. Contact us if you believe your account has been accessed without permission.</p>
            </section>
            <section>
                <h2 class="text-base font-bold text-text-h">Posts and community conduct</h2>
                <p class="mt-2">You retain ownership of content you submit. You give {{ appName }} permission to host, store, display, and distribute that content as needed to operate the service. Only post content you have the right to share. Do not use the service to violate others' rights, break the law, disrupt the service, or harass or threaten people.</p>
            </section>
            <section>
                <h2 class="text-base font-bold text-text-h">Public content</h2>
                <p class="mt-2">Posts and replies are visible to visitors. Do not include private or sensitive information in public content. Profile fields marked private are only returned to the profile owner by the application.</p>
            </section>
            <section>
                <h2 class="text-base font-bold text-text-h">Availability and changes</h2>
                <p class="mt-2">We may change, suspend, or discontinue parts of the service, and may remove content or restrict accounts when needed to protect the service or its users. The service is provided on an “as available” basis to the extent permitted by law.</p>
            </section>
            <section>
                <h2 class="text-base font-bold text-text-h">Contact</h2>
                <p class="mt-2">Questions about these terms can be sent to <a class="text-accent underline" href="mailto:hi@dotmuted.com">hi@dotmuted.com</a>.</p>
            </section>
        </div>
    </main>
</template>

<script setup lang="ts">
import { APP_NAME } from '@/Core/config';

const appName = APP_NAME;
</script>