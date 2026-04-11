import { useEffect, useMemo, useState } from 'react'

import { useAuth } from '../context/AuthContext'
import { api, ApiError } from '../lib/api'
import type { Address } from '../types'

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
  const [addresses, setAddresses] = useState<Address[]>([])
  const [addressForm, setAddressForm] = useState(emptyAddress)
  const [editingAddressId, setEditingAddressId] = useState<number | null>(null)
  const [statusMessage, setStatusMessage] = useState('')
  const [error, setError] = useState('')

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

  useEffect(() => {
    if (!token) {
      return
    }
    void api.listAddresses(token).then(setAddresses).catch(() => setError('Unable to load addresses.'))
  }, [token])

  const defaultAddress = useMemo(() => addresses.find((address) => address.is_default), [addresses])

  const saveProfile = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!token || !member || !user) return
    setError('')
    setStatusMessage('')
    try {
      const updated = await api.updateProfile(token, profileForm)
      setSessionState({ user, member: updated })
      setStatusMessage('Profile settings saved.')
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Unable to save profile.')
    }
  }

  const saveAddress = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!token) return
    setError('')
    try {
      const nextAddress = editingAddressId
        ? await api.updateAddress(token, editingAddressId, addressForm)
        : await api.createAddress(token, addressForm)
      let nextAddresses = editingAddressId
        ? addresses.map((address) => (address.id === editingAddressId ? nextAddress : address))
        : [...addresses, nextAddress]
      if (nextAddress.is_default) {
        nextAddresses = nextAddresses.map((address) => ({ ...address, is_default: address.id === nextAddress.id }))
      }
      setAddresses(nextAddresses)
      setAddressForm(emptyAddress)
      setEditingAddressId(null)
      setStatusMessage('Address saved successfully.')
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Unable to save address.')
    }
  }

  const editAddress = (address: Address) => {
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
    const nextDefault = await api.setDefaultAddress(token, addressId)
    setAddresses(addresses.map((address) => ({ ...address, is_default: address.id === nextDefault.id })))
  }

  const removeAddress = async (addressId: number) => {
    if (!token) return
    await api.deleteAddress(token, addressId)
    const refreshed = await api.listAddresses(token)
    setAddresses(refreshed)
  }

  return (
    <div className="stack-xl">
      <section className="card stack-md">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Profile settings</p>
            <h2>Keep your care details up to date</h2>
          </div>
          {defaultAddress ? <span className="tag">Default address: {defaultAddress.label}</span> : null}
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
        {statusMessage ? <p className="success-text">{statusMessage}</p> : null}
        {error ? <p className="error-text">{error}</p> : null}
      </section>

      <section className="card stack-md">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Service locations</p>
            <h2>Manage multiple saved addresses</h2>
          </div>
        </div>
        <div className="address-grid">
          {addresses.map((address) => (
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
