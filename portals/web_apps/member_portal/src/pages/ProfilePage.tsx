import { useCallback, useEffect, useState } from 'react'

import { useAuth } from '../context/AuthContext'
import { api, ApiError } from '../lib/api'
import type { AddressListResponse } from '../types'

const emptyAddress = {
  label: 'Home',
  line1: '',
  line2: '',
  city: '',
  state: '',
  postal_code: '',
  instructions: '',
  is_default: false,
}

const emptyAddressResponse: AddressListResponse = {
  items: [],
  page: 1,
  page_size: 8,
  total: 0,
  total_pages: 1,
}

const ADDRESS_PAGE_SIZE = 8

export function ProfilePage() {
  const { token, member, setSessionState, user } = useAuth()
  const [profileForm, setProfileForm] = useState({
    first_name: member?.first_name ?? '',
    last_name: member?.last_name ?? '',
    email: member?.email ?? '',
    phone: member?.phone ?? '',
    dob: member?.dob ?? '',
    insurance_id: member?.insurance_id ?? '',
  })
  const [addressData, setAddressData] = useState<AddressListResponse>(emptyAddressResponse)
  const [addressForm, setAddressForm] = useState(emptyAddress)
  const [editingAddressId, setEditingAddressId] = useState<number | null>(null)
  const [profileStatusMessage, setProfileStatusMessage] = useState('')
  const [profileError, setProfileError] = useState('')
  const [addressStatusMessage, setAddressStatusMessage] = useState('')
  const [addressError, setAddressError] = useState('')
  const [addressQuery, setAddressQuery] = useState('')
  const [addressPage, setAddressPage] = useState(1)
  const [addressLoading, setAddressLoading] = useState(false)

  useEffect(() => {
    setProfileForm({
      first_name: member?.first_name ?? '',
      last_name: member?.last_name ?? '',
      email: member?.email ?? '',
      phone: member?.phone ?? '',
      dob: member?.dob ?? '',
      insurance_id: member?.insurance_id ?? '',
    })
  }, [member])

  const loadAddresses = useCallback(async (query = addressQuery, page = addressPage) => {
    if (!token) {
      return
    }
    setAddressLoading(true)
    try {
      const params = new URLSearchParams({
        query,
        page: String(page),
        page_size: String(ADDRESS_PAGE_SIZE),
      })
      const nextData = await api.searchAddresses(token, params)
      setAddressData(nextData)
    } catch {
      setAddressError('Unable to load saved addresses.')
    } finally {
      setAddressLoading(false)
    }
  }, [addressPage, addressQuery, token])

  useEffect(() => {
    void loadAddresses()
  }, [loadAddresses])

  const saveProfile = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!token || !member || !user) return
    setProfileError('')
    setProfileStatusMessage('')
    try {
      const updated = await api.updateProfile(token, profileForm)
      setSessionState({ user, member: updated })
      setProfileStatusMessage('Profile settings saved.')
    } catch (err) {
      setProfileError(err instanceof ApiError ? err.message : 'Unable to save profile.')
    }
  }

  const saveAddress = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!token) return
    setAddressError('')
    setAddressStatusMessage('')
    try {
      await (editingAddressId
        ? await api.updateAddress(token, editingAddressId, addressForm)
        : await api.createAddress(token, addressForm))
      setAddressForm(emptyAddress)
      setEditingAddressId(null)
      setAddressQuery('')
      setAddressPage(1)
      await loadAddresses('', 1)
      setAddressStatusMessage('Address saved successfully.')
    } catch (err) {
      setAddressError(err instanceof ApiError ? err.message : 'Unable to save address.')
    }
  }

  const editAddress = (address: AddressListResponse['items'][number]) => {
    setEditingAddressId(address.id)
    setAddressForm({
      label: address.label,
      line1: address.line1,
      line2: address.line2 ?? '',
      city: address.city,
      state: address.state,
      postal_code: address.postal_code,
      instructions: address.instructions ?? '',
      is_default: address.is_default,
    })
  }

  const makeDefault = async (addressId: number) => {
    if (!token) return
    setAddressError('')
    setAddressStatusMessage('')
    try {
      await api.setDefaultAddress(token, addressId)
      await loadAddresses()
      setAddressStatusMessage('Default address updated.')
    } catch (err) {
      setAddressError(err instanceof ApiError ? err.message : 'Unable to update the default address.')
    }
  }

  const removeAddress = async (addressId: number) => {
    if (!token) return
    setAddressError('')
    setAddressStatusMessage('')
    try {
      await api.deleteAddress(token, addressId)
      await loadAddresses()
      setAddressStatusMessage('Address deleted.')
    } catch (err) {
      setAddressError(err instanceof ApiError ? err.message : 'Unable to delete the address.')
    }
  }

  const showingFrom = addressData.total === 0 ? 0 : (addressData.page - 1) * addressData.page_size + 1
  const showingTo = addressData.total === 0 ? 0 : showingFrom + addressData.items.length - 1

  return (
    <div className="stack-xl">
      <section className="card stack-md">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Profile settings</p>
            <h2>Keep your care details up to date</h2>
          </div>
        </div>
        <form className="form-grid two-col" onSubmit={saveProfile}>
          <label>
            First name
            <input value={profileForm.first_name} onChange={(event) => setProfileForm({ ...profileForm, first_name: event.target.value })} />
          </label>
          <label>
            Last name
            <input value={profileForm.last_name} onChange={(event) => setProfileForm({ ...profileForm, last_name: event.target.value })} />
          </label>
          <label>
            Email
            <input type="email" value={profileForm.email} onChange={(event) => setProfileForm({ ...profileForm, email: event.target.value })} />
          </label>
          <label>
            Phone
            <input value={profileForm.phone} onChange={(event) => setProfileForm({ ...profileForm, phone: event.target.value })} />
          </label>
          <label>
            Date of birth
            <input type="date" value={profileForm.dob ?? ''} onChange={(event) => setProfileForm({ ...profileForm, dob: event.target.value })} />
          </label>
          <label>
            Insurance ID
            <input value={profileForm.insurance_id} onChange={(event) => setProfileForm({ ...profileForm, insurance_id: event.target.value })} />
          </label>
          <div className="form-actions full-width">
            <button className="primary-button" type="submit">Save profile</button>
          </div>
        </form>
        {profileStatusMessage ? <p className="success-text">{profileStatusMessage}</p> : null}
        {profileError ? <p className="error-text">{profileError}</p> : null}
      </section>

      <section className="search-surface">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Addresses</p>
            <h2>Find and manage saved addresses</h2>
            <p className="muted">Use search and pagination so home, family, and recurring care addresses stay manageable as the directory grows.</p>
          </div>
        </div>
        <div className="search-input-shell">
          <span className="search-icon">⌕</span>
          <input
            placeholder="Search by label, street, city, state, ZIP, instructions, or address ID"
            value={addressQuery}
            onChange={(event) => {
              setAddressQuery(event.target.value)
              setAddressPage(1)
            }}
          />
          <span className="tag">{addressData.total} addresses</span>
        </div>
      </section>
      <div className="stats-strip compact">
        <div className="metric-card">
          <strong>{addressData.total}</strong>
          <span>Saved addresses</span>
        </div>
        <div className="metric-card">
          <strong>{addressData.items.length}</strong>
          <span>Showing on this page</span>
        </div>
        <div className="metric-card">
          <strong>{addressData.page}</strong>
          <span>Page of {addressData.total_pages}</span>
        </div>
      </div>
      <section className="card stack-md">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Results</p>
            <h2>Your addresses</h2>
            <p className="muted">Review, edit, and set a default address without scrolling through one long list.</p>
          </div>
        </div>
        {addressLoading ? <p className="muted">Loading addresses…</p> : null}
        <div className="address-grid">
          {addressData.items.map((address) => (
            <article className="subcard" key={address.id}>
              <div className="row-between">
                <strong>{address.label}</strong>
                {address.is_default ? <span className="tag">Default</span> : null}
              </div>
              <p>{address.line1}{address.line2 ? `, ${address.line2}` : ''}</p>
              <p>{address.city}, {address.state} {address.postal_code}</p>
              {address.instructions ? <p className="muted">{address.instructions}</p> : null}
              <div className="action-row">
                <button className="text-button" type="button" onClick={() => editAddress(address)}>Edit</button>
                {!address.is_default ? <button className="text-button" type="button" onClick={() => void makeDefault(address.id)}>Make default</button> : null}
                <button className="text-button danger" type="button" onClick={() => void removeAddress(address.id)}>Delete</button>
              </div>
            </article>
          ))}
          {!addressLoading && addressData.items.length === 0 ? (
            <div className="subcard empty-state-card">
              {addressData.total === 0 && addressQuery.trim().length === 0
                ? 'No saved addresses yet.'
                : 'No addresses match your search.'}
            </div>
          ) : null}
        </div>
        <div className="pagination-row">
          <button className="secondary-button" disabled={addressData.page <= 1} onClick={() => setAddressPage(addressData.page - 1)}>Previous</button>
          <span>
            Showing {showingFrom}-{showingTo} of {addressData.total}
          </span>
          <button className="secondary-button" disabled={addressData.page >= addressData.total_pages} onClick={() => setAddressPage(addressData.page + 1)}>Next</button>
        </div>
        {addressStatusMessage ? <p className="success-text">{addressStatusMessage}</p> : null}
        {addressError ? <p className="error-text">{addressError}</p> : null}
      </section>
      <section className="card stack-md">
        <div className="section-heading">
          <div>
            <p className="eyebrow">{editingAddressId ? 'Update address' : 'Add address'}</p>
            <h2>{editingAddressId ? 'Edit address' : 'Add an address'}</h2>
          </div>
        </div>
        <form className="form-grid two-col" onSubmit={saveAddress}>
          <label>
            Label
            <input value={addressForm.label} onChange={(event) => setAddressForm({ ...addressForm, label: event.target.value })} />
          </label>
          <label>
            Address line 1
            <input value={addressForm.line1} onChange={(event) => setAddressForm({ ...addressForm, line1: event.target.value })} required />
          </label>
          <label>
            Address line 2
            <input value={addressForm.line2} onChange={(event) => setAddressForm({ ...addressForm, line2: event.target.value })} />
          </label>
          <label>
            City
            <input value={addressForm.city} onChange={(event) => setAddressForm({ ...addressForm, city: event.target.value })} required />
          </label>
          <label>
            State
            <input value={addressForm.state} onChange={(event) => setAddressForm({ ...addressForm, state: event.target.value })} required />
          </label>
          <label>
            Postal code
            <input value={addressForm.postal_code} onChange={(event) => setAddressForm({ ...addressForm, postal_code: event.target.value })} required />
          </label>
          <label className="full-width">
            Instructions
            <textarea value={addressForm.instructions} onChange={(event) => setAddressForm({ ...addressForm, instructions: event.target.value })} rows={3} />
          </label>
          <label className="checkbox-field full-width">
            <input type="checkbox" checked={addressForm.is_default} onChange={(event) => setAddressForm({ ...addressForm, is_default: event.target.checked })} />
            Make this the default service address
          </label>
          <div className="form-actions full-width">
            <button className="primary-button" type="submit">{editingAddressId ? 'Update address' : 'Add address'}</button>
            {editingAddressId ? <button className="secondary-button" type="button" onClick={() => { setEditingAddressId(null); setAddressForm(emptyAddress) }}>Cancel</button> : null}
          </div>
        </form>
      </section>
    </div>
  )
}
