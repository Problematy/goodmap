report_location_schema = {
    'type': 'object',
    'properties': {
        'location': {
            'type': 'array',
        },
        'name':{
            'type' : 'string',
        },
        'type':{
            'type' : 'string',
        }
    },
    'required': ['location', 'name', 'type'],
}