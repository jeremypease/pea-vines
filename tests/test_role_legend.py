"""The Members & Invites page explains what each role means (it previously
asked admins to set a role with no guidance)."""


def test_members_page_has_role_legend(app, auth_client):
    html = auth_client.get('/admin/users').data.decode()
    assert 'What the roles mean' in html
    # all three roles are described
    for role in ('Member', 'Contributor', 'Admin'):
        assert role in html
    # the distinguishing capabilities are spelled out
    assert 'invite family' in html and 'full control' in html
