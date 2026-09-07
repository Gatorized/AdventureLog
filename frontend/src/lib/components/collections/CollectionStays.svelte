<script lang="ts">
	import type { Collection, Location, User } from '$lib/types';
	import { createEventDispatcher } from 'svelte';
	import { t } from 'svelte-i18n';
	import Bed from '~icons/mdi/bed';
	import MapMarkerDistance from '~icons/mdi/map-marker-distance';
	import Pencil from '~icons/mdi/pencil';
	import { buildStayRows } from '$lib/stays';

	const dispatch = createEventDispatcher();

	export let collection: Collection;
	export let user: User | null = null;

	function formatDateOnly(dateString: string | null): string {
		if (!dateString) return '';
		return dateString.split('T')[0];
	}

	$: home =
		user?.home_latitude != null && user?.home_longitude != null
			? { latitude: user.home_latitude, longitude: user.home_longitude }
			: null;

	// One row per visit (a location visited more than once yields multiple
	// rows), sorted by start date. See $lib/stays for how the distance is
	// derived.
	$: stayRows = buildStayRows((collection?.locations || []) as Location[], home);

	function editStay(location: Location) {
		dispatch('openEdit', { type: 'locations', item: location });
	}
</script>

<div class="card bg-base-200 shadow-xl">
	<div class="card-body">
		<h2 class="card-title text-2xl mb-4">
			<Bed class="w-6 h-6" aria-hidden="true" />
			{$t('adventures.stays_timeline')}
		</h2>

		{#if stayRows.length === 0}
			<p class="text-sm opacity-70">{$t('adventures.no_stays_yet')}</p>
		{:else}
			<div class="space-y-3">
				{#each stayRows as row (row.visit.id)}
					<button
						type="button"
						class="w-full text-left bg-base-300 hover:bg-base-100 transition-colors rounded-lg p-4 flex items-start justify-between gap-3"
						on:click={() => editStay(row.location)}
					>
						<div class="min-w-0">
							<div class="font-semibold text-lg truncate">{row.location.name}</div>
							<div class="text-sm opacity-80">
								{formatDateOnly(row.visit.start_date)} – {formatDateOnly(row.visit.end_date)}
							</div>
							<div class="text-sm mt-1 flex items-center gap-1 opacity-70">
								<MapMarkerDistance class="w-4 h-4 shrink-0" aria-hidden="true" />
								{#if row.distanceKm !== null}
									<span>
										{row.isEstimate ? '≈ ' : ''}{row.distanceKm.toFixed(0)}
										km
									</span>
									{#if row.isEstimate}
										<span class="italic opacity-70">({$t('adventures.distance_estimated')})</span>
									{/if}
								{:else}
									<span class="italic">{$t('adventures.distance_unavailable')}</span>
								{/if}
							</div>
						</div>
						<Pencil class="w-4 h-4 shrink-0 opacity-50" aria-hidden="true" />
					</button>
				{/each}
			</div>
		{/if}
	</div>
</div>
