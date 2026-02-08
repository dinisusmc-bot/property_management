import { Card, CardContent, Typography, Box, Button } from '@mui/material'
import { useNavigate } from 'react-router-dom'
import { ContactPhone, Description } from '@mui/icons-material'

export function QuickActionsCard() {
  const navigate = useNavigate()

  const actions = [
    {
      label: 'Create Lead',
      icon: <ContactPhone />,
      color: 'primary',
      path: '/leads/new',
    },
    {
      label: 'Create Charter Quote',
      icon: <Description />,
      color: 'secondary',
      path: '/charters/new',
    },
  ]

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Quick Actions
        </Typography>

        <Box display="flex" flexDirection="column" gap={2} mt={2}>
          {actions.map((action) => (
            <Button
              key={action.path}
              variant="contained"
              color={action.color as any}
              size="large"
              startIcon={action.icon}
              fullWidth
              onClick={() => navigate(action.path)}
            >
              {action.label}
            </Button>
          ))}
        </Box>

        <Box mt={3}>
          <Typography variant="caption" color="text.secondary" display="block" gutterBottom>
            Quick Links
          </Typography>
          <Box display="flex" flexDirection="column" gap={1}>
            <Button
              size="small"
              variant="text"
              onClick={() => navigate('/leads')}
              sx={{ justifyContent: 'flex-start' }}
            >
              View All Leads
            </Button>
            <Button
              size="small"
              variant="text"
              onClick={() => navigate('/charters')}
              sx={{ justifyContent: 'flex-start' }}
            >
              View All Charters
            </Button>
          </Box>
        </Box>
      </CardContent>
    </Card>
  )
}
