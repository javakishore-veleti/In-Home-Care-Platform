from __future__ import annotations

from fastapi import APIRouter, Depends, Response, status

from .schemas import AddressCreate, AddressResponse, AddressUpdate, MemberCreate, MemberProfile, MemberUpdate
from .store import MemberStore

router = APIRouter(tags=['members'])
_store = MemberStore()


def get_store() -> MemberStore:
    return _store


@router.post('/members', response_model=MemberProfile, status_code=status.HTTP_201_CREATED)
def create_member(payload: MemberCreate, store: MemberStore = Depends(get_store)) -> MemberProfile:
    return MemberProfile(**store.create_member(payload))


@router.get('/members/{member_id}', response_model=MemberProfile)
def get_member(member_id: int, store: MemberStore = Depends(get_store)) -> MemberProfile:
    return MemberProfile(**store.get_member(member_id))


@router.patch('/members/{member_id}', response_model=MemberProfile)
def update_member(member_id: int, payload: MemberUpdate, store: MemberStore = Depends(get_store)) -> MemberProfile:
    return MemberProfile(**store.update_member(member_id, payload))


@router.get('/members/{member_id}/addresses', response_model=list[AddressResponse])
def list_addresses(member_id: int, store: MemberStore = Depends(get_store)) -> list[AddressResponse]:
    return [AddressResponse(**row) for row in store.list_addresses(member_id)]


@router.post('/members/{member_id}/addresses', response_model=AddressResponse, status_code=status.HTTP_201_CREATED)
def create_address(member_id: int, payload: AddressCreate, store: MemberStore = Depends(get_store)) -> AddressResponse:
    return AddressResponse(**store.create_address(member_id, payload))


@router.patch('/members/{member_id}/addresses/{address_id}', response_model=AddressResponse)
def update_address(member_id: int, address_id: int, payload: AddressUpdate, store: MemberStore = Depends(get_store)) -> AddressResponse:
    return AddressResponse(**store.update_address(member_id, address_id, payload))


@router.delete('/members/{member_id}/addresses/{address_id}', status_code=status.HTTP_204_NO_CONTENT)
def delete_address(member_id: int, address_id: int, store: MemberStore = Depends(get_store)) -> Response:
    store.delete_address(member_id, address_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch('/members/{member_id}/default-address/{address_id}', response_model=AddressResponse)
def set_default_address(member_id: int, address_id: int, store: MemberStore = Depends(get_store)) -> AddressResponse:
    return AddressResponse(**store.set_default_address(member_id, address_id))
