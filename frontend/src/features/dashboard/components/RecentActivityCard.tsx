import {
  Card,
  CardContent,
  Typography,
  Box,
  CircularProgress,
  Alert,
  List,
  ListItem,
  ListItemText,
  Chip,
  IconButton,
} from '@mui/material'
import { useRecentActivity } from '../hooks/useDashboard'
import { useNavigate } from 'react-router-dom'
import { OpenInNew, ContactPhone, Description, CheckCircle, Update } from '@mui/icons-material'
import { formatDistanceToNow } from 'date-fns'

export function RecentActivityCard() {
  const { data: activityResponse, isLoading, isError } = useRecentActivity(10)
  const navigate = useNavigate()

  if (isLoading) {
    return (
      <Card>
        <CardContent>
          <Box display="flex" justifyContent="center" p={3}>
            <CircularProgress />
          </Box>
        </CardContent>
      </Card>
    )
  }

  if (isError || !activityResponse) {
    return (
      <Card>
        <CardContent>
          <Alert severity="error">Failed to load recent activity</Alert>
        </CardContent>
      </Card>
    )
  }

  const activities = activityResponse.activities

  const getIcon = (type: string) => {
    switch (type) {
      case 'call':
      case 'email':
        return <ContactPhone fontSize="small" />
      case 'status_change':
        return <CheckCircle fontSize="small" />
      case 'meeting':
        return <Description fontSize="small" />
      default:
        return <Update fontSize="small" />
    }
  }

  const getColor = (type: string) => {
    switch (type) {
      case 'call':
      case 'email':
        return 'info'
      case 'meeting':
        return 'warning'
      case 'status_change':
        return 'success'
      default:
        return 'default'
    }
  }

  const handleNavigate = (activity: typeof activities[0]) => {
    navigate(`/leads/${activity.lead_id}`)
  }

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Recent Activity
        </Typography>

        {activities.length === 0 ? (
          <Typography color="text.secondary" variant="body2">
            No recent activity
          </Typography>
        ) : (
          <List>
            {activities.map((activity) => (
              <ListItem
                key={activity.id}
                sx={{
                  borderRadius: 1,
                  mb: 1,
                  '&:hover': { bgcolor: 'action.hover' },
                }}
                secondaryAction={
                  <IconButton
                    edge="end"
                    size="small"
                    onClick={() => handleNavigate(activity)}
                  >
                    <OpenInNew fontSize="small" />
                  </IconButton>
                }
              >
                <ListItemText
                  primary={
                    <Box display="flex" alignItems="center" gap={1}>
                      <Chip
                        icon={getIcon(activity.type || activity.activity_type)}
                        label={activity.activity_type}
                        size="small"
                        color={getColor(activity.activity_type) as any}
                        variant="outlined"
                      />
                      <Typography variant="body2" fontWeight="medium">
                        {activity.subject || 'Lead Activity'}
                      </Typography>
                    </Box>
                  }
                  secondary={
                    <Box mt={0.5}>
                      <Typography variant="caption" display="block">
                        {activity.details}
                      </Typography>
                      <Box display="flex" gap={1} mt={0.5} alignItems="center">
                        <Typography variant="caption" color="text.secondary">
                          {activity.created_at
                            ? formatDistanceToNow(new Date(activity.created_at), {
                                addSuffix: true,
                              })
                            : 'just now'}
                        </Typography>
                      </Box>
                    </Box>
                  }
                />
              </ListItem>
            ))}
          </List>
        )}
      </CardContent>
    </Card>
  )
}
