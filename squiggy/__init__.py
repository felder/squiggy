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

from decorator import decorator
from flask import current_app as app
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError

__version__ = '5.1'

db = SQLAlchemy()


def std_commit(allow_test_environment=False):
    """Commit failures in SQLAlchemy must be explicitly handled.

    This function follows the suggested default, which is to roll back and close the active session, letting the pooled
    connection start a new transaction cleanly. WARNING: Session closure will invalidate any in-memory DB entities. Rows
    will have to be reloaded from the DB to be read or updated.
    """
    # Give a hoot, don't pollute.
    if app.config['TESTING'] and not allow_test_environment:
        # When running tests, session flush generates id and timestamps that would otherwise show up during a commit.
        db.session.flush()
        return
    successful_commit = False
    try:
        db.session.commit()
        successful_commit = True
    except SQLAlchemyError:
        db.session.rollback()
        raise
    finally:
        if not successful_commit:
            db.session.close()


def mock_open_file(path_to_file):
    @decorator
    def _open_file(func, *args, **kw):
        if app.config['SQUIGGY_ENV'] == 'test':
            return open(f'{_get_fixtures_path()}/{path_to_file}', 'r')
        else:
            return func(*args, **kw)
    return _open_file


def mock(mock_object):
    @decorator
    def _get_object(func, *args, **kw):
        return mock_object if app.config['SQUIGGY_ENV'] == 'test' else func(*args, **kw)
    return _get_object


def _get_fixtures_path():
    return app.config.get('FIXTURES_PATH') or (app.config['BASE_DIR'] + '/fixtures')
