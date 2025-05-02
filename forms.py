from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, SubmitField, IntegerField
from wtforms.validators import DataRequired, Length

class ChapterForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(min=1, max=255)])
    content = TextAreaField('Content', validators=[DataRequired()])
    cover_image = FileField('Cover Image', validators=[
        FileAllowed(['jpg', 'png', 'jpeg', 'gif'], 'Images only!')
    ])
    submit = SubmitField('Save Chapter')
    
    def validate_cover_image(self, field):
        # This is just to add debugging information
        if field.data:
            print(f"Validating file: {field.data.filename}")
        else:
            print("No file selected for upload")

class CommentForm(FlaskForm):
    content = TextAreaField('Comment', validators=[DataRequired(), Length(min=1, max=1000)])
    submit = SubmitField('Post Comment')