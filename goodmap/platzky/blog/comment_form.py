from flask_babel import lazy_gettext
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from wtforms.widgets import TextArea


class CommentForm(FlaskForm):
    author_name = StringField(str(lazy_gettext("Name")), validators=[DataRequired()])
    comment = StringField(
        str(lazy_gettext("Type comment here")),
        validators=[DataRequired()],
        widget=TextArea(),
    )
    submit = SubmitField(str(lazy_gettext("Comment")))
