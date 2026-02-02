import { Box, Container, Typography, Button, Paper, Grid } from '@mui/material'
import { useNavigate } from 'react-router-dom'
import {
  DirectionsBus as BusIcon,
  Security as SecurityIcon,
  AttachMoney as MoneyIcon,
  EventSeat as ComfortIcon,
  Business as BusinessIcon,
  School as SchoolIcon,
  Church as ChurchIcon,
  Groups as FamilyIcon,
  SportsBaseball as SportsIcon,
  Phone as PhoneIcon
} from '@mui/icons-material'

export default function HomePage() {
  const navigate = useNavigate()

  return (
    <Box sx={{ minHeight: '100vh', bgcolor: 'grey.50' }}>
      {/* Header Bar */}
      <Box sx={{ bgcolor: 'primary.main', color: 'white', py: 1 }}>
        <Container maxWidth="lg">
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="body2">
              🛡️ $10 million insurance • DOT compliant • Nationwide service
            </Typography>
            <Button
              variant="outlined"
              size="small"
              startIcon={<PhoneIcon />}
              onClick={() => navigate('/quote')}
              sx={{ 
                borderColor: 'white', 
                color: 'white',
                '&:hover': { bgcolor: 'rgba(255,255,255,0.1)', borderColor: 'white' }
              }}
            >
              Call 24/7
            </Button>
          </Box>
        </Container>
      </Box>

      {/* Hero Section */}
      <Box
        sx={{
          background: 'linear-gradient(135deg, #1976d2 0%, #1565c0 100%)',
          color: 'white',
          py: 10,
          textAlign: 'center'
        }}
      >
        <Container maxWidth="lg">
          <Typography variant="h2" gutterBottom fontWeight="bold">
            Nationwide Bus Rental Leader
          </Typography>
          <Typography variant="h5" sx={{ mb: 2, fontWeight: 300 }}>
            Professional Charter Bus Services for Every Occasion
          </Typography>
          <Typography variant="body1" sx={{ mb: 4, opacity: 0.95, maxWidth: 800, mx: 'auto' }}>
            Safe, reliable, and comfortable charter bus rentals for corporate events, school trips, 
            family reunions, church groups, and more. Available 24/7 nationwide.
          </Typography>
          <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center', flexWrap: 'wrap', mb: 4 }}>
            <Button
              variant="contained"
              size="large"
              onClick={() => navigate('/quote')}
              sx={{
                bgcolor: '#4caf50',
                color: 'white',
                px: 5,
                py: 2,
                fontSize: '1.1rem',
                fontWeight: 'bold',
                '&:hover': {
                  bgcolor: '#45a049'
                }
              }}
            >
              Get Instant Quote
            </Button>
            <Button
              variant="outlined"
              size="large"
              onClick={() => navigate('/login')}
              sx={{
                borderColor: 'white',
                color: 'white',
                px: 5,
                py: 2,
                fontSize: '1.1rem',
                '&:hover': {
                  borderColor: 'white',
                  bgcolor: 'rgba(255,255,255,0.1)'
                }
              }}
            >
              Client Login
            </Button>
          </Box>

          {/* Vehicle Selection Quick View */}
          <Grid container spacing={2} sx={{ maxWidth: 900, mx: 'auto', mt: 4 }}>
            <Grid item xs={12} md={4}>
              <Paper 
                sx={{ 
                  p: 3, 
                  textAlign: 'center', 
                  cursor: 'pointer',
                  '&:hover': { transform: 'translateY(-4px)', boxShadow: 4 },
                  transition: 'all 0.3s'
                }}
                onClick={() => navigate('/quote')}
              >
                <BusIcon sx={{ fontSize: 50, color: 'primary.main', mb: 1 }} />
                <Typography variant="h6" fontWeight="bold">Shuttle Van</Typography>
                <Typography variant="body2" color="text.secondary">1-16 passengers</Typography>
              </Paper>
            </Grid>
            <Grid item xs={12} md={4}>
              <Paper 
                sx={{ 
                  p: 3, 
                  textAlign: 'center', 
                  cursor: 'pointer',
                  '&:hover': { transform: 'translateY(-4px)', boxShadow: 4 },
                  transition: 'all 0.3s'
                }}
                onClick={() => navigate('/quote')}
              >
                <BusIcon sx={{ fontSize: 50, color: 'primary.main', mb: 1 }} />
                <Typography variant="h6" fontWeight="bold">Mini Bus</Typography>
                <Typography variant="body2" color="text.secondary">17-36 passengers</Typography>
              </Paper>
            </Grid>
            <Grid item xs={12} md={4}>
              <Paper 
                sx={{ 
                  p: 3, 
                  textAlign: 'center', 
                  cursor: 'pointer',
                  '&:hover': { transform: 'translateY(-4px)', boxShadow: 4 },
                  transition: 'all 0.3s'
                }}
                onClick={() => navigate('/quote')}
              >
                <BusIcon sx={{ fontSize: 50, color: 'primary.main', mb: 1 }} />
                <Typography variant="h6" fontWeight="bold">Full Coach</Typography>
                <Typography variant="body2" color="text.secondary">37+ passengers</Typography>
              </Paper>
            </Grid>
          </Grid>
        </Container>
      </Box>

      {/* About Section */}
      <Container maxWidth="lg" sx={{ py: 8 }}>
        <Typography variant="h3" align="center" gutterBottom fontWeight="bold">
          Nationwide Bus Rental Service
        </Typography>
        <Typography variant="body1" color="text.secondary" paragraph sx={{ maxWidth: 900, mx: 'auto', textAlign: 'center', mb: 6 }}>
          We have an unparalleled network of service providers throughout the United States, providing 
          state-of-the-art ground travel to thousands of events every year. Our highly professional 
          transportation consultants are trained and certified on Department Of Transportation (DOT) 
          compliance and regulations.
        </Typography>
      </Container>

      {/* Why Choose Us Section */}
      <Box sx={{ bgcolor: 'white', py: 8 }}>
        <Container maxWidth="lg">
          <Typography variant="h3" align="center" gutterBottom fontWeight="bold" sx={{ mb: 6 }}>
            Why Choose Us?
          </Typography>
          <Grid container spacing={4}>
            <Grid item xs={12} md={6}>
              <Paper sx={{ p: 4, height: '100%', display: 'flex', gap: 3 }}>
                <SecurityIcon sx={{ fontSize: 60, color: 'primary.main' }} />
                <Box>
                  <Typography variant="h5" gutterBottom fontWeight="bold">
                    Safe & Reliable
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    We work with our vendors to monitor driver performance & we look to secure late 
                    model vehicles that are well maintained and pass all state inspections.
                  </Typography>
                </Box>
              </Paper>
            </Grid>
            <Grid item xs={12} md={6}>
              <Paper sx={{ p: 4, height: '100%', display: 'flex', gap: 3 }}>
                <MoneyIcon sx={{ fontSize: 60, color: 'primary.main' }} />
                <Box>
                  <Typography variant="h5" gutterBottom fontWeight="bold">
                    Affordable & Efficient
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    We offer competitive rates that deliver value to meet your budget. Our extensive 
                    network allows us to find the best price for your charter.
                  </Typography>
                </Box>
              </Paper>
            </Grid>
            <Grid item xs={12} md={6}>
              <Paper sx={{ p: 4, height: '100%', display: 'flex', gap: 3 }}>
                <ComfortIcon sx={{ fontSize: 60, color: 'primary.main' }} />
                <Box>
                  <Typography variant="h5" gutterBottom fontWeight="bold">
                    Comfortable & Convenient
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    There's plenty of amenities and room to stretch and move around on the coaches 
                    we provide. WiFi, reclining seats, and climate control included.
                  </Typography>
                </Box>
              </Paper>
            </Grid>
            <Grid item xs={12} md={6}>
              <Paper sx={{ p: 4, height: '100%', display: 'flex', gap: 3 }}>
                <BusIcon sx={{ fontSize: 60, color: 'primary.main' }} />
                <Box>
                  <Typography variant="h5" gutterBottom fontWeight="bold">
                    Flexible
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    You won't have to choose from prepackaged trips. You tell us where you want to go 
                    and when you want to be there and we'll handle the details.
                  </Typography>
                </Box>
              </Paper>
            </Grid>
          </Grid>
        </Container>
      </Box>

      {/* Use Cases Section */}
      <Container maxWidth="lg" sx={{ py: 8 }}>
        <Typography variant="h3" align="center" gutterBottom fontWeight="bold" sx={{ mb: 6 }}>
          Charter Your Buses For
        </Typography>
        <Grid container spacing={3}>
          <Grid item xs={12} sm={6} md={4}>
            <Paper 
              sx={{ 
                p: 3, 
                textAlign: 'center', 
                height: '100%',
                cursor: 'pointer',
                '&:hover': { boxShadow: 6 },
                transition: 'all 0.3s'
              }}
              onClick={() => navigate('/quote')}
            >
              <BusinessIcon sx={{ fontSize: 60, color: 'primary.main', mb: 2 }} />
              <Typography variant="h6" gutterBottom fontWeight="bold">
                Corporate Trips
              </Typography>
              <Typography variant="body2" color="text.secondary">
                WiFi-equipped buses so your team can work while traveling. Perfect for conferences, 
                team building, and corporate events.
              </Typography>
            </Paper>
          </Grid>
          <Grid item xs={12} sm={6} md={4}>
            <Paper 
              sx={{ 
                p: 3, 
                textAlign: 'center', 
                height: '100%',
                cursor: 'pointer',
                '&:hover': { boxShadow: 6 },
                transition: 'all 0.3s'
              }}
              onClick={() => navigate('/quote')}
            >
              <SchoolIcon sx={{ fontSize: 60, color: 'primary.main', mb: 2 }} />
              <Typography variant="h6" gutterBottom fontWeight="bold">
                School Trips
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Safe, reliable transportation for students and faculty. We understand the added 
                responsibility when traveling with children.
              </Typography>
            </Paper>
          </Grid>
          <Grid item xs={12} sm={6} md={4}>
            <Paper 
              sx={{ 
                p: 3, 
                textAlign: 'center', 
                height: '100%',
                cursor: 'pointer',
                '&:hover': { boxShadow: 6 },
                transition: 'all 0.3s'
              }}
              onClick={() => navigate('/quote')}
            >
              <FamilyIcon sx={{ fontSize: 60, color: 'primary.main', mb: 2 }} />
              <Typography variant="h6" gutterBottom fontWeight="bold">
                Family Trips
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Perfect for family reunions, weddings, and special occasions. Keep everyone together 
                and comfortable throughout the journey.
              </Typography>
            </Paper>
          </Grid>
          <Grid item xs={12} sm={6} md={4}>
            <Paper 
              sx={{ 
                p: 3, 
                textAlign: 'center', 
                height: '100%',
                cursor: 'pointer',
                '&:hover': { boxShadow: 6 },
                transition: 'all 0.3s'
              }}
              onClick={() => navigate('/quote')}
            >
              <ChurchIcon sx={{ fontSize: 60, color: 'primary.main', mb: 2 }} />
              <Typography variant="h6" gutterBottom fontWeight="bold">
                Church Trips
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Focus on fellowship while we handle transportation. Ideal for retreats, mission trips, 
                and church outings.
              </Typography>
            </Paper>
          </Grid>
          <Grid item xs={12} sm={6} md={4}>
            <Paper 
              sx={{ 
                p: 3, 
                textAlign: 'center', 
                height: '100%',
                cursor: 'pointer',
                '&:hover': { boxShadow: 6 },
                transition: 'all 0.3s'
              }}
              onClick={() => navigate('/quote')}
            >
              <SportsIcon sx={{ fontSize: 60, color: 'primary.main', mb: 2 }} />
              <Typography variant="h6" gutterBottom fontWeight="bold">
                Sports Events
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Going to the big game? Comfortable, affordable transport that drops you right at the 
                stadium or arena.
              </Typography>
            </Paper>
          </Grid>
          <Grid item xs={12} sm={6} md={4}>
            <Paper 
              sx={{ 
                p: 3, 
                textAlign: 'center', 
                height: '100%',
                cursor: 'pointer',
                '&:hover': { boxShadow: 6 },
                transition: 'all 0.3s'
              }}
              onClick={() => navigate('/quote')}
            >
              <BusIcon sx={{ fontSize: 60, color: 'primary.main', mb: 2 }} />
              <Typography variant="h6" gutterBottom fontWeight="bold">
                Short Notice Bookings
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Need a bus this week? We specialize in finding buses when others cannot, even at the 
                last minute.
              </Typography>
            </Paper>
          </Grid>
        </Grid>
      </Container>

      {/* Final CTA Section */}
      <Box sx={{ bgcolor: 'primary.main', color: 'white', py: 8, textAlign: 'center' }}>
        <Container maxWidth="md">
          <Typography variant="h3" gutterBottom fontWeight="bold">
            Ready to Book Your Charter?
          </Typography>
          <Typography variant="h6" sx={{ mb: 4, fontWeight: 300 }}>
            Get a personalized quote in minutes. Our team responds 24/7.
          </Typography>
          <Button
            variant="contained"
            size="large"
            onClick={() => navigate('/quote')}
            sx={{
              bgcolor: '#4caf50',
              color: 'white',
              px: 6,
              py: 2.5,
              fontSize: '1.2rem',
              fontWeight: 'bold',
              '&:hover': {
                bgcolor: '#45a049'
              }
            }}
          >
            Request a Quote Now
          </Button>
          <Typography variant="body2" sx={{ mt: 3, opacity: 0.9 }}>
            Or call us 24/7 for immediate assistance
          </Typography>
        </Container>
      </Box>

      {/* Footer */}
      <Box sx={{ bgcolor: 'grey.900', color: 'grey.400', py: 3 }}>
        <Container maxWidth="lg">
          <Typography variant="body2" align="center">
            © 2026 Athena Charter Services | Professional Charter Bus Rentals Nationwide
          </Typography>
        </Container>
      </Box>
    </Box>
  )
}
