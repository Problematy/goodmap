from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from wtforms.widgets import TextArea
from flask_babel import lazy_gettext


class CommentForm(FlaskForm):
    author_name = StringField(lazy_gettext('Name'), validators=[DataRequired()])
    comment = StringField(lazy_gettext('Type comment here'), validators=[DataRequired()], widget=TextArea())
    submit = SubmitField(lazy_gettext('Comment'))
