<script lang="ts" setup>
import { APP_NAME } from '@/Core/config';
</script>

<template>
    <main class="mx-auto w-full max-w-4xl px-4 py-10 sm:px-6 sm:py-14">
        <p class="text-xs font-semibold uppercase tracking-wider text-accent">About</p>
        <h1 class="mt-2 text-3xl font-bold text-text-h sm:text-4xl">A place for thoughtful conversation.</h1>
        <p class="mt-5 max-w-2xl text-base leading-relaxed text-text-muted">
            {{ APP_NAME }} is a text-first community for sharing ideas, following conversations, and picking up a thread where it left off.
        </p>

        <div class="mt-10 grid gap-8 border-t border-border pt-8 sm:grid-cols-3">
            <section>
                <h2 class="text-sm font-bold text-text-h">Share</h2>
                <p class="mt-2 text-sm leading-relaxed text-text-muted">Publish short posts and give people a clear place to respond.</p>
            </section>
            <section>
                <h2 class="text-sm font-bold text-text-h">Follow the thread</h2>
                <p class="mt-2 text-sm leading-relaxed text-text-muted">Read public posts and nested replies without losing the original context.</p>
            </section>
            <section>
                <h2 class="text-sm font-bold text-text-h">Find your people</h2>
                <p class="mt-2 text-sm leading-relaxed text-text-muted">Follow creators, react to posts, and keep up with the conversations you care about.</p>
            </section>
        </div>
    </main>
</template>