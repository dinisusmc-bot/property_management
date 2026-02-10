import React from 'react';
import { Box, Typography, Grid } from '@mui/material';
import { ReactiveCard } from '../components/ReactiveCard';
import { DashboardLayout } from '../components/DashboardLayout';
import PeopleIcon from '@mui/icons-material/People';
import HomeWorkIcon from '@mui/icons-material/HomeWork';
import BuildIcon from '@mui/icons-material/Build';
import PaymentIcon from '@mui/icons-material/Payment';

const Dashboard: React.FC = () => {
  return (
    <DashboardLayout>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h2" fontWeight={700} gutterBottom>
          Overview
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Welcome back! Here's what's happening with your properties today.
        </Typography>
      </Box>

      <Grid container spacing={3}>
        <Grid item xs={12} sm={6} md={3}>
          <ReactiveCard
            title="Total Properties"
            value={12}
            subtitle="+2 this month"
            color="primary"
            icon={<HomeWorkIcon />}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <ReactiveCard
            title="Occupied Units"
            value={28}
            subtitle="85% occupancy rate"
            color="success"
            icon={<PeopleIcon />}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <ReactiveCard
            title="Maintenance Requests"
            value={5}
            subtitle="3 pending approval"
            color="warning"
            icon={<BuildIcon />}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <ReactiveCard
            title="Monthly Revenue"
            value="$42,500"
            subtitle="+12% vs last month"
            color="primary"
            icon={<PaymentIcon />}
          />
        </Grid>
      </Grid>
    </DashboardLayout>
  );
};

export default Dashboard;
