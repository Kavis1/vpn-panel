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
import Layout from '../components/Layout';

const StyledContainer = styled(Container)(({ theme }) => ({
  paddingTop: theme.spacing(3),
  paddingBottom: theme.spacing(3),
}));

const NodesPage: React.FC = () => {
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [isDrawerOpen, setIsDrawerOpen] = useState(true);
  const queryClient = useQueryClient();
  
  // Fetch nodes
  const { data: nodesData, isLoading, isError } = useQuery({
    queryKey: ['nodes'],
    queryFn: getNodes
  });
  
  // Set first node as selected by default if none selected
  React.useEffect(() => {
    if ((nodesData as any)?.data?.length > 0 && !selectedNodeId) {
      setSelectedNodeId((nodesData as any).data[0]?.id);
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
    <Layout>
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
      
      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 3 }}>
        {/* Node List */}
        <Box sx={{ flex: isDrawerOpen ? '0 0 40%' : '1', minWidth: '300px' }}>
          <NodeList 
            nodes={nodes} 
            selectedNodeId={selectedNodeId}
            onSelectNode={handleNodeSelect}
          />
        </Box>

        {/* Node Details */}
        {selectedNode && isDrawerOpen && (
          <Box sx={{ flex: '1 1 500px', minWidth: '500px' }}>
            <NodeDetails 
              node={selectedNode as any}
              onClose={() => setIsDrawerOpen(false)}
            />
          </Box>
        )}
      </Box>
    </Layout>
  );
};

export default NodesPage;
