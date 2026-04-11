from fastapi.testclient import TestClient

from visit_management_svc.main import create_app


def test_visit_routes_support_artifact_crud() -> None:
    client = TestClient(create_app())

    visit = client.post('/visits', json={'member_id': 1, 'appointment_id': 11, 'notes_summary': 'Initial visit'})
    assert visit.status_code == 201
    visit_id = visit.json()['id']

    note = client.post(f'/visits/{visit_id}/notes', json={'note': 'Vitals stable', 'author_name': 'Nurse Joy'})
    decision = client.post(f'/visits/{visit_id}/decisions', json={'decision': 'Continue therapy', 'owner_name': 'Dr. Lane'})
    action = client.post(f'/visits/{visit_id}/action-items', json={'description': 'Hydrate daily', 'status': 'open'})
    document = client.post(f'/visits/{visit_id}/documents', json={'title': 'Visit Summary', 'doc_type': 'summary', 'summary': 'Patient improving'})

    assert note.status_code == 201
    assert decision.status_code == 201
    assert action.status_code == 201
    assert document.status_code == 201

    notes = client.get(f'/visits/{visit_id}/notes')
    assert notes.status_code == 200
    assert notes.json()[0]['note'] == 'Vitals stable'
