import React from 'react';
import { View, Text, StyleSheet, ScrollView } from 'react-native';

export default function AlertDetailScreen({ route }) {
  const { alert } = route.params || {};

  if (!alert) {
    return (
      <View style={styles.container}>
        <Text style={styles.empty}>No alert data</Text>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container} contentContainerStyle={{ padding: 20 }}>
      <Text style={styles.title}>{alert.alert_type}</Text>
      {alert.subtype ? <Text style={styles.sub}>{alert.subtype}</Text> : null}

      <View style={styles.row}>
        <Text style={styles.label}>Priority</Text>
        <Text style={[styles.value, alert.priority === 'HIGH' && { color: '#ef4444' }]}>
          {alert.priority || 'LOW'}
        </Text>
      </View>
      <View style={styles.row}>
        <Text style={styles.label}>Camera</Text>
        <Text style={styles.value}>{alert.camera_id}</Text>
      </View>
      <View style={styles.row}>
        <Text style={styles.label}>Confidence</Text>
        <Text style={styles.value}>
          {alert.confidence ? `${(alert.confidence * 100).toFixed(1)}%` : 'N/A'}
        </Text>
      </View>
      <View style={styles.row}>
        <Text style={styles.label}>Status</Text>
        <Text style={styles.value}>{alert.status}</Text>
      </View>
      <View style={styles.row}>
        <Text style={styles.label}>Time</Text>
        <Text style={styles.value}>
          {alert.timestamp ? new Date(alert.timestamp).toLocaleString() : '—'}
        </Text>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#020617' },
  title: { color: '#f8fafc', fontSize: 22, fontWeight: '700', marginBottom: 4 },
  sub: { color: '#94a3b8', fontSize: 15, marginBottom: 20 },
  row: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#1e293b',
  },
  label: { color: '#64748b', fontSize: 14 },
  value: { color: '#e2e8f0', fontSize: 14, fontWeight: '500' },
  empty: { color: '#64748b', textAlign: 'center', marginTop: 40 },
});
