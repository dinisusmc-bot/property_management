import { useEffect, useState } from 'react'
import { Box, Grid, Paper, Typography, Card, CardContent, CircularProgress } from '@mui/material'
import {
  DirectionsBus as BusIcon,
  People as PeopleIcon,
  AttachMoney as MoneyIcon,
  TrendingUp as TrendingIcon,
} from '@mui/icons-material'
import api from '../services/api'

interface StatCardProps {
  title: string
  value: string | number
  icon: React.ReactNode
  color: string
  loading?: boolean
}

function StatCard({ title, value, icon, color, loading }: StatCardProps) {
  return (
    <Card>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <Box
            sx={{
              bgcolor: color,
              borderRadius: 2,
              p: 1.5,
              color: 'white',
              mr: 2,
            }}
          >
            {icon}
          </Box>
          <Typography variant="h6" color="textSecondary">
            {title}
          </Typography>
        </Box>
        <Typography variant="h4" fontWeight="bold">
          {loading ? <CircularProgress size={32} /> : value}
        </Typography>
      </CardContent>
    </Card>
  )
}

interface DashboardStats {
  totalCharters: number
  activeCharters: number
  totalClients: number
  monthlyRevenue: number
}

export default function Dashboard() {
  const [stats, setStats] = useState<DashboardStats>({
    totalCharters: 0,
    activeCharters: 0,
    totalClients: 0,
    monthlyRevenue: 0,
  })
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchDashboardData()
  }, [])

  const fetchDashboardData = async () => {
    try {
      setLoading(true)
      
      // Fetch clients
      const clientsResponse = await api.get('/api/v1/clients/clients')
      const clients = clientsResponse.data
      
      // Fetch charters
      const chartersResponse = await api.get('/api/v1/charters/charters')
      const charters = chartersResponse.data
      
      // Calculate stats
      const activeCharters = charters.filter((c: any) => 
        c.status === 'confirmed' || c.status === 'pending'
      ).length
      
      const monthlyRevenue = charters.reduce((sum: number, c: any) => 
        sum + (c.total_cost || 0), 0
      )
      
      setStats({
        totalCharters: charters.length,
        activeCharters: activeCharters,
        totalClients: clients.length,
        monthlyRevenue: monthlyRevenue,
      })
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Dashboard
      </Typography>
      <Typography variant="body1" color="textSecondary" sx={{ mb: 4 }}>
        Welcome to Athena Charter Management System
      </Typography>

      <Grid container spacing={3}>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Active Charters"
            value={stats.activeCharters}
            icon={<BusIcon />}
            color="#1976d2"
            loading={loading}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Total Clients"
            value={stats.totalClients}
            icon={<PeopleIcon />}
            color="#2e7d32"
            loading={loading}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Total Revenue"
            value={`$${stats.monthlyRevenue.toFixed(2)}`}
            icon={<MoneyIcon />}
            color="#ed6c02"
            loading={loading}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Total Charters"
            value={stats.totalCharters}
            icon={<TrendingIcon />}
            color="#0288d1"
            loading={loading}
          />
        </Grid>

        <Grid item xs={12}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              System Overview
            </Typography>
            <Typography variant="body2" color="textSecondary">
              You have {stats.totalClients} clients and {stats.totalCharters} charters in the system.
              {stats.activeCharters > 0 && ` Currently ${stats.activeCharters} charters are active.`}
            </Typography>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  )
}
