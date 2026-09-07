<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	const dispatch = createEventDispatcher();
	import { onMount } from 'svelte';
	let modal: HTMLDialogElement;
	import { t } from 'svelte-i18n';
	import type { ContentImage } from '$lib/types';
	import ImageSourceBadge from './ImageSourceBadge.svelte';
	import { defaultImageSource } from '$lib/images';
	import { addToast } from '$lib/toasts';
	export let images: ContentImage[] = [];
	export let initialIndex: number = 0;
	export let name: string = '';
	export let location: string = '';

	let isRotating = false;
	let focalPickMode = false;
	let isSavingFocalPoint = false;

	async function rotateImage(direction: 'cw' | 'ccw') {
		const image = images[currentIndex];
		if (!image?.id || isRotating) return;

		isRotating = true;
		try {
			const res = await fetch(`/api/images/${image.id}/rotate`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ direction })
			});
			if (!res.ok) throw new Error('Failed to rotate image');
			const updated: ContentImage = await res.json();
			applyImageUpdate(updated);
		} catch (error) {
			console.error('Error rotating image:', error);
			addToast('error', $t('adventures.failed_to_rotate_image'));
		} finally {
			isRotating = false;
		}
	}

	async function saveFocalPoint(focalX: number, focalY: number) {
		const image = images[currentIndex];
		if (!image?.id) return;

		isSavingFocalPoint = true;
		try {
			const res = await fetch(`/api/images/${image.id}/`, {
				method: 'PATCH',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ focal_x: focalX, focal_y: focalY })
			});
			if (!res.ok) throw new Error('Failed to save focal point');
			const updated: ContentImage = await res.json();
			applyImageUpdate(updated);
			addToast('success', $t('adventures.cover_position_updated'));
		} catch (error) {
			console.error('Error saving focal point:', error);
			addToast('error', $t('adventures.failed_to_save_cover_position'));
		} finally {
			isSavingFocalPoint = false;
			focalPickMode = false;
		}
	}

	function applyImageUpdate(updated: ContentImage) {
		images = images.map((img) => (img.id === updated.id ? { ...img, ...updated } : img));
		currentImage = images[currentIndex]?.image || '';
		dispatch('imageUpdated', updated);
	}

	function handleImageAreaClick(event: MouseEvent) {
		if (!focalPickMode) return;
		const target = event.currentTarget as HTMLElement;
		const rect = target.getBoundingClientRect();
		const focalX = Math.min(1, Math.max(0, (event.clientX - rect.left) / rect.width));
		const focalY = Math.min(1, Math.max(0, (event.clientY - rect.top) / rect.height));
		saveFocalPoint(focalX, focalY);
	}

	let currentIndex = initialIndex;
	let currentImage = images[currentIndex]?.image || '';

	onMount(() => {
		modal = document.getElementById('my_modal_1') as HTMLDialogElement;
		if (modal) {
			modal.showModal();
		}
		// Set initial values
		updateCurrentSlide(initialIndex);
	});

	function close() {
		dispatch('close');
		if (modal) {
			modal.close();
		}
	}

	function handleKeydown(event: KeyboardEvent) {
		if (event.key === 'Escape') {
			close();
		} else if (event.key === 'ArrowLeft') {
			previousSlide();
		} else if (event.key === 'ArrowRight') {
			nextSlide();
		}
	}

	function handleClickOutside(event: MouseEvent) {
		if (event.target === modal) {
			close();
		}
	}

	function updateCurrentSlide(index: number) {
		currentIndex = index;
		currentImage = images[currentIndex]?.image || '';
	}

	function nextSlide() {
		if (images.length > 0) {
			const nextIndex = (currentIndex + 1) % images.length;
			updateCurrentSlide(nextIndex);
		}
	}

	function previousSlide() {
		if (images.length > 0) {
			const prevIndex = (currentIndex - 1 + images.length) % images.length;
			updateCurrentSlide(prevIndex);
		}
	}

	function goToSlide(index: number) {
		updateCurrentSlide(index);
	}

	// Reactive statement to handle prop changes
	$: if (images.length > 0 && currentIndex >= images.length) {
		updateCurrentSlide(0);
	}

	$: currentImageSource = defaultImageSource(images[currentIndex]?.source);
