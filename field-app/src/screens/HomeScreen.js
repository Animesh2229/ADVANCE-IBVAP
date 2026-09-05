import React, { useState, useEffect, useCallback } from 'react';
import {
  View, Text, FlatList, TouchableOpacity, StyleSheet,
  RefreshControl, Alert
} from 'react-native';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';

export default function HomeScreen({ navigation }) {
  const { user, logout } = useAuth();
  const [alerts, setAlerts] = useState([]);
  const [refreshing, setRefreshing] = useState(false);

  const fetchAlerts = useCallback(async () => {
    try {
      const res = await api.get('/alerts?limit=40');
      const critical = (res.data || []).filter(
        a => a.priority === 'HIGH' || a.priority === 'MEDIUM' || a.status === 'new'
      );
      setAlerts(critical.length ? critical : res.data || []);
    } catch (err) {
      console.warn('Failed to fetch alerts', err.message);
    }
  }, []);

  useEffect(() => {
    fetchAlerts();
    const interval = setInterval(fetchAlerts, 8000);
    return () => clearInterval(interval);
  }, [fetchAlerts]);

  const onRefresh = async () => {
    setRefreshing(true);
    await fetchAlerts();
    setRefreshing(false);
  };

  const handleAction = async (alertId, action) => {
    try {
      await api.post(`/alerts/${alertId}/action`, { action });
      Alert.alert('Success', action === 'acknowledged' ? 'Alert acknowledged' : 'En-route recorded');
      fetchAlerts();
    } catch (err) {
      Alert.alert('Error', 'Failed to update alert');
    }
  };

  const renderItem = ({ item }) => (
    <TouchableOpacity
      style={[styles.card, item.priority === 'HIGH' && styles.highPriority]}
      onPress={() => navigation.navigate('AlertDetail', { alert: item })}
    >
      <View style={styles.cardHeader}>
        <Text style={styles.type}>{item.alert_type} {item.subtype ? `• ${item.subtype}` : ''}</Text>
        <Text style={styles.priority}>{item.priority || 'LOW'}</Text>
      </View>
      <Text style={styles.camera}>Camera: {item.camera_id}</Text>
      <Text style={styles.time}>
        {item.timestamp ? new Date(item.timestamp).toLocaleString() : ''}
      </Text>
      <View style={styles.actions}>
        <TouchableOpacity
          style={styles.ackBtn}
          onPress={() => handleAction(item.id, 'acknowledged')}
        >
          <Text style={styles.btnText}>Acknowledge</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={styles.enrouteBtn}
          onPress={() => handleAction(item.id, 'en_route')}
        >
          <Text style={styles.btnText}>Main ja raha hoon</Text>
        </TouchableOpacity>
      </View>
    </TouchableOpacity>
  );

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.greeting}>Namaste, {user?.full_name || user?.username}</Text>
        <TouchableOpacity onPress={logout}>
          <Text style={styles.logout}>Logout</Text>
        </TouchableOpacity>
      </View>

      <FlatList
        data={alerts}
        keyExtractor={(item) => String(item.id)}
        renderItem={renderItem}
        contentContainerStyle={{ padding: 16, paddingBottom: 40 }}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="#3b82f6" />}
        ListEmptyComponent={
          <Text style={styles.empty}>No critical alerts right now. Stay alert.</Text>
        }
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#020617' },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#1e293b',
  },
  greeting: { color: '#f1f5f9', fontSize: 16, fontWeight: '600' },
  logout: { color: '#f87171', fontSize: 14 },
  card: {
    backgroundColor: '#0f172a',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#1e293b',
  },
  highPriority: { borderLeftWidth: 4, borderLeftColor: '#ef4444' },
  cardHeader: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 6 },
  type: { color: '#f8fafc', fontWeight: '600', fontSize: 15, flex: 1 },
  priority: { color: '#fbbf24', fontSize: 12, fontWeight: '700' },
  camera: { color: '#94a3b8', fontSize: 13 },
  time: { color: '#64748b', fontSize: 12, marginTop: 4 },
  actions: { flexDirection: 'row', gap: 10, marginTop: 12 },
  ackBtn: {
    backgroundColor: '#1e40af',
    paddingVertical: 8,
    paddingHorizontal: 14,
    borderRadius: 8,
  },
  enrouteBtn: {
    backgroundColor: '#065f46',
    paddingVertical: 8,
    paddingHorizontal: 14,
    borderRadius: 8,
  },
  btnText: { color: '#fff', fontSize: 13, fontWeight: '600' },
  empty: { color: '#64748b', textAlign: 'center', marginTop: 60, fontSize: 15 },
});
