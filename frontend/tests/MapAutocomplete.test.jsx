import React from 'react';
import { render, screen, act, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import AutoComplete from '../src/components/common/Autocomplete';
import '@testing-library/jest-dom/extend-expect';

const exampleMapResponseJson = [
    {
        place_id: 293025836,
        licence: 'Data © OpenStreetMap contributors, ODbL 1.0. http://osm.org/copyright',
        osm_type: 'relation',
        osm_id: 104778,
        lat: '39.4203978',
        lon: '-84.180897',
        class: 'boundary',
        type: 'administrative',
        place_rank: 12,
        importance: 0.5226241945245353,
        addresstype: 'county',
        name: 'Warren County',
        display_name: 'Warren County, Ohio, United States',
        boundingbox: ['39.2550740', '39.5894696', '-84.3652334', '-83.9769126'],
    },
    {
        place_id: 294425830,
        licence: 'Data © OpenStreetMap contributors, ODbL 1.0. http://osm.org/copyright',
        osm_type: 'relation',
        osm_id: 240095,
        lat: '37.3012246',
        lon: '-81.6909425',
        class: 'boundary',
        type: 'administrative',
        place_rank: 16,
        importance: 0.38472319726874576,
        addresstype: 'city',
        name: 'War',
        display_name: 'War, McDowell County, West Virginia, United States',
        boundingbox: ['37.2880250', '37.3138570', '-81.6973420', '-81.6653360'],
    },
    {
        place_id: 188384948,
        licence: 'Data © OpenStreetMap contributors, ODbL 1.0. http://osm.org/copyright',
        osm_type: 'relation',
        osm_id: 1759757,
        lat: '34.3191345',
        lon: '68.3360426',
        class: 'boundary',
        type: 'administrative',
        place_rank: 8,
        importance: 0.5060170723829673,
        addresstype: 'state',
        name: 'Maidan Wardak Province',
        display_name: 'Maidan Wardak Province, Afghanistan',
        boundingbox: ['33.6808164', '34.7976739', '67.2151689', '68.9699791'],
    },
    {
        place_id: 140246107,
        licence: 'Data © OpenStreetMap contributors, ODbL 1.0. http://osm.org/copyright',
        osm_type: 'node',
        osm_id: 9457970456,
        lat: '53.194951',
        lon: '5.5151261',
        class: 'place',
        type: 'hamlet',
        place_rank: 20,
        importance: 0.2792976647232802,
        addresstype: 'hamlet',
        name: 'War',
        display_name: 'War, Franeker, Waadhoeke, Frisia, Netherlands, 8802 PH, Netherlands',
        boundingbox: ['53.1749510', '53.2149510', '5.4951261', '5.5351261'],
    },
    {
        place_id: 213503336,
        licence: 'Data © OpenStreetMap contributors, ODbL 1.0. http://osm.org/copyright',
        osm_type: 'node',
        osm_id: 1195164092,
        lat: '20.9143438',
        lon: '74.688063',
        class: 'place',
        type: 'village',
        place_rank: 19,
        importance: 0.27501,
        addresstype: 'village',
        name: 'War',
        display_name: 'War, Dhule Taluka, Dhule District, Maharashtra, India',
        boundingbox: ['20.8943438', '20.9343438', '74.6680630', '74.7080630'],
    },
];

describe('should autocomplete work correctly', () => {
    beforeEach(async () => {
        jest.spyOn(global, 'fetch').mockResolvedValue({
            json: jest.fn().mockResolvedValue(exampleMapResponseJson),
        });
        await act(async () => {
            render(<AutoComplete onClick={() => {}} />);
        });
    });

    it('should render proper list', async () => {
        const input = screen.getByRole('textbox');

        await act(async () => {
            await userEvent.type(input, 'War');
        });

        expect(screen.getByText('Warren County, Ohio, United States')).toBeInTheDocument();
    });

    afterEach(() => {
        jest.restoreAllMocks();
    });
});
