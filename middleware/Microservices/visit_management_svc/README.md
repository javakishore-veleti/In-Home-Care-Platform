# visit_management_svc

Visit lifecycle: create (from appointment event), assign field staff, update status (scheduled → in_progress → completed → reviewed), list upcoming/past visits for a member or a staff member. Owns the `visits` MongoDB collection.

**Tech:** FastAPI, PyMongo, Pytest.
