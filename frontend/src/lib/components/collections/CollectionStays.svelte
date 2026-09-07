<script lang="ts">
	import type { Collection, Location, Visit } from '$lib/types';
	import { createEventDispatcher } from 'svelte';
	import { t } from 'svelte-i18n';
	import Bed from '~icons/mdi/bed';
	import MapMarkerDistance from '~icons/mdi/map-marker-distance';
	import Pencil from '~icons/mdi/pencil';

	const dispatch = createEventDispatcher();

	export let collection: Collection;

	// Approximate straight-line distance between two coordinates, in km.
	function haversineKm(lat1: number, lon1: number, lat2: number, lon2: number): number {
		const R = 6371;
		const dLat = ((lat2 - lat1) * Math.PI) / 180;
		const dLon = ((lon2 - lon1) * Math.PI) / 180;
		const a =
			Math.sin(dLat / 2) ** 2 +
			Math.cos((lat1 * Math.PI) / 180) *
				Math.cos((lat2 * Math.PI) / 180) *
				Math.sin(dLon / 2) ** 2;
		return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
	}

	function formatDateOnly(dateString: string | null): string {
		if (!dateString) return '';
		return dateString.split('T')[0];
	}

	type StayRow = {
		location: Location;
		visit: Visit;
		distanceKm: number | null;
		isEstimate: boolean;
	};

	// One row per visit (a location visited more than once yields multiple
	// rows), sorted by start date; undated visits sort last, by location name.
	$: sortedStays = ((collection?.locations || []) as Location[])
		.flatMap((location) => (location.visits || []).map((visit) => ({ location, visit })))
		.sort((a, b) => {
			if (!a.visit.start_date && !b.visit.start_date) {
				return a.location.name.localeCompare(b.location.name);
			}
			if (!a.visit.start_date) return 1;
			if (!b.visit.start_date) return -1;
			return a.visit.start_date.localeCompare(b.visit.start_date);
		});

	// Distance traveled per visit: a user-entered override wins; otherwise
	// it's approximated from the straight-line distance to the previous
	// stay's location when both have coordinates. This is the first step
	// toward a full itinerary (linked places with per-leg distances) — for
	// now stays are just ordered by date rather than explicitly linked.
	$: stayRows = sortedStays.map(({ location, visit }, index): StayRow => {
		if (visit.distance_km !== null && visit.distance_km !== undefined) {
			return { location, visit, distanceKm: visit.distance_km, isEstimate: false };
		}

		const previous = sortedStays[index - 1]?.location;
		if (
			previous &&
			previous.latitude != null &&
			previous.longitude != null &&
			location.latitude != null &&
			location.longitude != null
		) {
			const km = haversineKm(
				previous.latitude,
				previous.longitude,
				location.latitude,
				location.longitude
			);
			return { location, visit, distanceKm: km, isEstimate: true };
		}

		return { location, visit, distanceKm: null, isEstimate: false };
	});

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
