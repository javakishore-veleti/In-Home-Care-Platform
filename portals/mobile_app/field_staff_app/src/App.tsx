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
  const [screen, setScreen] = useState<'list' | 'visit'>('list');

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor={COLORS.primary} />
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Field Staff</Text>
        <Text style={styles.headerSub}>Today's Assignments</Text>
      </View>

      <ScrollView style={styles.content}>
        {visits.map(v => (
          <TouchableOpacity key={v.id} style={styles.card} onPress={() => setScreen('visit')}>
            <View style={styles.cardHeader}>
              <Text style={styles.cardTitle}>{v.member}</Text>
              <View style={[styles.badge, { backgroundColor: v.status === 'Next' ? COLORS.secondary : COLORS.info }]}>
                <Text style={styles.badgeText}>{v.status}</Text>
              </View>
            </View>
            <Text style={styles.cardDetail}>{v.type} · {v.time}</Text>
            <Text style={styles.cardAddress}>{v.address}</Text>
          </TouchableOpacity>
        ))}
      </ScrollView>

      <View style={styles.bottomBar}>
        <TouchableOpacity style={styles.bottomBtn}>
          <Text style={styles.bottomBtnText}>Assignments</Text>
        </TouchableOpacity>
        <TouchableOpacity style={[styles.bottomBtn, styles.bottomBtnActive]}>
          <Text style={[styles.bottomBtnText, { color: COLORS.white }]}>Record Visit</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.bottomBtn}>
          <Text style={styles.bottomBtnText}>Camera</Text>
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
  bottomBar: { flexDirection: 'row', borderTopWidth: 2, borderColor: COLORS.primary, backgroundColor: COLORS.white },
  bottomBtn: { flex: 1, paddingVertical: 14, alignItems: 'center' },
  bottomBtnActive: { backgroundColor: COLORS.secondary },
  bottomBtnText: { fontWeight: 'bold', color: COLORS.text, fontSize: 13 },
});
