export const MODEL_UPDATED_EVENT = 'ml:model-updated';

export function emitModelUpdated(detail = {}) {
  if (typeof window === 'undefined') return;
  window.dispatchEvent(new CustomEvent(MODEL_UPDATED_EVENT, {
    detail: {
      timestamp: Date.now(),
      ...detail,
    },
  }));
}
