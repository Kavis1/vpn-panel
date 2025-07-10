import React from 'react';
import {
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Typography,
  IconButton,
  Tooltip,
  Box,
  useTheme,
} from '@mui/material';
import {
  CloudQueue as CloudQueueIcon,
  CloudOff as CloudOffIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
} from '@mui/icons-material';
import { styled } from '@mui/material/styles';
import { Node } from '../../services/nodeService';

const StyledTableRow = styled(TableRow)(({ theme }) => ({
  '&:nth-of-type(odd)': {
    backgroundColor: theme.palette.action.hover,
  },
  '&:last-child td, &:last-child th': {
    border: 0,
  },
  '&:hover': {
    backgroundColor: theme.palette.action.selected,
    cursor: 'pointer',
  },
}));

const StatusChip = styled('span')<{ status: string }>(({ theme, status }) => ({
  display: 'inline-flex',
  alignItems: 'center',
  padding: '4px 8px',
  borderRadius: 16,
  fontSize: '0.75rem',
  fontWeight: 600,
  backgroundColor: status === 'online'
    ? theme.palette.success.light
    : status === 'offline'
    ? theme.palette.error.light
    : theme.palette.warning.light,
  color: status === 'online'
    ? theme.palette.success.contrastText
    : status === 'offline'
    ? theme.palette.error.contrastText
    : theme.palette.warning.contrastText,
}));

interface NodeListProps {
  nodes: Node[];
  selectedNodeId: string | null;
  onSelectNode: (nodeId: string) => void;
  onEditNode?: (node: Node) => void;
  onDeleteNode?: (node: Node) => void;
}

const NodeList: React.FC<NodeListProps> = ({
  nodes,
  selectedNodeId,
  onSelectNode,
  onEditNode,
  onDeleteNode,
}) => {
  const [page, setPage] = React.useState(0);
  const [rowsPerPage, setRowsPerPage] = React.useState(10);
  const theme = useTheme();

  const handleChangePage = (event: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };
  
  const handleRowClick = (nodeId: string) => {
    onSelectNode(nodeId);
  };
  
  const handleEditClick = (e: React.MouseEvent, node: Node) => {
    e.stopPropagation();
    if (onEditNode) onEditNode(node);
  };
  
  const handleDeleteClick = (e: React.MouseEvent, node: Node) => {
    e.stopPropagation();
    if (onDeleteNode) onDeleteNode(node);
  };
  
  // Avoid a layout jump when reaching the last page with empty rows.
  const emptyRows = page > 0 ? Math.max(0, (1 + page) * rowsPerPage - nodes.length) : 0;

  return (
    <Paper sx={{ width: '100%', overflow: 'hidden' }}>
      <TableContainer sx={{ maxHeight: 'calc(100vh - 200px)' }}>
        <Table stickyHeader aria-label="nodes table" size="small">
          <TableHead>
            <TableRow>
              <TableCell>Имя</TableCell>
              <TableCell>Хост</TableCell>
              <TableCell>Статус</TableCell>
              <TableCell>Пользователи</TableCell>
              <TableCell align="right">Действия</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {nodes
              .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
              .map((node) => (
                <StyledTableRow 
                  key={node.id} 
                  hover 
                  selected={selectedNodeId === node.id}
                  onClick={() => handleRowClick(node.id)}
                >
                  <TableCell>
                    <Box display="flex" alignItems="center">
                      {node.status === 'online' ? (
                        <CloudQueueIcon 
                          color="success" 
                          fontSize="small" 
                          sx={{ mr: 1 }} 
                        />
                      ) : (
                        <CloudOffIcon 
                          color="error" 
                          fontSize="small" 
                          sx={{ mr: 1 }} 
                        />
                      )}
                      <Typography variant="body2">
                        {node.name}
                      </Typography>
                    </Box>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">
                      {node.host}:{node.port}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <StatusChip status={node.status}>
                      {node.status === 'online' ? 'Онлайн' : 'Оффлайн'}
                    </StatusChip>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">
                      {node.current_users || 0} / {node.max_users || '∞'}
                    </Typography>
                  </TableCell>
                  <TableCell align="right">
                    {onEditNode && (
                      <Tooltip title="Редактировать">
                        <IconButton 
                          size="small"
                          onClick={(e) => handleEditClick(e, node)}
                        >
                          <EditIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    )}
                    {onDeleteNode && (
                      <Tooltip title="Удалить">
                        <IconButton 
                          size="small"
                          color="error"
                          onClick={(e) => handleDeleteClick(e, node)}
                        >
                          <DeleteIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    )}
                  </TableCell>
                </StyledTableRow>
              ))}
            
            {emptyRows > 0 && (
              <TableRow style={{ height: 53 * emptyRows }}>
                <TableCell colSpan={5} />
              </TableRow>
            )}
            
            {nodes.length === 0 && (
              <TableRow>
                <TableCell colSpan={5} align="center" sx={{ py: 4 }}>
                  <Typography variant="body1" color="textSecondary">
                    Ноды не найдены
                  </Typography>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>
      
      <TablePagination
        rowsPerPageOptions={[5, 10, 25]}
        component="div"
        count={nodes.length}
        rowsPerPage={rowsPerPage}
        page={page}
        onPageChange={handleChangePage}
        onRowsPerPageChange={handleChangeRowsPerPage}
        labelRowsPerPage="Строк на странице:"
        labelDisplayedRows={({ from, to, count }) => 
          `${from}-${to} из ${count !== -1 ? count : `больше чем ${to}`}`
        }
      />
    </Paper>
  );
};

export default NodeList;
