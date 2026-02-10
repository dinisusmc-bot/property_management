import React from 'react';
import { Box, Container, Paper, Typography, TextField, Button, Checkbox, FormControlLabel, Link } from '@mui/material';
import { Theme, useTheme } from '@mui/material/styles';
import { glass } from '../theme';

const Login: React.FC = () => {
  const theme = useTheme();

  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: `linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%)`,
      }}
    >
      <Container maxWidth="sm">
        <Paper
          sx={{
            ...glass,
            p: 4,
            textAlign: 'center',
          }}
        >
          <Box sx={{ mb: 4 }}>
            <Typography variant="h2" fontWeight={700} gutterBottom>
              Property Manager
            </Typography>
            <Typography variant="body1" color="text.secondary">
              Sign in to manage your properties
            </Typography>
          </Box>

          <form onSubmit={(e) => e.preventDefault()}>
            <TextField
              fullWidth
              label="Email"
              type="email"
              variant="outlined"
              sx={{ mb: 3 }}
              InputProps={{
                sx: {
                  bgcolor: 'rgba(255,255,255,0.05)',
                  borderRadius: 2,
                  '& .MuiOutlinedInput-notchedOutline': {
                    borderColor: 'rgba(255,255,255,0.1)',
                  },
                },
              }}
            />
            <TextField
              fullWidth
              label="Password"
              type="password"
              variant="outlined"
              sx={{ mb: 3 }}
              InputProps={{
                sx: {
                  bgcolor: 'rgba(255,255,255,0.05)',
                  borderRadius: 2,
                  '& .MuiOutlinedInput-notchedOutline': {
                    borderColor: 'rgba(255,255,255,0.1)',
                  },
                },
              }}
            />
            <FormControlLabel
              control={<Checkbox defaultChecked sx={{ color: '#6366f1' }} />}
              label="Remember me"
              sx={{ justifyContent: 'flex-start', mb: 3 }}
            />
            <Button
              type="submit"
              fullWidth
              variant="contained"
              size="large"
              sx={{
                py: 1.5,
                borderRadius: 2,
                background: 'linear-gradient(90deg, #6366f1, #8b5cf6)',
                '&:hover': {
                  background: 'linear-gradient(90deg, #4f46e5, #7c3aed)',
                },
              }}
            >
              Sign In
            </Button>
          </form>

          <Box sx={{ mt: 3 }}>
            <Link href="#" underline="hover" color="text.secondary">
              Forgot password?
            </Link>
          </Box>
        </Paper>
      </Container>
    </Box>
  );
};

export default Login;
