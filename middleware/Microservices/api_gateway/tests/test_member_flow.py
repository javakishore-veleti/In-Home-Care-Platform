from fastapi.testclient import TestClient

from api_gateway.main import create_app as create_gateway_app
from visit_management_svc.main import create_app as create_visit_app


def test_member_portal_gateway_flow() -> None:
    gateway = TestClient(create_gateway_app())
    visits = TestClient(create_visit_app())

    signup = gateway.post(
        '/api/auth/signup',
        json={
            'email': 'portal.member@example.com',
            'password': 'Password123',
            'first_name': 'Ava',
            'last_name': 'Miles',
            'phone': '555-111-2222',
        },
    )
    assert signup.status_code == 201
    member_id = signup.json()['member']['id']

    signin = gateway.post(
        '/api/auth/signin',
        json={'email': 'portal.member@example.com', 'password': 'Password123'},
    )
    assert signin.status_code == 200
    token = signin.json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}

    profile = gateway.patch('/api/member/profile', json={'phone': '555-000-9999'}, headers=headers)
    assert profile.status_code == 200
    assert profile.json()['phone'] == '555-000-9999'

    address = gateway.post(
        '/api/member/addresses',
        json={
            'label': 'Home',
            'line1': '123 Care Lane',
            'city': 'Austin',
            'state': 'TX',
            'postal_code': '78701',
            'instructions': 'Front desk call on arrival',
            'is_default': True,
        },
        headers=headers,
    )
    assert address.status_code == 201
    address_id = address.json()['id']

    second_address = gateway.post(
        '/api/member/addresses',
        json={
            'label': 'Parents',
            'line1': '456 Family Drive',
            'city': 'Austin',
            'state': 'TX',
            'postal_code': '78702',
            'instructions': 'Use side entrance',
        },
        headers=headers,
    )
    assert second_address.status_code == 201

    address_listing = gateway.get('/api/member/address-directory?query=Austin&page=1&page_size=1', headers=headers)
    assert address_listing.status_code == 200
    assert address_listing.json()['total'] == 2
    assert address_listing.json()['page_size'] == 1
    assert address_listing.json()['total_pages'] == 2

    appointment = gateway.post(
        '/api/member/appointments',
        json={
            'address_id': address_id,
            'service_type': 'Skilled Nursing',
            'service_area': 'Post-discharge support',
            'requested_date': '2026-05-20',
            'requested_time_slot': 'Morning',
            'preferred_hour': '09',
            'preferred_minute': '30',
            'reason': 'Medication management',
            'notes': 'Recent discharge from hospital',
        },
        headers=headers,
    )
    assert appointment.status_code == 201
    appointment_id = appointment.json()['id']
    assert appointment.json()['preferred_hour'] == '09'
    assert appointment.json()['preferred_minute'] == '30'

    visit = visits.post(
        '/visits',
        json={
            'member_id': member_id,
            'appointment_id': appointment_id,
            'notes_summary': 'Follow-up visit completed',
        },
    )
    assert visit.status_code == 201
    visit_id = visit.json()['id']
    visits.post(f'/visits/{visit_id}/documents', json={'title': 'Care Plan', 'doc_type': 'plan', 'summary': 'Adjusted medications'})
    visits.post(f'/visits/{visit_id}/notes', json={'note': 'Patient progressing well', 'author_name': 'Nurse Joy'})
    visits.post(f'/visits/{visit_id}/decisions', json={'decision': 'Schedule weekly check-ins', 'owner_name': 'Dr. Lane'})
    visits.post(f'/visits/{visit_id}/action-items', json={'description': 'Review blood pressure daily', 'status': 'open'})

    listing = gateway.get('/api/member/appointments?query=Skilled&page=1&page_size=5', headers=headers)
    assert listing.status_code == 200
    assert listing.json()['total'] == 1

    typed_listing = gateway.get('/api/member/appointments?service_type=Skilled%20Nursing&page=1&page_size=5', headers=headers)
    assert typed_listing.status_code == 200
    assert typed_listing.json()['total'] == 1

    visit_listing = gateway.get(f'/api/member/appointments/{appointment_id}/visits', headers=headers)
    assert visit_listing.status_code == 200
    assert visit_listing.json()[0]['id'] == visit_id

    documents = gateway.get(f'/api/member/visits/{visit_id}/documents', headers=headers)
    assert documents.status_code == 200
    assert documents.json()[0]['title'] == 'Care Plan'

    chat = gateway.post('/api/member/chat/messages', json={'message': 'Can you help with my appointment?'}, headers=headers)
    assert chat.status_code == 200
    assert len(chat.json()['messages']) == 2
