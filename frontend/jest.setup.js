import { TextEncoder, TextDecoder } from 'node:util';
import failOnConsole from 'jest-fail-on-console'

failOnConsole()

global.TextEncoder = TextEncoder;
global.TextDecoder = TextDecoder;

// Platzky's base.html renders this overlay layer on every page. Components that
// portal into it - AppToaster - need it in jsdom too. Created once per test
// file; Testing Library's cleanup only removes containers it created itself.
const overlayRoot = document.createElement('div');
overlayRoot.id = 'overlay-root';
document.body.appendChild(overlayRoot);

global.fetch = jest.fn(() =>
    Promise.resolve({
        json: () => Promise.resolve([]), // Mock response
}),
);