</script>

<!-- svelte-ignore a11y-no-noninteractive-element-interactions -->
<!-- svelte-ignore a11y-click-events-have-key-events -->
<dialog id="my_modal_1" class="modal backdrop-blur-sm" on:click={handleClickOutside}>
	<!-- svelte-ignore a11y-no-noninteractive-element-interactions -->
	<!-- svelte-ignore a11y-no-noninteractive-tabindex -->
	<div
		class="modal-box w-11/12 max-w-6xl bg-gradient-to-br from-base-100 via-base-100 to-base-200 border border-base-300 shadow-2xl"
		role="dialog"
		on:keydown={handleKeydown}
		tabindex="0"
	>
		{#if images.length > 0 && currentImage}
			<!-- Header -->
			<div
				class="top-0 z-10 bg-base-100/90 backdrop-blur-lg border-b border-base-300 -mx-6 -mt-6 px-6 py-4 mb-6"
			>
				<div class="flex items-center justify-between">
					<div class="flex items-center gap-3">
						<div class="p-2 bg-primary/10 rounded-xl">
							<svg
								class="w-6 h-6 text-primary"
								fill="none"
								stroke="currentColor"
								viewBox="0 0 24 24"
							>
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="2"
									d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
								/>
							</svg>
						</div>
						<div>
							<h1 class="text-2xl font-bold text-primary">
								{name}
							</h1>
							{#if images.length > 1}
								<p class="text-sm text-base-content/60">
									{currentIndex + 1} of {images.length}
									{$t('adventures.images')}
								</p>
							{/if}
						</div>
					</div>

					<!-- Navigation indicators for multiple images -->
					{#if images.length > 1}
						<div class="hidden md:flex items-center gap-2">
							<div class="flex gap-1">
								{#each images as _, index}
									<button
										type="button"
										class="w-2 h-2 rounded-full transition-all {index === currentIndex
											? 'bg-primary'
											: 'bg-base-300 hover:bg-base-400'}"
										aria-label={`Go to image ${index + 1}`}
										on:click={() => goToSlide(index)}
									></button>
								{/each}
							</div>
						</div>
					{/if}

					<!-- Rotate controls -->
					<div class="flex items-center gap-1">
						<button
							type="button"
							class="btn btn-ghost btn-square btn-sm"
							aria-label={$t('adventures.rotate_counter_clockwise')}
							title={$t('adventures.rotate_counter_clockwise')}
							disabled={isRotating}
							on:click={() => rotateImage('ccw')}
						>
							<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="2"
									d="M9 15L4 10m0 0l5-5m-5 5h11a4 4 0 010 8h-1"
								/>
							</svg>
						</button>
						<button
							type="button"
							class="btn btn-ghost btn-square btn-sm"
							aria-label={$t('adventures.rotate_clockwise')}
							title={$t('adventures.rotate_clockwise')}
							disabled={isRotating}
							on:click={() => rotateImage('cw')}
						>
							<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="2"
									d="M15 15l5-5m0 0l-5-5m5 5H9a4 4 0 000 8h1"
								/>
							</svg>
						</button>
						{#if images[currentIndex]?.is_primary}
							<button
								type="button"
								class="btn btn-sm gap-1 {focalPickMode ? 'btn-primary' : 'btn-ghost'}"
								disabled={isSavingFocalPoint}
								title={$t('adventures.set_cover_focal_point_hint')}
								on:click={() => (focalPickMode = !focalPickMode)}
							>
								<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path
										stroke-linecap="round"
										stroke-linejoin="round"
										stroke-width="2"
										d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
									/>
								</svg>
								<span class="hidden lg:inline">{$t('adventures.set_cover_focal_point')}</span>
							</button>
						{/if}
					</div>

					<!-- Close Button -->
					<button
						type="button"
						class="btn btn-ghost btn-square"
						aria-label={$t('about.close')}
						title={$t('about.close')}
						on:click={close}
					>
						<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="2"
								d="M6 18L18 6M6 6l12 12"
							/>
						</svg>
					</button>
				</div>
			</div>

			<!-- Image Display Area -->
			<div class="relative h-[75vh] flex justify-center items-center max-w-full">
				<!-- Previous Button -->
				{#if images.length > 1}
					<button
						type="button"
						class="absolute left-4 top-1/2 -translate-y-1/2 z-20 btn btn-circle btn-primary/80 hover:btn-primary"
						aria-label="Previous image"
						title="Previous image"
						on:click={previousSlide}
					>
						<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="2"
								d="M15 19l-7-7 7-7"
							/>
						</svg>
					</button>
				{/if}

				<!-- Main Image -->
				<div
					class="relative inline-flex max-h-[75vh] max-w-full"
					class:cursor-crosshair={focalPickMode}
					on:click={handleImageAreaClick}
					role="presentation"
				>
					<img
						src={currentImage}
						alt={name}
						class="max-h-[75vh] max-w-full rounded-lg object-contain shadow-lg"
						style="max-width: 100%; max-height: 75vh; object-fit: contain;"
					/>
					<ImageSourceBadge source={currentImageSource} />
					{#if focalPickMode}
						<div
							class="pointer-events-none absolute inset-0 flex items-center justify-center rounded-lg bg-black/20"
						>
							<span class="rounded bg-black/60 px-3 py-1.5 text-sm text-white">
								{$t('adventures.set_cover_focal_point_hint')}
							</span>
						</div>
					{/if}
					{#if images[currentIndex]?.is_primary}
						<div
							class="pointer-events-none absolute h-4 w-4 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-white bg-primary/80 shadow"
							style="left: {(images[currentIndex]?.focal_x ?? 0.5) *
								100}%; top: {(images[currentIndex]?.focal_y ?? 0.5) * 100}%;"
						></div>
					{/if}
				</div>

				<!-- Next Button -->
				{#if images.length > 1}
					<button
						type="button"
						class="absolute right-4 top-1/2 -translate-y-1/2 z-20 btn btn-circle btn-primary/80 hover:btn-primary"
						aria-label="Next image"
						title="Next image"
						on:click={nextSlide}
					>
						<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="2"
								d="M9 5l7 7-7 7"
							/>
						</svg>
					</button>
				{/if}
			</div>

			<!-- Thumbnail Navigation (for multiple images) -->
			{#if images.length > 1}
				<div class="mt-6 px-2">
					<div class="flex gap-2 overflow-x-auto pb-2">
						{#each images as imageData, index}
							<button
								class="flex-shrink-0 w-20 h-20 rounded-lg overflow-hidden border-2 transition-all {index ===
								currentIndex
									? 'border-primary shadow-lg'
									: 'border-base-300 hover:border-base-400'}"
								on:click={() => goToSlide(index)}
							>
								<img src={imageData.image} alt={name} class="w-full h-full object-cover" />
							</button>
						{/each}
					</div>
				</div>
			{/if}

			<!-- Footer -->
			<div
				class="bottom-0 bg-base-100/90 backdrop-blur-lg border-t border-base-300 -mx-6 -mb-6 px-6 py-4 mt-6 rounded-lg"
			>
				<div class="flex items-center justify-between">
					<div class="text-sm text-base-content/60">
						{#if location}
							<span class="flex items-center gap-1">
								<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path
										stroke-linecap="round"
										stroke-linejoin="round"
										stroke-width="2"
										d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"
									/>
									<path
										stroke-linecap="round"
										stroke-linejoin="round"
										stroke-width="2"
										d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"
									/>
								</svg>
								{location}
							</span>
						{/if}
					</div>
					<div class="flex items-center gap-3">
						{#if images.length > 1}
							<div class="text-sm text-base-content/60">
								{$t('adventures.image_modal_navigate')}
							</div>
						{/if}
						<button class="btn btn-primary gap-2" on:click={close}>
							<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="2"
									d="M6 18L18 6M6 6l12 12"
								/>
							</svg>
							{$t('about.close')}
						</button>
					</div>
				</div>
			</div>
		{/if}
	</div>
</dialog>
