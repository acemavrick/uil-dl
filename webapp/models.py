from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Contest(db.Model):
    """Represents a contest entry in the database."""
    __tablename__ = 'contests'

    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String, nullable=False)
    level = db.Column(db.String, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    level_sort = db.Column(db.Integer, nullable=True)  # db may lack this col in older versions
    pdf_link = db.Column(db.String, nullable=True)
    zip_link = db.Column(db.String, nullable=True)
    other_link = db.Column(db.String, nullable=True)

    # Define the unique constraint and index from your original DDL
    __table_args__ = (
        db.UniqueConstraint('subject', 'level', 'year', name='uq_contest'),
        db.Index('idx_contests_subject_level_year', 'subject', 'level', 'year'),
        db.Index('idx_contests_subject_levelsort_year', 'subject', 'level_sort', 'year')
    )

    def __repr__(self):
        return f'<Contest {self.subject} {self.level} {self.year}>' 