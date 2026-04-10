/**
 * Shared media helpers for dashboard pages.
 */

/**
 * Return avatar asset path from avatar key.
 * Accepts a predefined key (male/female) or an image URL.
 * @param {string} avatar
 * @returns {string}
 */
export const avatarSource = (avatar) => {
  if (!avatar) return '/images/male.png';
  if (avatar === 'female') return '/images/female.png';
  if (avatar === 'male') return '/images/male.png';

  const value = String(avatar).trim();
  const isUrl = value.startsWith('http://') || value.startsWith('https://');
  const isDataUrl = value.startsWith('data:image/');
  const isBlobUrl = value.startsWith('blob:');

  if (isUrl || isDataUrl || isBlobUrl) {
    return value;
  }

  return '/images/male.png';
};

/**
 * Build an image error handler that swaps to a fallback source.
 * @param {string} fallbackSrc
 * @returns {(event: Event) => void}
 */
export const imageFallbackHandler = (fallbackSrc) => (event) => {
  event.currentTarget.onerror = null;
  event.currentTarget.src = fallbackSrc;
};
