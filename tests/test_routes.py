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

from squiggy.models.user import User
from tests.util import override_config


class TestRoutes:

    def test_bookmarklet_auth(self, app, client):
        """Verify that bookmarklet source files are properly formatted."""
        with override_config(app, 'VUE_LOCALHOST_BASE_URL', 'http://localhost:8080'):
            student = User.find_by_canvas_user_id('8765432')
            bookmarklet_auth = student.to_api_json()['bookmarkletAuth']
            url_path = '/assets'
            response = client.get(f'{url_path}?_b={bookmarklet_auth}')
            assert response.status_code == 302
            assert response.location.startswith(f"{app.config['VUE_LOCALHOST_BASE_URL']}{url_path}")

    def test_front_end_route_redirect(self, app, client):
        """Server-side redirect to Vue."""
        with override_config(app, 'VUE_LOCALHOST_BASE_URL', 'http://localhost:8080'):
            url_path = '/assets'
            response = client.get(url_path)
            assert response.status_code == 302
            assert response.location.startswith(f"{app.config['VUE_LOCALHOST_BASE_URL']}{url_path}")
