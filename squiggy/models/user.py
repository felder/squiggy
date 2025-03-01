"""
Copyright ©2023. The Regents of the University of California (Regents). All Rights Reserved.

Permission to use, copy, modify, and distribute this software and its documentation
for educational, research, and not-for-profit purposes, without fee and without a
signed licensing agreement, is hereby granted, provided that the above copyright
notice, this paragraph and the following two paragraphs appear in all copies,
modifications, and distributions.

Contact The Office of Technology Licensing, UC Berkeley, 2150 Shattuck Avenue,
Suite 510, Berkeley, CA 94720-1620, (510) 643-7201, otl@berkeley.edu,
http://ipira.berkeley.edu/industry-info for commercial licensing opportunities.

IN NO EVENT SHALL REGENTS BE LIABLE TO ANY PARTY FOR DIRECT, INDIRECT, SPECIAL,
INCIDENTAL, OR CONSEQUENTIAL DAMAGES, INCLUDING LOST PROFITS, ARISING OUT OF
THE USE OF THIS SOFTWARE AND ITS DOCUMENTATION, EVEN IF REGENTS HAS BEEN ADVISED
OF THE POSSIBILITY OF SUCH DAMAGE.

REGENTS SPECIFICALLY DISCLAIMS ANY WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE. THE
SOFTWARE AND ACCOMPANYING DOCUMENTATION, IF ANY, PROVIDED HEREUNDER IS PROVIDED
"AS IS". REGENTS HAS NO OBLIGATION TO PROVIDE MAINTENANCE, SUPPORT, UPDATES,
ENHANCEMENTS, OR MODIFICATIONS.
"""

import random

from cryptography.fernet import Fernet
from flask import current_app as app
from sqlalchemy import and_, or_
from sqlalchemy.dialects.postgresql import ARRAY, ENUM
from sqlalchemy.sql import desc, text
from squiggy import db, std_commit
from squiggy.lib.util import is_admin, is_observer, is_student, is_teaching, isoformat, to_int
from squiggy.models.asset_user import asset_user_table
from squiggy.models.base import Base
from squiggy.models.course import Course
from squiggy.models.course_group_membership import CourseGroupMembership
from squiggy.models.whiteboard_user import whiteboard_user_table

canvas_enrollment_state_type = ENUM(
    'active',
    'completed',
    'inactive',
    'invited',
    'rejected',
    name='enum_users_canvas_enrollment_state',
    create_type=False,
)


