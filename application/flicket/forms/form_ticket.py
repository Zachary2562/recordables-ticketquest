from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired

# Import your models so we can query priorities and categories
from application.flicket.models.flicket_models import FlicketPriority, FlicketCategory

class TicketForm(FlaskForm):
    title = StringField('Ticket Title', validators=[DataRequired()])
    content = TextAreaField('Content', validators=[DataRequired()])

    priority = SelectField('Priority Level', coerce=str, validators=[DataRequired()])
    category = SelectField('Category', coerce=str, validators=[DataRequired()])
    other_category = StringField('If Other, please specify:')
    submit = SubmitField('Submit')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Dynamically load priorities from DB
        self.priority.choices = [(p.priority, p.priority) for p in FlicketPriority.query.all()]

        # Dynamically load categories from DB, plus "Other"
        category_choices = [(c.category, c.category) for c in FlicketCategory.query.all()]
        category_choices.append(('Other', 'Other'))
        self.category.choices = category_choices
