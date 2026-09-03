import React from 'react';
import PropTypes from 'prop-types';

/**
 * Renders the HTML the server produced for a field value.
 *
 * Two things arrive this way. A platzky plugin's shortcode renders its own field, and
 * goodmap renders its own first-party types (`hyperlink`, `CTA` — see
 * goodmap/field_types.py). Neither needs a component here, which is the point: a field
 * type is added by teaching the server to render it, not by shipping React.
 *
 * The markup is not sanitized, and deliberately so. It is either goodmap's own or comes
 * from an installed plugin package, which already runs arbitrary code in the server
 * process — the same trust platzky extends to shortcode output in post content.
 * Sanitizing would filter nothing such a package could not do more directly, while
 * breaking legitimate markup. The obligation in return is to escape the *data* being
 * interpolated, which is untrusted; `field_types.py` and `Shortcode.render` both do.
 *
 * This is the innermost stage of the fold, so a field plugin attached to the same `type`
 * wraps it and cannot replace it. That is what stops a plugin taking over a first-party
 * type: the server always emits `html` for one, so there is always a seed beneath the
 * wrapper.
 */
const ServerHtmlField = ({ input }) => <span dangerouslySetInnerHTML={{ __html: input.html }} />;

ServerHtmlField.propTypes = {
    input: PropTypes.shape({ html: PropTypes.string.isRequired }).isRequired,
};

export default ServerHtmlField;
