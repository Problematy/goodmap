// Only the backend's allowed extensions are worth targeting (jpeg/jpg), so we
// always re-encode to JPEG regardless of the source format.
const MIN_QUALITY = 0.4;
const QUALITY_STEP = 0.1;

const loadImage = file =>
    new Promise((resolve, reject) => {
        const objectUrl = URL.createObjectURL(file);
        const img = new Image();
        img.onload = () => {
            URL.revokeObjectURL(objectUrl);
            resolve(img);
        };
        img.onerror = () => {
            URL.revokeObjectURL(objectUrl);
            reject(new Error('Failed to load image for compression'));
        };
        img.src = objectUrl;
    });

const canvasToBlob = (canvas, quality) =>
    new Promise((resolve, reject) => {
        canvas.toBlob(
            blob => (blob ? resolve(blob) : reject(new Error('Image encoding failed'))),
            'image/jpeg',
            quality,
        );
    });

/**
 * Re-encodes an image file as JPEG, scaling it down to fit within maxDimension
 * and lowering quality as needed to land under maxSizeBytes.
 *
 * @param {File} file - Source image file.
 * @param {{maxSizeBytes?: number, maxDimension?: number}} options
 * @returns {Promise<File>} Compressed JPEG file (may still exceed maxSizeBytes
 *   if the image can't be reduced further without going below MIN_QUALITY).
 */
export const compressImageToJpeg = async (file, { maxSizeBytes, maxDimension = 1920 } = {}) => {
    const img = await loadImage(file);

    const scale = Math.min(1, maxDimension / Math.max(img.width, img.height));
    const width = Math.round(img.width * scale);
    const height = Math.round(img.height * scale);

    const canvas = document.createElement('canvas');
    canvas.width = width;
    canvas.height = height;
    canvas.getContext('2d').drawImage(img, 0, 0, width, height);

    let quality = 0.9;
    let blob = await canvasToBlob(canvas, quality);
    while (blob.size > maxSizeBytes && quality > MIN_QUALITY) {
        quality -= QUALITY_STEP;
        blob = await canvasToBlob(canvas, quality);
    }

    const baseName = file.name.replace(/\.[^./\\]+$/, '') || 'photo';
    return new File([blob], `${baseName}.jpg`, { type: 'image/jpeg' });
};
