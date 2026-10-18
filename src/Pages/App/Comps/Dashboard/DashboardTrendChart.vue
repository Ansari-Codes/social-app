<script setup lang="ts">
import { computed } from 'vue';

export interface TrendPoint {
  label: string;
  value: number;
}

const props = defineProps<{
  title: string;
  points: TrendPoint[];
  color?: string;
}>();

const chart = { width: 720, height: 232, left: 48, right: 12, top: 16, bottom: 34 };
const plotWidth = chart.width - chart.left - chart.right;
const plotHeight = chart.height - chart.top - chart.bottom;
const maxValue = computed(() => Math.max(1, ...props.points.map((point) => point.value)));
const yTicks = computed(() => [0, 0.25, 0.5, 0.75, 1].map((fraction) => Math.round(maxValue.value * fraction)));

const coordinates = computed(() => props.points.map((point, index) => {
  const x = chart.left + (index / Math.max(props.points.length - 1, 1)) * plotWidth;
  const y = chart.top + plotHeight - (point.value / maxValue.value) * plotHeight;
  return { x, y, label: point.label, value: point.value };
}));

const linePoints = computed(() => coordinates.value.map((point) => `${point.x},${point.y}`).join(' '));
const labelPoints = computed(() => {
  if (coordinates.value.length <= 3) return coordinates.value;
  return [coordinates.value[0], coordinates.value[Math.floor((coordinates.value.length - 1) / 2)], coordinates.value.at(-1)!];
});
</script>

<template>
  <section class="min-w-0 rounded-lg border border-border bg-bg-elevated p-4 sm:p-5">
    <div class="mb-3 flex items-center justify-between gap-3">
      <h2 class="text-sm font-semibold text-text-h">{{ title }}</h2>
      <span class="inline-flex items-center gap-1.5 text-xs text-text-muted">
        <span class="h-2 w-2 rounded-full" :style="{ backgroundColor: color ?? 'var(--color-accent)' }" />
        Active total
      </span>
    </div>

    <div class="w-full overflow-hidden">
      <svg
        class="block h-auto w-full"
        :viewBox="`0 0 ${chart.width} ${chart.height}`"
        preserveAspectRatio="none"
        role="img"
        :aria-label="`${title} over time`"
      >
        <title>{{ title }} over time</title>
        <g v-for="(tick, index) in yTicks" :key="`${tick}-${index}`">
          <line
            :x1="chart.left"
            :x2="chart.width - chart.right"
            :y1="chart.top + plotHeight - (index / 4) * plotHeight"
            :y2="chart.top + plotHeight - (index / 4) * plotHeight"
            stroke="var(--color-border)"
            stroke-dasharray="3 5"
          />
          <text
            :x="chart.left - 8"
            :y="chart.top + plotHeight - (index / 4) * plotHeight + 4"
            text-anchor="end"
            fill="var(--color-text-faint)"
            font-size="11"
          >
            {{ tick }}
          </text>
        </g>
        <polyline
          v-if="coordinates.length"
          :points="linePoints"
          fill="none"
          :stroke="color ?? 'var(--color-accent)'"
          stroke-width="3"
          stroke-linecap="round"
          stroke-linejoin="round"
          vector-effect="non-scaling-stroke"
        />
        <circle
          v-for="(point, index) in coordinates"
          :key="`${point.label}-${index}`"
          :cx="point.x"
          :cy="point.y"
          r="3"
          :fill="color ?? 'var(--color-accent)'"
        >
          <title>{{ point.label }}: {{ point.value }}</title>
        </circle>
      </svg>
      <div class="-mt-1 flex justify-between pl-10 text-[10px] text-text-faint">
        <span v-for="point in labelPoints" :key="point.label">{{ point.label }}</span>
      </div>
    </div>
  </section>
</template>
