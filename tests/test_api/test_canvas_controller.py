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


class TestLtiCartridgeController:
    """LTI cartridge API."""

    def test_asset_library_xml(self, client):
        """Valid cartridge XML contains Asset Library launch URL."""
        response = client.get('/lti/cartridge/asset_library.xml')
        assert response.status_code == 200
        assert 'application/xml' in response.content_type
        assert '/api/auth/lti_launch/asset_library' in str(response.data)

    def test_engagement_index_xml(self, client):
        """Valid cartridge XML contains Engagement Index launch URL."""
        response = client.get('/lti/cartridge/engagement_index.xml')
        assert response.status_code == 200
        assert 'application/xml' in response.content_type
        assert '/api/auth/lti_launch/engagement_index' in str(response.data)

    def test_impact_studio_xml(self, client):
        """Valid cartridge XML contains Whiboards launch URL."""
        response = client.get('/lti/cartridge/impact_studio.xml')
        assert response.status_code == 200
        assert 'application/xml' in response.content_type
        assert '/api/auth/lti_launch/impact_studio' in str(response.data)

    def test_whiteboards_xml(self, client):
        """Valid cartridge XML contains Whiboards launch URL."""
        response = client.get('/lti/cartridge/whiteboards.xml')
        assert response.status_code == 200
        assert 'application/xml' in response.content_type
        assert '/api/auth/lti_launch/whiteboards' in str(response.data)
