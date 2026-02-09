/**
 * Client Notes & Activity Tab Component
 */
import {
  Box,
  Typography,
  TextField,
  Button,
  Paper,
  List,
  ListItem,
  ListItemText,
  ListItemAvatar,
  Avatar,
  IconButton,
  Divider,
  Chip
} from '@mui/material'
import { useState } from 'react'
import { format } from 'date-fns'
import { Add as AddIcon, Delete as DeleteIcon } from '@mui/icons-material'

interface ClientNotesTabProps {
  clientId: number
}

export default function ClientNotesTab({ clientId }: ClientNotesTabProps) {
  // clientId is available for future integration with API
  void clientId
  
  const [notes, setNotes] = useState('')
  const [noteList, setNoteList] = useState([
    {
      id: 1,
      user: 'Admin',
      content: 'Client requested premium vehicle for upcoming trip',
      timestamp: new Date('2026-02-08T10:30:00'),
      type: 'note'
    },
    {
      id: 2,
      user: 'System',
      content: 'Payment of $250.00 received',
      timestamp: new Date('2026-02-07T14:15:00'),
      type: 'system'
    },
    {
      id: 3,
      user: 'Admin',
      content: 'COI expiring in 30 days - follow up',
      timestamp: new Date('2026-02-06T09:00:00'),
      type: 'note'
    }
  ])

  const addNote = () => {
    if (!notes.trim()) return
    
    const newNote = {
      id: noteList.length + 1,
      user: 'Current User',
      content: notes,
      timestamp: new Date(),
      type: 'note'
    }
    
    setNoteList([newNote, ...noteList])
    setNotes('')
  }

  return (
    <Box>
      {/* Add Note Form */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <TextField
          fullWidth
          multiline
          rows={3}
          variant="outlined"
          placeholder="Add a note..."
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          sx={{ mb: 2 }}
        />
        <Box display="flex" justifyContent="flex-end">
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={addNote}
            disabled={!notes.trim()}
          >
            Add Note
          </Button>
        </Box>
      </Paper>
      
      {/* Notes List */}
      <List>
        {noteList.map((note) => (
          <ListItem key={note.id} alignItems="flex-start">
            <ListItemAvatar>
              <Avatar sx={{ bgcolor: note.type === 'system' ? 'grey.500' : 'primary.main' }}>
                {note.user.charAt(0)}
              </Avatar>
            </ListItemAvatar>
            <ListItemText
              primary={
                <Typography variant="body2" sx={{ mb: 0.5 }}>
                  {note.content}
                </Typography>
              }
              secondary={
                <Box display="flex" alignItems="center" gap={1}>
                  <Typography variant="caption" color="text.secondary">
                    {format(note.timestamp, 'MMM dd, yyyy HH:mm')}
                  </Typography>
                  {note.type === 'system' && (
                    <Chip
                      label="SYSTEM"
                      size="small"
                      sx={{ height: 20 }}
                    />
                  )}
                </Box>
              }
            />
            {note.type === 'note' && (
              <IconButton size="small" sx={{ ml: 1 }}>
                <DeleteIcon fontSize="small" />
              </IconButton>
            )}
            {note.id < noteList.length && <Divider variant="inset" component="li" />}
          </ListItem>
        ))}
      </List>
      
      {noteList.length === 0 && (
        <Box textAlign="center" py={4}>
          <Typography color="text.secondary">
            No notes yet. Add one above!
          </Typography>
        </Box>
      )}
    </Box>
  )
}
