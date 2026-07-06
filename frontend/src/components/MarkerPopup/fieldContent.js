/**
 * Converts a field value to a string representation.
 * Arrays are joined with a comma-space separator; other values are stringified.
 *
 * @param {*} data - Data to convert to string
 * @returns {string} Joined string if array, otherwise the data converted to string
 */
const getContentAsString = data => (Array.isArray(data) ? data.join(', ') : String(data ?? ''));

export default getContentAsString;
