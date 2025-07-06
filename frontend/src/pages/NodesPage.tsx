import React, { useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Button,
  Container,
  Grid,
  Paper,
  Typography,
  CircularProgress,
  Alert,
} from '@mui/material';
import { Add as AddIcon } from '@mui/icons-material';
import { styled } from '@mui/material/styles';
import { getNodes } from '../services/nodeService';
import NodeList from '../components/nodes/NodeList';
import NodeDetails from '../components/nodes/NodeDetails';

const StyledContainer = styled(Container)(({ theme }) => ({
  paddingTop: theme.spacing(3),
  paddingBottom: theme.spacing(3),
}));

const NodesPage: React.FC = () => {
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [isDrawerOpen, setIsDrawerOpen] = useState(true);
  const queryClient = useQueryClient();
  
  // Fetch nodes
  const { data: nodesData, isLoading, isError } = useQuery(['nodes'], getNodes);
  
  // Set first node as selected by default if none selected
  React.useEffect(() => {
    if (nodesData?.data?.length > 0 && !selectedNodeId) {
      setSelectedNodeId(nodesData.data[0]?.id);
    }
  }, [nodesData, selectedNodeId]);
  
  const handleNodeSelect = (nodeId: string) => {
    setSelectedNodeId(nodeId);
  };
  
  const handleAddNode = () => {
    // TODO: Implement add node dialog
    console.log('Add new node');
  };
  
  const toggleDrawer = () => {
    setIsDrawerOpen(!isDrawerOpen);
  };
  
  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
        <CircularProgress />
      </Box>
    );
  }
  
  if (isError) {
    return (
      <Box textAlign="center" p={3}>
        <Alert severity="error">
          Ошибка при загрузке списка нод. Пожалуйста, обновите страницу.
        </Alert>
      </Box>
    );
  }
  
  const nodes = nodesData?.data || [];
  const selectedNode = nodes.find(node => node.id === selectedNodeId) || null;

  return (
    <StyledContainer maxWidth={false}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1">
          Управление нодами
        </Typography>
        <Button
          variant="contained"
          color="primary"
          startIcon={<AddIcon />}
          onClick={handleAddNode}
        >
          Добавить ноду
        </Button>
      </Box>
      
      <Grid container spacing={3}>
        {/* Node List */}
        <Grid item xs={12} md={isDrawerOpen ? 5 : 12}>
          <NodeList 
            nodes={nodes} 
            selectedNodeId={selectedNodeId}
            onSelectNode={handleNodeSelect}
          />
        </Grid>
        
        {/* Node Details */}
        {selectedNode && isDrawerOpen && (
          <Grid item xs={12} md={7}>
            <NodeDetails 
              node={selectedNode} 
              onClose={() => setIsDrawerOpen(false)}
            />
          </Grid>
        )}
      </Grid>
    </StyledContainer>
  );
};

export default NodesPage;
