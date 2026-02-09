/**
 * Client Portal Login Page
 */
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Alert,
  Link,
  Divider,
  Grid,
  Container
} from '@mui/material'
import { useClientLogin } from '../hooks/useClientPortalQuery'
import {
  AccountCircle as AccountIcon,
  Lock as LockIcon,
  Email as EmailIcon
} from '@mui/icons-material'

export default function ClientLogin() {
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  
  const loginMutation = useClientLogin()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    
    if (!email || !password) {
      setError('Please fill in all fields')
      return
    }

    try {
      loginMutation.mutate(
        { email, password },
        {
          onSuccess: (data) => {
            if (data.success) {
              // Store token in localStorage
              if (data.token) {
                localStorage.setItem('clientToken', data.token)
                navigate('/client/dashboard')
              }
            } else {
              setError(data.message || 'Login failed')
            }
          },
          onError: () => {
            setError('Failed to login. Please try again.')
          },
        }
      )
    } catch (err: any) {
      setError(err.message || 'An error occurred during login')
    }
  }

  return (
    <Container maxWidth="sm">
      <Box
        sx={{
          mt: 8,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
        }}
      >
        <Paper sx={{ p: 4, width: '100%' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', mb: 3 }}>
            <AccountIcon fontSize="large" sx={{ mr: 1, color: 'primary.main' }} />
            <Typography variant="h4" component="h1">
              Client Portal
            </Typography>
          </Box>

          {error && (
            <Alert severity="error" sx={{ mb: 3 }}>
              {error}
            </Alert>
          )}

          <form onSubmit={handleSubmit}>
            <TextField
              fullWidth
              label="Email Address"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              sx={{ mb: 3 }}
              InputProps={{
                startAdornment: <EmailIcon sx={{ mr: 1, color: 'text.secondary' }} />,
              }}
            />

            <TextField
              fullWidth
              label="Password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              sx={{ mb: 3 }}
              InputProps={{
                startAdornment: <LockIcon sx={{ mr: 1, color: 'text.secondary' }} />,
              }}
            />

            <Button
              type="submit"
              fullWidth
              variant="contained"
              size="large"
              sx={{ mb: 3 }}
              disabled={loginMutation.isPending}
            >
              {loginMutation.isPending ? 'Logging in...' : 'Sign In'}
            </Button>
          </form>

          <Divider sx={{ my: 3 }}>
            <Typography variant="body2" color="text.secondary">
              OR
            </Typography>
          </Divider>

          <Grid container spacing={2}>
            <Grid item xs={6}>
              <Button
                fullWidth
                variant="outlined"
                onClick={() => navigate('/client/register')}
              >
                Register
              </Button>
            </Grid>
            <Grid item xs={6}>
              <Button
                fullWidth
                variant="text"
                onClick={() => navigate('/')}
              >
                Back to Main
              </Button>
            </Grid>
          </Grid>
        </Paper>

        <Typography variant="body2" color="text.secondary" sx={{ mt: 3 }}>
          Don't have an account?{' '}
          <Link href="#" onClick={(e) => { e.preventDefault(); navigate('/client/register'); }}>
            Register here
          </Link>
        </Typography>
      </Box>
    </Container>
  )
}
