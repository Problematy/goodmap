import { compressImageToJpeg } from '../../src/utils/imageCompression';

describe('compressImageToJpeg', () => {
    let contextMock;

    beforeEach(() => {
        contextMock = {
            fillStyle: null,
            fillRect: jest.fn(),
            drawImage: jest.fn(),
        };
        HTMLCanvasElement.prototype.getContext = jest.fn(() => contextMock);

        URL.createObjectURL = jest.fn(() => 'blob:mock-url');
        URL.revokeObjectURL = jest.fn();

        // Fires onload asynchronously, like a real Image, with a fixed 4000x3000
        // "photo" size so scaling behavior is deterministic across tests.
        global.Image = class {
            constructor() {
                this.width = 4000;
                this.height = 3000;
            }
            set src(_value) {
                setTimeout(() => this.onload && this.onload());
            }
        };
    });

    afterEach(() => {
        jest.restoreAllMocks();
    });

    // Queues one mock blob size per toBlob() call; the last size repeats if
    // toBlob is called more times than sizes provided.
    const mockToBlobSizes = sizes => {
        let call = 0;
        HTMLCanvasElement.prototype.toBlob = jest.fn((callback, type) => {
            const size = sizes[Math.min(call, sizes.length - 1)];
            call += 1;
            callback(new Blob([new Uint8Array(size)], { type }));
        });
        return () => call;
    };

    it('scales dimensions down to fit maxDimension, preserving aspect ratio', async () => {
        mockToBlobSizes([1000]);
        const file = new File(['x'], 'photo.png', { type: 'image/png' });

        await compressImageToJpeg(file, { maxSizeBytes: 5000, maxDimension: 1920 });

        // 4000x3000 at maxDimension 1920 -> 1920x1440
        expect(contextMock.drawImage).toHaveBeenCalledWith(expect.anything(), 0, 0, 1920, 1440);
    });

    it('never upscales an image already under maxDimension', async () => {
        mockToBlobSizes([1000]);
        global.Image = class {
            constructor() {
                this.width = 800;
                this.height = 600;
            }
            set src(_value) {
                setTimeout(() => this.onload && this.onload());
            }
        };
        const file = new File(['x'], 'photo.png', { type: 'image/png' });

        await compressImageToJpeg(file, { maxSizeBytes: 5000, maxDimension: 1920 });

        expect(contextMock.drawImage).toHaveBeenCalledWith(expect.anything(), 0, 0, 800, 600);
    });

    it('fills the canvas white before drawing, so transparent areas do not turn black', async () => {
        mockToBlobSizes([1000]);
        const file = new File(['x'], 'photo.png', { type: 'image/png' });

        await compressImageToJpeg(file, { maxSizeBytes: 5000 });

        expect(contextMock.fillStyle).toBe('#fff');
        expect(contextMock.fillRect).toHaveBeenCalledWith(0, 0, 1920, 1440);
    });

    it('lowers quality on each retry until the blob fits under maxSizeBytes', async () => {
        const getCallCount = mockToBlobSizes([9000, 7000, 4000]);
        const file = new File(['x'], 'photo.jpg', { type: 'image/jpeg' });

        const result = await compressImageToJpeg(file, { maxSizeBytes: 5000 });

        expect(getCallCount()).toBe(3);
        expect(result.size).toBe(4000);
    });

    it('stops retrying at MIN_QUALITY and returns the best effort even if still oversized', async () => {
        const getCallCount = mockToBlobSizes([100000]);
        const file = new File(['x'], 'photo.jpg', { type: 'image/jpeg' });

        const result = await compressImageToJpeg(file, { maxSizeBytes: 5000 });

        // Quality steps from 0.9 down to just above 0.4 in 0.1 increments: bounded,
        // not infinite, even though every attempt stays oversized.
        expect(getCallCount()).toBeGreaterThan(1);
        expect(getCallCount()).toBeLessThan(10);
        expect(result.size).toBe(100000);
    });

    it('replaces the original extension with .jpg', async () => {
        mockToBlobSizes([1000]);
        const file = new File(['x'], 'vacation-photo.HEIC', { type: 'image/heic' });

        const result = await compressImageToJpeg(file, { maxSizeBytes: 5000 });

        expect(result.name).toBe('vacation-photo.jpg');
        expect(result.type).toBe('image/jpeg');
    });

    it('falls back to "photo.jpg" for a filename with no extension', async () => {
        mockToBlobSizes([1000]);
        const file = new File(['x'], 'noextension', { type: 'image/jpeg' });

        const result = await compressImageToJpeg(file, { maxSizeBytes: 5000 });

        expect(result.name).toBe('noextension.jpg');
    });

    it('rejects when the file cannot be loaded as an image', async () => {
        global.Image = class {
            set src(_value) {
                setTimeout(() => this.onerror && this.onerror());
            }
        };
        const file = new File(['not an image'], 'broken.jpg', { type: 'image/jpeg' });

        await expect(compressImageToJpeg(file, { maxSizeBytes: 5000 })).rejects.toThrow(
            'Failed to load image for compression',
        );
    });

    it('rejects when canvas encoding fails to produce a blob', async () => {
        HTMLCanvasElement.prototype.toBlob = jest.fn(callback => callback(null));
        const file = new File(['x'], 'photo.jpg', { type: 'image/jpeg' });

        await expect(compressImageToJpeg(file, { maxSizeBytes: 5000 })).rejects.toThrow(
            'Image encoding failed',
        );
    });
});
