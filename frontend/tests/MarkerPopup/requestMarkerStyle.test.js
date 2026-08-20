import requestMarkerStyle from '../../src/components/MarkerPopup/requestMarkerStyle';
import httpService from '../../src/services/http/httpService';
import useMarkerStylesStore from '../../src/components/Map/store/markerStyles.store';

jest.mock('../../src/services/http/httpService');

describe('requestMarkerStyle', () => {
    beforeEach(() => {
        jest.useFakeTimers();
        jest.clearAllMocks();
        useMarkerStylesStore.setState({ stylesByUuid: {} });
        globalThis.MARKER_STYLES = { icon_field: 'pointType' }; // eslint-disable-line camelcase -- matches backend API schema property name
        delete globalThis.FEATURE_FLAGS;
    });

    afterEach(() => {
        jest.runOnlyPendingTimers();
        jest.useRealTimers();
        delete globalThis.MARKER_STYLES;
        delete globalThis.FEATURE_FLAGS;
    });

    it('still fetches when marker styling is not configured, for has_remark', () => {
        globalThis.MARKER_STYLES = {};
        httpService.getMarkerStyles.mockResolvedValue({ 'uuid-1': { has_remark: true } }); // eslint-disable-line camelcase -- matches backend API schema property name
        requestMarkerStyle('uuid-1');
        jest.runAllTimers();
        expect(httpService.getMarkerStyles).toHaveBeenCalledWith(['uuid-1']);
    });

    it('does nothing when server-side clustering is enabled', () => {
        globalThis.FEATURE_FLAGS = { USE_SERVER_SIDE_CLUSTERING: true };
        requestMarkerStyle('uuid-1');
        jest.runAllTimers();
        expect(httpService.getMarkerStyles).not.toHaveBeenCalled();
    });

    it('batches uuids requested within the debounce window into one request', async () => {
        httpService.getMarkerStyles.mockResolvedValue({ 'uuid-1': { pointType: 'a' } });
        requestMarkerStyle('uuid-1');
        requestMarkerStyle('uuid-2');
        jest.runAllTimers();
        await Promise.resolve();
        expect(httpService.getMarkerStyles).toHaveBeenCalledTimes(1);
        expect(httpService.getMarkerStyles).toHaveBeenCalledWith(['uuid-1', 'uuid-2']);
    });

    it('merges results into the store, defaulting unmatched uuids to {}', async () => {
        httpService.getMarkerStyles.mockResolvedValue({ 'uuid-1': { pointType: 'a' } });
        requestMarkerStyle('uuid-1');
        requestMarkerStyle('uuid-2');
        jest.runAllTimers();
        await Promise.resolve();
        expect(useMarkerStylesStore.getState().stylesByUuid).toEqual({
            'uuid-1': { pointType: 'a' },
            'uuid-2': {},
        });
    });

    it('does not re-request a uuid already known, even with no matching styling', () => {
        useMarkerStylesStore.setState({ stylesByUuid: { 'uuid-1': {} } });
        requestMarkerStyle('uuid-1');
        jest.runAllTimers();
        expect(httpService.getMarkerStyles).not.toHaveBeenCalled();
    });
});
