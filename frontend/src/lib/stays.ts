import type { Location, Visit } from './types';

export type StayRow = {
	location: Location;
	visit: Visit;
	distanceKm: number | null;
	isEstimate: boolean;
};

// Approximate straight-line distance between two coordinates, in km.
function haversineKm(lat1: number, lon1: number, lat2: number, lon2: number): number {
	const R = 6371;
	const dLat = ((lat2 - lat1) * Math.PI) / 180;
	const dLon = ((lon2 - lon1) * Math.PI) / 180;
	const a =
		Math.sin(dLat / 2) ** 2 +
		Math.cos((lat1 * Math.PI) / 180) * Math.cos((lat2 * Math.PI) / 180) * Math.sin(dLon / 2) ** 2;
	return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

export type HomeLocation = { latitude: number; longitude: number } | null | undefined;

/**
 * One row per visit across all of a collection's locations, sorted by start
 * date (undated visits sort last, by location name), with a distance
 * traveled per stay: a user-entered override wins; otherwise, if the visit
 * is explicitly marked `linked_to_previous` (same trip, no return home in
 * between), it's approximated from the previous stay's coordinates; failing
 * that (including for a normal, unlinked visit) it falls back to the
 * straight-line distance from the user's home location when that's set.
 */
export function buildStayRows(locations: Location[], home?: HomeLocation): StayRow[] {
	const sortedStays = (locations || [])
		.flatMap((location) => (location.visits || []).map((visit) => ({ location, visit })))
		.sort((a, b) => {
			if (!a.visit.start_date && !b.visit.start_date) {
				return a.location.name.localeCompare(b.location.name);
			}
			if (!a.visit.start_date) return 1;
			if (!b.visit.start_date) return -1;
			return a.visit.start_date.localeCompare(b.visit.start_date);
		});

	return sortedStays.map(({ location, visit }, index): StayRow => {
		if (visit.distance_km !== null && visit.distance_km !== undefined) {
			return { location, visit, distanceKm: visit.distance_km, isEstimate: false };
		}

		if (location.latitude != null && location.longitude != null) {
			const previous = visit.linked_to_previous ? sortedStays[index - 1]?.location : null;
			if (previous && previous.latitude != null && previous.longitude != null) {
				const km = haversineKm(
					previous.latitude,
					previous.longitude,
					location.latitude,
					location.longitude
				);
				return { location, visit, distanceKm: km, isEstimate: true };
			}

			if (home) {
				const km = haversineKm(home.latitude, home.longitude, location.latitude, location.longitude);
				return { location, visit, distanceKm: km, isEstimate: true };
			}
		}

		return { location, visit, distanceKm: null, isEstimate: false };
	});
}
