import React, { useState } from 'react';
import { View, Text, ScrollView, TouchableOpacity, StyleSheet, SafeAreaView, StatusBar } from 'react-native';

const COLORS = {
  primary: '#0D7377',
  primaryDark: '#084C4F',
  secondary: '#E8612D',
  text: '#1A2B3C',
  textMuted: '#3D5A73',
  success: '#2D8A4E',
  info: '#1976D2',
  warning: '#E8A317',
  white: '#FFFFFF',
};

const visits = [
  { id: 'V-2001', member: 'A. Johnson', address: '123 Oak Lane', time: '9:00 AM', type: 'Skilled Nursing', status: 'Next' },
  { id: 'V-2002', member: 'R. Williams', address: '456 Elm St', time: '11:30 AM', type: 'Physical Therapy', status: 'Upcoming' },
  { id: 'V-2003', member: 'S. Davis', address: '789 Pine Ave', time: '2:00 PM', type: 'Home Health Aide', status: 'Upcoming' },
];

export default function App() {
  const [tab, setTab] = useState('assignments');

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor={COLORS.primary} />

      <View style={styles.header}>
        <Text style={styles.headerTitle}>Field Staff</Text>
        <Text style={styles.headerSub}>Today's Assignments</Text>
      </View>

      <ScrollView style={styles.content}>
        {visits.map(v => (
          <TouchableOpacity key={v.id} style={styles.card}>
            <View style={styles.cardHeader}>
              <Text style={styles.cardTitle}>{v.member}</Text>
              <View style={[styles.badge, { backgroundColor: v.status === 'Next' ? COLORS.secondary : COLORS.info }]}>
                <Text style={styles.badgeText}>{v.status}</Text>
              </View>
            </View>
            <Text style={styles.cardDetail}>{v.type} - {v.time}</Text>
            <Text style={styles.cardAddress}>{v.address}</Text>
          </TouchableOpacity>
        ))}

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Quick Actions</Text>
          <TouchableOpacity style={styles.actionBtn}>
            <Text style={styles.actionBtnText}>Start Next Visit</Text>
          </TouchableOpacity>
          <TouchableOpacity style={[styles.actionBtn, { backgroundColor: COLORS.primary }]}>
            <Text style={styles.actionBtnText}>Record Visit Notes</Text>
          </TouchableOpacity>
          <TouchableOpacity style={[styles.actionBtn, { backgroundColor: COLORS.info }]}>
            <Text style={styles.actionBtnText}>Capture Document</Text>
          </TouchableOpacity>
        </View>
      </ScrollView>

      <View style={styles.bottomBar}>
        <TouchableOpacity
          style={[styles.bottomBtn, tab === 'assignments' && styles.bottomBtnActive]}
          onPress={() => setTab('assignments')}>
          <Text style={[styles.bottomBtnText, tab === 'assignments' && { color: COLORS.white }]}>Assignments</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.bottomBtn, tab === 'record' && styles.bottomBtnActive]}
          onPress={() => setTab('record')}>
          <Text style={[styles.bottomBtnText, tab === 'record' && { color: COLORS.white }]}>Record</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.bottomBtn, tab === 'camera' && styles.bottomBtnActive]}
          onPress={() => setTab('camera')}>
          <Text style={[styles.bottomBtnText, tab === 'camera' && { color: COLORS.white }]}>Camera</Text>
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.white },
  header: { backgroundColor: COLORS.primary, paddingHorizontal: 20, paddingTop: 16, paddingBottom: 20 },
  headerTitle: { color: COLORS.white, fontSize: 24, fontWeight: 'bold' },
  headerSub: { color: '#B2DFDB', fontSize: 14, marginTop: 4 },
  content: { flex: 1, padding: 16 },
  card: { borderWidth: 2, borderColor: COLORS.primary, borderRadius: 12, padding: 16, marginBottom: 12 },
  cardHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  cardTitle: { fontSize: 18, fontWeight: 'bold', color: COLORS.text },
  badge: { paddingHorizontal: 10, paddingVertical: 4, borderRadius: 12 },
  badgeText: { color: COLORS.white, fontSize: 12, fontWeight: 'bold' },
  cardDetail: { fontSize: 14, color: COLORS.textMuted, marginTop: 6 },
  cardAddress: { fontSize: 13, color: COLORS.textMuted, marginTop: 2 },
  section: { marginTop: 20 },
  sectionTitle: { fontSize: 18, fontWeight: 'bold', color: COLORS.text, marginBottom: 12 },
  actionBtn: { backgroundColor: COLORS.secondary, borderRadius: 10, paddingVertical: 14, alignItems: 'center', marginBottom: 10 },
  actionBtnText: { color: COLORS.white, fontWeight: 'bold', fontSize: 16 },
  bottomBar: { flexDirection: 'row', borderTopWidth: 2, borderColor: COLORS.primary, backgroundColor: COLORS.white },
  bottomBtn: { flex: 1, paddingVertical: 14, alignItems: 'center' },
  bottomBtnActive: { backgroundColor: COLORS.secondary },
  bottomBtnText: { fontWeight: 'bold', color: COLORS.text, fontSize: 13 },
});
