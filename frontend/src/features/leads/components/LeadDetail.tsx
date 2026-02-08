import { useParams, useNavigate } from 'react-router-dom'
import {
  Box,
  Typography,
  Grid,
  Button,
  Chip,
  Divider,
  CircularProgress,
  Card,
  CardContent
} from '@mui/material'
import {
  Edit as EditIcon,
  ArrowBack as BackIcon,
  CheckCircle as ConvertIcon
} from '@mui/icons-material'
import { useLead, useConvertLead } from '../hooks/useLeads'
import { format } from 'date-fns'

export default function LeadDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { data: lead, isLoading } = useLead(Number(id))
  const convertMutation = useConvertLead()
  
  const handleConvert = () => {
    if (lead && confirm(`Convert lead "${lead.first_name} ${lead.last_name}" to quote?`)) {
      convertMutation.mutate(lead.id, {
        onSuccess: (data) => {
          navigate(`/charters/${data.charter_id}`)
        }
      })
    }
  }
  
  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    )
  }
  
  if (!lead) {
    return (
      <Box>
        <Typography>Lead not found</Typography>
      </Box>
    )
  }
  
  const getStatusColor = (status: string): any => {
    const colors = {
      new: 'info',
      contacted: 'primary',
      qualified: 'secondary',
      quote_sent: 'warning',
      converted: 'success',
      lost: 'error'
    }
    return colors[status as keyof typeof colors] || 'default'
  }
  
  return (
    <Box>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box display="flex" alignItems="center" gap={2}>
          <Button
            startIcon={<BackIcon />}
            onClick={() => navigate('/leads')}
          >
            Back to Leads
          </Button>
          <Typography variant="h4">{lead.first_name} {lead.last_name}</Typography>
          <Chip
            label={lead.status}
            color={getStatusColor(lead.status)}
          />
        </Box>
        <Box display="flex" gap={1}>
          {lead.status !== 'converted' && (
            <Button
              variant="contained"
              color="success"
              startIcon={<ConvertIcon />}
              onClick={handleConvert}
              disabled={convertMutation.isPending}
            >
              Convert to Quote
            </Button>
          )}
          <Button
            variant="outlined"
            startIcon={<EditIcon />}
            onClick={() => navigate(`/leads/${lead.id}/edit`)}
          >
            Edit
          </Button>
        </Box>
      </Box>
      
      {/* Lead Information */}
      <Grid container spacing={3}>
        {/* Contact Information */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Contact Information
              </Typography>
              <Divider sx={{ mb: 2 }} />
              
              <Grid container spacing={2}>
                <Grid item xs={4}>
                  <Typography variant="body2" color="textSecondary">
                    Name
                  </Typography>
                </Grid>
                <Grid item xs={8}>
                  <Typography variant="body1">{lead.name}</Typography>
                </Grid>
                
                <Grid item xs={4}>
                  <Typography variant="body2" color="textSecondary">
                    Company
                  </Typography>
                </Grid>
                <Grid item xs={8}>
                  <Typography variant="body1">
                    {lead.company_name || '-'}
                  </Typography>
                </Grid>
                
                <Grid item xs={4}>
                  <Typography variant="body2" color="textSecondary">
                    Email
                  </Typography>
                </Grid>
                <Grid item xs={8}>
                  <Typography variant="body1">{lead.email}</Typography>
                </Grid>
                
                <Grid item xs={4}>
                  <Typography variant="body2" color="textSecondary">
                    Phone
                  </Typography>
                </Grid>
                <Grid item xs={8}>
                  <Typography variant="body1">{lead.phone}</Typography>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>
        
        {/* Lead Details */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Lead Details
              </Typography>
              <Divider sx={{ mb: 2 }} />
              
              <Grid container spacing={2}>
                <Grid item xs={4}>
                  <Typography variant="body2" color="textSecondary">
                    Source
                  </Typography>
                </Grid>
                <Grid item xs={8}>
                  <Chip label={lead.source} size="small" />
                </Grid>
                
                <Grid item xs={4}>
                  <Typography variant="body2" color="textSecondary">
                    Status
                  </Typography>
                </Grid>
                <Grid item xs={8}>
                  <Chip
                    label={lead.status}
                    color={getStatusColor(lead.status)}
                    size="small"
                  />
                </Grid>
                
                <Grid item xs={4}>
                  <Typography variant="body2" color="textSecondary">
                    Assigned To
                  </Typography>
                </Grid>
                <Grid item xs={8}>
                  <Typography variant="body1">
                    {lead.assigned_agent_id ? `Agent ${lead.assigned_agent_id}` : 'Unassigned'}
                  </Typography>
                </Grid>
                
                <Grid item xs={4}>
                  <Typography variant="body2" color="textSecondary">
                    Created
                  </Typography>
                </Grid>
                <Grid item xs={8}>
                  <Typography variant="body1">
                    {format(new Date(lead.created_at), 'MMM dd, yyyy HH:mm')}
                  </Typography>
                </Grid>
                
                {lead.last_contact_date && (
                  <>
                    <Grid item xs={4}>
                      <Typography variant="body2" color="textSecondary">
                        Last Contact
                      </Typography>
                    </Grid>
                    <Grid item xs={8}>
                      <Typography variant="body1">
                        {format(new Date(lead.last_contact_date), 'MMM dd, yyyy')}
                      </Typography>
                    </Grid>
                  </>
                )}
              </Grid>
            </CardContent>
          </Card>
        </Grid>
        
        {/* Trip Information */}
        {(lead.trip_type || lead.trip_date || lead.passengers) && (
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Trip Information
                </Typography>
                <Divider sx={{ mb: 2 }} />
                
                <Grid container spacing={2}>
                  {lead.trip_type && (
                    <>
                      <Grid item xs={2}>
                        <Typography variant="body2" color="textSecondary">
                          Trip Type
                        </Typography>
                      </Grid>
                      <Grid item xs={4}>
                        <Typography variant="body1">{lead.trip_type}</Typography>
                      </Grid>
                    </>
                  )}
                  
                  {lead.trip_date && (
                    <>
                      <Grid item xs={2}>
                        <Typography variant="body2" color="textSecondary">
                          Trip Date
                        </Typography>
                      </Grid>
                      <Grid item xs={4}>
                        <Typography variant="body1">
                          {format(new Date(lead.trip_date), 'MMM dd, yyyy')}
                        </Typography>
                      </Grid>
                    </>
                  )}
                  
                  {lead.passengers && (
                    <>
                      <Grid item xs={2}>
                        <Typography variant="body2" color="textSecondary">
                          Passengers
                        </Typography>
                      </Grid>
                      <Grid item xs={4}>
                        <Typography variant="body1">{lead.passengers}</Typography>
                      </Grid>
                    </>
                  )}
                </Grid>
              </CardContent>
            </Card>
          </Grid>
        )}
        
        {/* Notes */}
        {lead.notes && (
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Notes
                </Typography>
                <Divider sx={{ mb: 2 }} />
                <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
                  {lead.notes}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        )}
      </Grid>
    </Box>
  )
}
