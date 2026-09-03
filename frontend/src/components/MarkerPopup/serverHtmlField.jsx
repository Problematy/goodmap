import React from 'react';
import PropTypes from 'prop-types';

/**
 * Renders the HTML the server produced for a field value.
 *
 * A platzky plugin's shortcode and goodmap's own built-in types (`hyperlink`, `CTA` — see
 * goodmap/field_types.py) both arrive this way, and neither needs a component here. That is
 * the point: a field type is added by teaching the server to render it, not by shipping React.
 *
 * The markup is deliberately not sanitized. It is goodmap's own or comes from an installed
 * plugin package already running arbitrary code in the server process, so filtering would
 * break legitimate markup while blocking nothing such a package could not do more directly —
 * the same trust platzky extends to shortcode output in post content. The obligation in
 * return is to escape the interpolated *data*, which `field_types.py` and `Shortcode.render`
 * both do.
 *
 * This is the innermost stage of the fold, so a field plugin on the same `type` wraps it and
 * cannot replace it — the server always emits `html` for a type it renders, so there is
 * always a seed beneath the wrapper.
 */
const ServerHtmlField = ({ input }) => <span dangerouslySetInnerHTML={{ __html: input.html }} />;

ServerHtmlField.propTypes = {
    input: PropTypes.shape({ html: PropTypes.string.isRequired }).isRequired,
};

export default ServerHtmlField;