class User(Base):
    __tablename__ = 'users'

    id = db.Column(db.Integer, nullable=False, primary_key=True)  # noqa: A003
    bookmarklet_token = db.Column(db.String(32), nullable=False)
    canvas_course_role = db.Column(db.String(255), nullable=False)
    canvas_course_sections = db.Column(ARRAY(db.String(255)))
    canvas_email = db.Column(db.String(255))
    canvas_enrollment_state = db.Column('canvas_enrollment_state', canvas_enrollment_state_type, nullable=False)
    canvas_full_name = db.Column(db.String(255), nullable=False)
    canvas_image = db.Column(db.String(255))
    canvas_user_id = db.Column(db.Integer, nullable=False)
    personal_description = db.Column(db.String(255))
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    points = db.Column(db.Integer, default=0, nullable=False)
    share_points = db.Column(db.Boolean, default=None)
    looking_for_collaborators = db.Column(db.Boolean, default=False, nullable=False)
    last_activity = db.Column(db.DateTime, default=None)

    assets = db.relationship(
        'Asset',
        secondary=asset_user_table,
        backref='users',
        lazy='dynamic',
    )
    course = db.relationship(Course.__name__, back_populates='users')
    whiteboards = db.relationship(
        'Whiteboard',
        back_populates='users',
        secondary=whiteboard_user_table,
    )

    def __init__(
        self,
        canvas_course_role,
        canvas_enrollment_state,
        canvas_full_name,
        canvas_user_id,
        course_id,
        canvas_course_sections=None,
        canvas_email=None,
        canvas_image=None,
        personal_description=None,
        points=0,
        share_points=None,
        looking_for_collaborators=False,
    ):
        self.bookmarklet_token = '%032x' % random.getrandbits(128)
        self.canvas_course_role = canvas_course_role
        self.canvas_course_sections = canvas_course_sections
        self.canvas_email = canvas_email
        self.canvas_enrollment_state = canvas_enrollment_state
        self.canvas_full_name = canvas_full_name
        self.canvas_image = canvas_image
        self.canvas_user_id = canvas_user_id
        self.course_id = course_id
        self.personal_description = personal_description
        self.points = points
        self.share_points = share_points
        self.looking_for_collaborators = looking_for_collaborators

    def __repr__(self):
        return f"""<User id={self.id},
                    bookmarklet_token={self.bookmarklet_token}
                    canvas_course_role={self.canvas_course_role},
                    canvas_course_sections={self.canvas_course_sections},
                    canvas_email={self.canvas_email},
                    canvas_enrollment_state={self.canvas_enrollment_state},
                    canvas_full_name={self.canvas_full_name},
                    canvas_user_id={self.canvas_user_id},
                    course_id={self.course_id},
                    personal_description={self.personal_description},
                    last_activity={self.last_activity},
                    points={self.points},
                    share_points={self.share_points},
                    looking_for_collaborators={self.looking_for_collaborators},
                    created_at={self.created_at},
                    updated_at={self.updated_at}>
                """

    @classmethod
    def create(
            cls,
            canvas_course_role,
            canvas_enrollment_state,
            canvas_full_name,
            canvas_user_id,
            course_id,
            canvas_course_sections=None,
            canvas_email=None,
            canvas_image=None,
            personal_description=None,
    ):
        user = cls(
            canvas_course_role=canvas_course_role,
            canvas_course_sections=canvas_course_sections,
            canvas_email=canvas_email,
            canvas_enrollment_state=canvas_enrollment_state,
            canvas_full_name=canvas_full_name,
            canvas_image=canvas_image,
            canvas_user_id=canvas_user_id,
            course_id=course_id,
            personal_description=personal_description,
        )
        db.session.add(user)
        std_commit()
        return user

    @classmethod
    def find_by_course_id(cls, canvas_user_id, course_id):
        where_clause = and_(cls.course_id == course_id, cls.canvas_user_id == canvas_user_id)
        return cls.query.filter(where_clause).one_or_none()

    @classmethod
    def get_users_by_course_id(cls, course_id, sections=None):
        query = cls.query.filter(
            and_(cls.course_id == course_id, cls.canvas_enrollment_state.in_(['active', 'invited'])),
        )
        if sections:
            query = query.filter(
                or_(
                    cls.canvas_course_sections.overlap(sections),
                    and_(cls.canvas_course_role.not_ilike('%student%'), cls.canvas_course_role.not_ilike('%learner%')),
                ),
            )
        return query.order_by(cls.canvas_full_name).all()

    @classmethod
    def get_leaderboard(cls, course_id, sections=None, sharing_only=True):
        query = cls.query.filter(
            and_(cls.course_id == course_id, cls.canvas_enrollment_state.in_(['active', 'invited'])),
        )
        if sections:
            query = query.filter(
                or_(
                    cls.canvas_course_sections.overlap(sections),
                    and_(cls.canvas_course_role.not_ilike('%student%'), cls.canvas_course_role.not_ilike('%learner%')),
                ),
            )
        if sharing_only:
            query = query.filter_by(share_points=True)
        return query.order_by(desc(cls.points), cls.id).all()

    @classmethod
    def find_by_canvas_user_id(cls, canvas_user_id):
        return cls.query.filter_by(canvas_user_id=canvas_user_id).first()

    @classmethod
    def find_by_id(cls, user_id):
        user_id = to_int(user_id)
        if not user_id:
            return None
        return cls.query.filter_by(id=user_id).first()

    @classmethod
    def find_by_ids(cls, user_ids):
        return cls.query.filter(cls.id.in_(user_ids)).all()

    @classmethod
    def is_sharing_points(cls, user_id):
        sql = 'SELECT share_points FROM users WHERE id = :id'
        result = db.session.execute(text(sql), {'id': user_id}).first()
        return bool(result and result['share_points'])

    @classmethod
    def update_personal_description(cls, personal_description, user_id):
        user = cls.query.filter_by(id=user_id).first()
        user.personal_description = personal_description
        db.session.add(user)
        std_commit()

    @classmethod
    def update_looking_for_collaborators(cls, is_looking_for_collaborators, user_id):
        user = cls.query.filter_by(id=user_id).first()
        user.looking_for_collaborators = True if is_looking_for_collaborators else False
        db.session.add(user)
        std_commit()

    @classmethod
    def update_share_points(cls, share, user_id):
        user = cls.query.filter_by(id=user_id).first()
        user.share_points = True if share else False
        std_commit()

    def to_api_json(self, include_assets=False, include_points=False, include_sharing=False):
        encryption_key = app.config['BOOKMARKLET_ENCRYPTION_KEY']
        group_memberships = CourseGroupMembership.find_by_course_and_user(
            canvas_user_id=self.canvas_user_id,
            course_id=self.course_id,
        )
        api_json = {
            'id': self.id,
            'bookmarkletAuth': Fernet(encryption_key).encrypt(f'{self.id}_{self.course_id}_{self.bookmarklet_token}'.encode()),
            'canvasApiDomain': self.course.canvas_api_domain,
            'canvasCourseId': self.course.canvas_course_id,
            'canvasCourseRole': self.canvas_course_role,
            'canvasCourseSections': self.canvas_course_sections,
            'canvasEmail': self.canvas_email,
            'canvasEnrollmentState': self.canvas_enrollment_state,
            'canvasFullName': self.canvas_full_name,
            'canvasGroupMemberships': [g.to_api_json() for g in group_memberships],
            'canvasImage': self.canvas_image,
            'canvasUserId': self.canvas_user_id,
            'courseId': self.course_id,
            'courseName': self.course.name,
            'personalDescription': self.personal_description,
            'points': self.points,
            'sharePoints': True if self.share_points else False,
            'lookingForCollaborators': self.looking_for_collaborators,
            'whiteboards': [{'id': w.id, 'title': w.title} for w in self.whiteboards],
            'isAdmin': is_admin(self),
            'isObserver': is_observer(self),
            'isStudent': is_student(self),
            'isTeaching': is_teaching(self),
            'lastActivity': isoformat(self.last_activity),
            'createdAt': isoformat(self.created_at),
            'updatedAt': isoformat(self.updated_at),
        }
        if not include_points:
            api_json.pop('points')
        if not include_sharing:
            api_json.pop('sharePoints')
        if include_assets:
            api_json['assets'] = [{'id': asset.id, 'title': asset.title} for asset in self.assets]
        return api_json
