import { useState, useEffect } from 'react'
import { authAPI } from '../api/client'
import { GlassCard, StatusBadge, SentinelButton, LoadingSpinner, PageHeader, EmptyState } from '../components/common'
import { Users, UserPlus, RefreshCw, Shield, Edit3 } from 'lucide-react'

export default function UserManagementPage() {
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)

  const fetchUsers = () => {
    setLoading(true)
    authAPI.getUsers()
      .then((res) => {
        if (res.data?.data) {
          setUsers(res.data.data)
        }
      })
      .catch(console.error)
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    fetchUsers()
  }, [])

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <PageHeader
        icon={Users}
        title="User Access Control (RBAC)"
        badge={`${users.length} accounts`}
        subtitle="Manage SOC analyst accounts, permissions, authentication credentials, and access roles"
        actions={
          <div className="flex items-center gap-2">
            <SentinelButton onClick={fetchUsers} variant="secondary" size="sm">
              <RefreshCw size={13} className={loading ? 'animate-spin' : ''} />
              <span>Refresh</span>
            </SentinelButton>
            <SentinelButton size="sm">
              <UserPlus size={14} /> Add Analyst
            </SentinelButton>
          </div>
        }
      />

      <GlassCard className="p-5">
        {loading ? (
          <LoadingSpinner text="Loading analyst accounts..." />
        ) : (
          <div className="overflow-x-auto">
            <table className="soc-table">
              <thead>
                <tr>
                  <th>Analyst Name</th>
                  <th>Email Address</th>
                  <th>Role</th>
                  <th>Status</th>
                  <th>Last Activity</th>
                  <th className="w-24">Actions</th>
                </tr>
              </thead>
              <tbody>
                {users.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="text-center py-10 text-xs text-[#607A71]">
                      No user accounts found.
                    </td>
                  </tr>
                ) : (
                  users.map((u) => (
                    <tr key={u._id || u.id || u.email}>
                      <td>
                        <div className="flex items-center gap-2.5">
                          <div className="w-7 h-7 rounded-md bg-[rgba(0,245,160,0.12)] text-[#00F5A0] border border-[rgba(0,245,160,0.25)] flex items-center justify-center font-mono font-bold text-xs">
                            {u.name?.[0]?.toUpperCase() || 'A'}
                          </div>
                          <span className="font-semibold text-[#E8FFF6] font-sans">{u.name}</span>
                        </div>
                      </td>
                      <td className="text-[#9BB7AD] font-mono text-xs">{u.email}</td>
                      <td>
                        <span className="px-2 py-0.5 rounded text-[10px] font-mono font-semibold bg-[rgba(0,245,160,0.1)] text-[#00F5A0] border border-[rgba(0,245,160,0.2)] uppercase">
                          {u.role || 'Analyst'}
                        </span>
                      </td>
                      <td>
                        <StatusBadge status={u.is_active !== false ? 'active' : 'inactive'} />
                      </td>
                      <td className="text-[#607A71] text-xs font-mono">
                        {u.last_login ? new Date(u.last_login).toLocaleString() : 'Recent'}
                      </td>
                      <td>
                        <button className="text-[11px] font-medium text-[#00F5A0] hover:underline cursor-pointer flex items-center gap-1">
                          <Edit3 size={11} /> Permissions
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        )}
      </GlassCard>
    </div>
  )
}
