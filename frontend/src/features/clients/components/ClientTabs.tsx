/**
 * Client Tabs Component
 * Shared tab navigation for Client pages
 */
import { useState } from 'react'
import {
  Paper,
  Tabs,
  Tab,
  Box
} from '@mui/material'

interface TabPanelProps {
  children?: React.ReactNode
  index: number
  value: number
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props
  return (
    <div hidden={value !== index} {...other}>
      {value === index && <Box sx={{ pt: 3 }}>{children}</Box>}
    </div>
  )
}

export function ClientTabs({ children }: { children: React.ReactNode }) {
  const [tab, setTab] = useState(0)

  const handleChangeTab = (_event: React.SyntheticEvent, newValue: number) => {
    setTab(newValue)
  }

  return (
    <Paper>
      <Tabs value={tab} onChange={handleChangeTab}>
        <Tab label="Details" />
        <Tab label="Trip History" />
        <Tab label="Payments" />
        <Tab label="Documents" />
        <Tab label="Notes & Activity" />
      </Tabs>
      {children}
    </Paper>
  )
}

export { TabPanel }
