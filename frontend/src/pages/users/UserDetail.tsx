import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  Typography,
  Paper,
  Box,
  Grid,
  Button,
  Chip,
  CircularProgress,
  Alert,
  Divider,
  TextField,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControlLabel,
  Switch,
  Select,
  MenuItem,
  FormControl,
  InputLabel
} from '@mui/material'
import { ArrowBack as BackIcon, Edit as EditIcon, Lock as LockIcon } from '@mui/icons-material'
import api from '../../services/api'
import { useAuthStore } from '../../store/authStore'

interface User {
  id: number
  email: string
  full_name: string
  role: string
  is_active: boolean
  is_superuser: boolean
  created_at: string
}

export default function UserDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const currentUser = useAuthStore(state => state.user)
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  
  // Edit dialog state
  const [editDialogOpen, setEditDialogOpen] = useState(false)
  const [editForm, setEditForm] = useState({
    full_name: '',
    role: '',
    is_active: true
  })
  
  // Password dialog state
  const [passwordDialogOpen, setPasswordDialogOpen] = useState(false)
  const [passwordForm, setPasswordForm] = useState({
    current_password: '',
    new_password: '',
    confirm_password: ''
  })
  const [adminPasswordForm, setAdminPasswordForm] = useState({
    new_password: '',
    confirm_password: ''
  })

  const isOwnProfile = currentUser?.id === Number(id)
  const isAdmin = currentUser?.is_superuser || false

  useEffect(() => {
    if (id) {
      fetchUser()
    }
  }, [id])

  const fetchUser = async () => {
    try {
      setLoading(true)
      const response = await api.get(`/api/v1/auth/users/${id}`)
      const userData = response.data
      setUser(userData)
      setEditForm({
        full_name: userData.full_name,
        role: userData.role,
        is_active: userData.is_active
      })
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load user')
    } finally {
      setLoading(false)
    }
  }

  const handleEditOpen = () => {
    setEditDialogOpen(true)
    setError('')
    setSuccess('')
  }

  const handleEditClose = () => {
    setEditDialogOpen(false)
  }

  const handleEditSave = async () => {
    try {
      const updateData: any = { full_name: editForm.full_name }
      
      if (isAdmin) {
        updateData.role = editForm.role
        updateData.is_active = editForm.is_active
      }
      
      await api.put(`/api/v1/auth/users/${id}`, updateData)
      setSuccess('User updated successfully')
      setEditDialogOpen(false)
      fetchUser()
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to update user')
    }
  }

  const handlePasswordOpen = () => {
    setPasswordDialogOpen(true)
    setError('')
    setSuccess('')
    setPasswordForm({ current_password: '', new_password: '', confirm_password: '' })
    setAdminPasswordForm({ new_password: '', confirm_password: '' })
  }

  const handlePasswordClose = () => {
    setPasswordDialogOpen(false)
  }

  const handlePasswordChange = async () => {
    if (isAdmin && !isOwnProfile) {
      // Admin changing another user's password
      if (adminPasswordForm.new_password !== adminPasswordForm.confirm_password) {
        setError('Passwords do not match')
        return
      }
      
      try {
        await api.post(`/api/v1/auth/users/${id}/admin-change-password`, {
          new_password: adminPasswordForm.new_password
        })
        setSuccess('Password changed successfully')
        setPasswordDialogOpen(false)
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to change password')
      }
    } else {
      // User changing own password
      if (passwordForm.new_password !== passwordForm.confirm_password) {
        setError('Passwords do not match')
        return
      }
      
      try {
        await api.post(`/api/v1/auth/users/${id}/change-password`, {
          current_password: passwordForm.current_password,
          new_password: passwordForm.new_password
        })
        setSuccess('Password changed successfully')
        setPasswordDialogOpen(false)
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to change password')
      }
    }
  }

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
        <CircularProgress />
      </Box>
    )
  }

  if (error && !user) {
    return (
      <Box>
        <Alert severity="error">{error}</Alert>
        <Button onClick={() => navigate('/users')} sx={{ mt: 2 }}>
          Back to Users
        </Button>
      </Box>
    )
  }

  if (!user) {
    return (
      <Box>
        <Alert severity="warning">User not found</Alert>
        <Button onClick={() => navigate('/users')} sx={{ mt: 2 }}>
          Back to Users
        </Button>
      </Box>
    )
  }

  return (
    <Box>
      <Button
        startIcon={<BackIcon />}
        onClick={() => navigate(isAdmin ? '/users' : '/dashboard')}
        sx={{ mb: 2 }}
      >
        {isAdmin ? 'Back to Users' : 'Back to Dashboard'}
      </Button>

      {success && <Alert severity="success" sx={{ mb: 2 }}>{success}</Alert>}
      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">{user.full_name}</Typography>
        <Box>
          {isOwnProfile && (
            <Chip label="Your Profile" color="primary" sx={{ mr: 1 }} />
          )}
          <Chip 
            label={user.is_active ? 'Active' : 'Inactive'} 
            color={user.is_active ? 'success' : 'default'} 
          />
        </Box>
      </Box>

      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6">User Information</Typography>
              {(isOwnProfile || isAdmin) && (
                <Button startIcon={<EditIcon />} size="small" onClick={handleEditOpen}>
                  Edit
                </Button>
              )}
            </Box>
            <Divider sx={{ mb: 2 }} />
            
            <Box sx={{ mb: 2 }}>
              <Typography variant="caption" color="textSecondary">Full Name</Typography>
              <Typography variant="body1">{user.full_name}</Typography>
            </Box>

            <Box sx={{ mb: 2 }}>
              <Typography variant="caption" color="textSecondary">Email</Typography>
              <Typography variant="body1">{user.email}</Typography>
            </Box>

            <Box sx={{ mb: 2 }}>
              <Typography variant="caption" color="textSecondary">Role</Typography>
              <Box sx={{ mt: 0.5 }}>
                <Chip label={user.role} color="primary" size="small" />
              </Box>
            </Box>

            <Box sx={{ mb: 2 }}>
              <Typography variant="caption" color="textSecondary">Superuser</Typography>
              <Typography variant="body1">
                {user.is_superuser ? <Chip label="Yes" color="warning" size="small" /> : 'No'}
              </Typography>
            </Box>

            <Box sx={{ mb: 2 }}>
              <Typography variant="caption" color="textSecondary">Created</Typography>
              <Typography variant="body1">
                {new Date(user.created_at).toLocaleDateString()}
              </Typography>
            </Box>
          </Paper>
        </Grid>

        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>Security</Typography>
            <Divider sx={{ mb: 2 }} />
            
            <Box sx={{ mb: 2 }}>
              <Typography variant="body2" color="textSecondary" paragraph>
                {isOwnProfile 
                  ? 'Change your password to keep your account secure.'
                  : isAdmin 
                    ? 'As an admin, you can reset this user\'s password.'
                    : 'Contact an administrator to change your password.'}
              </Typography>
              {(isOwnProfile || isAdmin) && (
                <Button 
                  variant="outlined" 
                  startIcon={<LockIcon />}
                  onClick={handlePasswordOpen}
                  fullWidth
                >
                  Change Password
                </Button>
              )}
            </Box>
          </Paper>
        </Grid>
      </Grid>

      {/* Edit Dialog */}
      <Dialog open={editDialogOpen} onClose={handleEditClose} maxWidth="sm" fullWidth>
        <DialogTitle>Edit User</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2 }}>
            <TextField
              fullWidth
              label="Full Name"
              value={editForm.full_name}
              onChange={(e) => setEditForm({ ...editForm, full_name: e.target.value })}
              margin="normal"
            />
            
            {isAdmin && (
              <>
                <FormControl fullWidth margin="normal">
                  <InputLabel>Role</InputLabel>
                  <Select
                    value={editForm.role}
                    onChange={(e) => setEditForm({ ...editForm, role: e.target.value })}
                    label="Role"
                  >
                    <MenuItem value="user">User</MenuItem>
                    <MenuItem value="manager">Manager</MenuItem>
                    <MenuItem value="admin">Admin</MenuItem>
                    <MenuItem value="vendor">Vendor</MenuItem>
                  </Select>
                </FormControl>
                
                <FormControlLabel
                  control={
                    <Switch
                      checked={editForm.is_active}
                      onChange={(e) => setEditForm({ ...editForm, is_active: e.target.checked })}
                    />
                  }
                  label="Active"
                />
              </>
            )}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleEditClose}>Cancel</Button>
          <Button onClick={handleEditSave} variant="contained">Save</Button>
        </DialogActions>
      </Dialog>

      {/* Password Change Dialog */}
      <Dialog open={passwordDialogOpen} onClose={handlePasswordClose} maxWidth="sm" fullWidth>
        <DialogTitle>Change Password</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2 }}>
            {isAdmin && !isOwnProfile ? (
              // Admin changing another user's password
              <>
                <TextField
                  fullWidth
                  type="password"
                  label="New Password"
                  value={adminPasswordForm.new_password}
                  onChange={(e) => setAdminPasswordForm({ ...adminPasswordForm, new_password: e.target.value })}
                  margin="normal"
                />
                <TextField
                  fullWidth
                  type="password"
                  label="Confirm Password"
                  value={adminPasswordForm.confirm_password}
                  onChange={(e) => setAdminPasswordForm({ ...adminPasswordForm, confirm_password: e.target.value })}
                  margin="normal"
                />
              </>
            ) : (
              // User changing own password
              <>
                <TextField
                  fullWidth
                  type="password"
                  label="Current Password"
                  value={passwordForm.current_password}
                  onChange={(e) => setPasswordForm({ ...passwordForm, current_password: e.target.value })}
                  margin="normal"
                />
                <TextField
                  fullWidth
                  type="password"
                  label="New Password"
                  value={passwordForm.new_password}
                  onChange={(e) => setPasswordForm({ ...passwordForm, new_password: e.target.value })}
                  margin="normal"
                />
                <TextField
                  fullWidth
                  type="password"
                  label="Confirm Password"
                  value={passwordForm.confirm_password}
                  onChange={(e) => setPasswordForm({ ...passwordForm, confirm_password: e.target.value })}
                  margin="normal"
                />
              </>
            )}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handlePasswordClose}>Cancel</Button>
          <Button onClick={handlePasswordChange} variant="contained" color="primary">
            Change Password
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
