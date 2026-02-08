import {
  Card,
  CardContent,
  Typography,
  Box,
  CircularProgress,
  Alert,
  List,
  ListItem,
  ListItemAvatar,
  ListItemText,
  Avatar,
  Chip,
} from '@mui/material'
import { useTopPerformers } from '../hooks/useDashboard'
import { EmojiEvents, TrendingUp } from '@mui/icons-material'

export function TopPerformersCard() {
  const { data: performersResponse, isLoading, isError } = useTopPerformers(5)

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

  if (isError || !performersResponse) {
    return (
      <Card>
        <CardContent>
          <Alert severity="error">Failed to load top performers</Alert>
        </CardContent>
      </Card>
    )
  }

  const performers = performersResponse.performers

  const getMedalColor = (rank: number) => {
    if (rank === 1) return '#FFD700' // Gold
    if (rank === 2) return '#C0C0C0' // Silver
    if (rank === 3) return '#CD7F32' // Bronze
    return undefined
  }

  return (
    <Card>
      <CardContent>
        <Box display="flex" alignItems="center" gap={1} mb={2}>
          <EmojiEvents color="primary" />
          <Typography variant="h6">Top Performers</Typography>
        </Box>

        {performers.length === 0 ? (
          <Typography color="text.secondary" variant="body2">
            No performance data available
          </Typography>
        ) : (
          <List>
            {performers.map((performer, index) => (
              <ListItem
                key={performer.agent_id}
                sx={{
                  mb: 1,
                  borderRadius: 1,
                  border: index < 3 ? 2 : 1,
                  borderColor: index < 3 ? getMedalColor(index + 1) : 'divider',
                }}
              >
                <ListItemAvatar>
                  <Avatar
                    sx={{
                      bgcolor: getMedalColor(index + 1) || 'primary.main',
                    }}
                  >
                    {index < 3 ? index + 1 : `A${performer.agent_id}`}
                  </Avatar>
                </ListItemAvatar>
                <ListItemText
                  primary={
                    <Box display="flex" alignItems="center" gap={1}>
                      <Typography variant="body1" fontWeight="medium">
                        Agent {performer.agent_id}
                      </Typography>
                      {index < 3 && (
                        <Chip
                          label={`#${index + 1}`}
                          size="small"
                          sx={{
                            bgcolor: getMedalColor(index + 1),
                            color: 'white',
                            fontWeight: 'bold',
                          }}
                        />
                      )}
                    </Box>
                  }
                  secondary={
                    <Box mt={0.5}>
                      <Typography variant="caption" display="block">
                        {performer.total_leads} leads • {performer.conversions} conversions
                      </Typography>
                      <Box display="flex" alignItems="center" gap={0.5} mt={0.5}>
                        <TrendingUp fontSize="small" sx={{ color: 'success.main' }} />
                        <Typography variant="caption" sx={{ color: 'success.main' }}>
                          {performer.conversion_rate.toFixed(1)}% conversion rate
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
