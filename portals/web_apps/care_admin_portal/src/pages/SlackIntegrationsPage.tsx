import { useEffect, useState } from 'react'

import { useAuth } from '../context/AuthContext'
import { api } from '../lib/api'
import type { SlackChannelRow, SlackChannelsResponse } from '../types'

const KNOWN_EVENT_TYPES = [
  { value: 'appointment.booked', label: 'New appointment requests' },
]

export function SlackIntegrationsPage() {
  const { token } = useAuth()
  const [data, setData] = useState<SlackChannelsResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [busyId, setBusyId] = useState<string | null>(null)
  const [actionMsg, setActionMsg] = useState<string | null>(null)

  async function load() {
    if (!token) return
    setLoading(true)
    try {
      const res = await api.listSlackChannels(token)
      setData(res)
      setError(null)
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : 'Failed to load Slack channels.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token])

  async function inviteBot(channel: SlackChannelRow) {
    if (!token) return
    setBusyId(channel.id)
    setActionMsg(null)
    try {
      const res = await api.inviteBotToChannel(token, channel.id)
      if (res.ok) {
        setActionMsg(`Bot invited to #${channel.name}.`)
      } else {
        setActionMsg(`Slack returned: ${res.error ?? 'unknown'}`)
      }
      await load()
    } catch (exc) {
      setActionMsg(exc instanceof Error ? exc.message : 'Invite failed.')
    } finally {
      setBusyId(null)
    }
  }

  async function integrate(channel: SlackChannelRow, eventType: string) {
    if (!token) return
    setBusyId(channel.id)
    setActionMsg(null)
    try {
      await api.upsertSlackIntegration(token, {
        slack_channel_id: channel.id,
        slack_channel_name: channel.name,
        event_type: eventType,
      })
      setActionMsg(`#${channel.name} now receives "${eventType}" notifications.`)
      await load()
    } catch (exc) {
      setActionMsg(exc instanceof Error ? exc.message : 'Integration failed.')
    } finally {
      setBusyId(null)
    }
  }

  async function toggle(integrationId: number, channel: SlackChannelRow, enabled: boolean) {
    if (!token) return
    setBusyId(channel.id)
    setActionMsg(null)
    try {
      await api.toggleSlackIntegration(token, integrationId, enabled)
      setActionMsg(`Integration ${enabled ? 'enabled' : 'disabled'} for #${channel.name}.`)
      await load()
    } catch (exc) {
      setActionMsg(exc instanceof Error ? exc.message : 'Toggle failed.')
    } finally {
      setBusyId(null)
    }
  }

  async function remove(integrationId: number, channel: SlackChannelRow) {
    if (!token) return
    setBusyId(channel.id)
    setActionMsg(null)
    try {
      await api.deleteSlackIntegration(token, integrationId)
      setActionMsg(`Integration removed from #${channel.name}.`)
      await load()
    } catch (exc) {
      setActionMsg(exc instanceof Error ? exc.message : 'Remove failed.')
    } finally {
      setBusyId(null)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-[#1A2B3C]">Slack Integrations</h2>
        <p className="text-sm text-[#3D5A73] mt-1">
          Map domain events (e.g. new appointment requests) to a Slack channel. Changes apply
          to slack_svc on the next message — no restart needed.
          {data?.team && <span className="ml-2">Workspace: <strong>{data.team}</strong></span>}
        </p>
      </div>

      {actionMsg && (
        <div className="text-xs bg-[#0D7377]/10 border border-[#0D7377]/20 text-[#0D7377] rounded px-3 py-2">
          {actionMsg}
        </div>
      )}
      {error && (
        <div className="text-sm text-[#D32F2F] bg-[#FCEAEA] border border-[#D32F2F]/20 rounded px-3 py-2">
          {error}
        </div>
      )}
      {loading && <p className="text-sm text-[#3D5A73]">Loading channels...</p>}
      {!loading && data && data.channels.length === 0 && (
        <div className="bg-white rounded-xl shadow p-8 text-center text-sm text-[#3D5A73]">
          No channels visible to the bot. Either the bot has not been added to any channel yet, or
          the SLACK_BOT_TOKEN env var is not set on api_gateway.
        </div>
      )}

      {data && data.channels.length > 0 && <FanoutBanner channels={data.channels} />}

      {data && data.channels.length > 0 && (
        <div className="bg-white rounded-xl shadow overflow-hidden">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-[#0D7377] text-white text-sm">
                <th className="px-4 py-3">Channel</th>
                <th className="px-4 py-3">Bot in channel?</th>
                <th className="px-4 py-3">Integrations</th>
                <th className="px-4 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {data.channels.map((channel) => (
                <tr key={channel.id} className="border-b border-[#0D7377]/10 text-sm align-top">
                  <td className="px-4 py-3">
                    <div className="font-semibold text-[#1A2B3C]">
                      #{channel.name}
                      {channel.is_private && <span className="ml-2 text-[10px] uppercase text-[#3D5A73]">private</span>}
                    </div>
                    <div className="text-[10px] font-mono text-[#3D5A73]">{channel.id}</div>
                  </td>
                  <td className="px-4 py-3">
                    {channel.is_member ? (
                      <span className="px-2 py-1 rounded text-xs font-bold text-white uppercase bg-[#2D8A4E]">
                        member
                      </span>
                    ) : (
                      <span className="px-2 py-1 rounded text-xs font-bold text-white uppercase bg-[#3D5A73]">
                        not in
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    {channel.integrations.length === 0 ? (
                      <span className="text-xs text-[#3D5A73]">none</span>
                    ) : (
                      <ul className="space-y-1">
                        {channel.integrations.map((integ) => (
                          <li key={integ.id} className="flex items-center gap-2">
                            <code className="text-[11px]">{integ.event_type}</code>
                            <span
                              className={`px-1.5 py-0.5 rounded text-[10px] font-bold text-white uppercase ${
                                integ.enabled ? 'bg-[#2D8A4E]' : 'bg-[#3D5A73]'
                              }`}
                            >
                              {integ.enabled ? 'on' : 'off'}
                            </span>
                            <button
                              type="button"
                              disabled={busyId === channel.id}
                              onClick={() => toggle(integ.id, channel, !integ.enabled)}
                              className="text-[10px] text-[#0D7377] hover:underline disabled:opacity-50"
                            >
                              {integ.enabled ? 'disable' : 'enable'}
                            </button>
                            <button
                              type="button"
                              disabled={busyId === channel.id}
                              onClick={() => remove(integ.id, channel)}
                              className="text-[10px] text-[#D32F2F] hover:underline disabled:opacity-50"
                            >
                              remove
                            </button>
                          </li>
                        ))}
                      </ul>
                    )}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <div className="flex flex-col items-end gap-2">
                      {!channel.is_member && (
                        <button
                          type="button"
                          disabled={busyId === channel.id}
                          onClick={() => inviteBot(channel)}
                          className="px-3 py-1.5 rounded bg-[#1976D2] hover:bg-[#155a9c] text-white text-xs font-semibold disabled:opacity-50"
                        >
                          {busyId === channel.id ? '...' : 'Invite bot'}
                        </button>
                      )}
                      <IntegrateMenu
                        disabled={busyId === channel.id || !channel.is_member}
                        existingEvents={channel.integrations.map((i) => i.event_type)}
                        onPick={(eventType) => integrate(channel, eventType)}
                      />
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

function FanoutBanner({ channels }: { channels: SlackChannelRow[] }) {
  const counts: Record<string, number> = {}
  for (const ch of channels) {
    for (const integ of ch.integrations) {
      if (integ.enabled) {
        counts[integ.event_type] = (counts[integ.event_type] ?? 0) + 1
      }
    }
  }
  const fanout = Object.entries(counts).filter(([, n]) => n > 1)
  if (fanout.length === 0) return null
  return (
    <div className="text-xs bg-[#1976D2]/10 border border-[#1976D2]/20 text-[#1A2B3C] rounded px-3 py-2">
      <strong>Fan-out active:</strong> the events below are wired to multiple channels — every enabled channel
      receives each message. slack_svc dedupes per (appointment, channel) so a redelivery never re-posts.
      <ul className="mt-1 ml-4 list-disc">
        {fanout.map(([eventType, n]) => (
          <li key={eventType}>
            <code>{eventType}</code> → <strong>{n}</strong> channels
          </li>
        ))}
      </ul>
    </div>
  )
}

function IntegrateMenu({
  disabled,
  existingEvents,
  onPick,
}: {
  disabled: boolean
  existingEvents: string[]
  onPick: (eventType: string) => void
}) {
  const [open, setOpen] = useState(false)
  const remaining = KNOWN_EVENT_TYPES.filter((et) => !existingEvents.includes(et.value))
  return (
    <div className="relative">
      <button
        type="button"
        disabled={disabled || remaining.length === 0}
        onClick={() => setOpen((v) => !v)}
        className="px-3 py-1.5 rounded bg-[#0D7377] hover:bg-[#084C4F] text-white text-xs font-semibold disabled:opacity-50"
      >
        {remaining.length === 0 ? 'All events wired' : 'Integrate event ▾'}
      </button>
      {open && remaining.length > 0 && (
        <div className="absolute right-0 mt-1 w-56 bg-white border border-[#0D7377]/20 rounded shadow-lg z-10">
          {remaining.map((et) => (
            <button
              key={et.value}
              type="button"
              onClick={() => {
                setOpen(false)
                onPick(et.value)
              }}
              className="block w-full text-left px-3 py-2 text-xs hover:bg-[#0D7377]/5"
            >
              <code className="text-[10px] text-[#3D5A73]">{et.value}</code>
              <div className="text-[#1A2B3C]">{et.label}</div>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
