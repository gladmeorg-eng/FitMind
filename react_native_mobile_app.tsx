"""
# ============================================================
# FILE: apps/mobile/src/App.tsx
# React Native Entry Point
# ============================================================

import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { StatusBar } from 'expo-status-bar';

import { AuthProvider, useAuth } from './contexts/AuthContext';
import { ThemeProvider } from './contexts/ThemeContext';

// Screens
import LoginScreen from './screens/LoginScreen';
import HomeScreen from './screens/HomeScreen';
import BookingScreen from './screens/BookingScreen';
import ProfileScreen from './screens/ProfileScreen';
import CheckInScreen from './screens/CheckInScreen';
import ClassDetailScreen from './screens/ClassDetailScreen';

// Components
import TabBarIcon from './components/TabBarIcon';

const Stack = createNativeStackNavigator();
const Tab = createBottomTabNavigator();

function MainTabs() {
  return (
    <Tab.Navigator
      screenOptions={{
        tabBarStyle: {
          backgroundColor: '#0a0a14',
          borderTopColor: '#1e1e3f',
          borderTopWidth: 1,
          paddingBottom: 8,
          paddingTop: 8,
          height: 70,
        },
        tabBarActiveTintColor: '#6366f1',
        tabBarInactiveTintColor: '#475569',
        headerShown: false,
      }}
    >
      <Tab.Screen
        name="Home"
        component={HomeScreen}
        options={{
          tabBarIcon: ({ color, size }) => (
            <TabBarIcon name="home" color={color} size={size} />
          ),
        }}
      />
      <Tab.Screen
        name="Book"
        component={BookingScreen}
        options={{
          tabBarIcon: ({ color, size }) => (
            <TabBarIcon name="calendar" color={color} size={size} />
          ),
        }}
      />
      <Tab.Screen
        name="CheckIn"
        component={CheckInScreen}
        options={{
          tabBarIcon: ({ color, size }) => (
            <TabBarIcon name="qr-code" color={color} size={size} />
          ),
        }}
      />
      <Tab.Screen
        name="Profile"
        component={ProfileScreen}
        options={{
          tabBarIcon: ({ color, size }) => (
            <TabBarIcon name="person" color={color} size={size} />
          ),
        }}
      />
    </Tab.Navigator>
  );
}

function AppNavigator() {
  const { isAuthenticated } = useAuth();

  return (
    <Stack.Navigator screenOptions={{ headerShown: false }}>
      {!isAuthenticated ? (
        <Stack.Screen name="Login" component={LoginScreen} />
      ) : (
        <>
          <Stack.Screen name="Main" component={MainTabs} />
          <Stack.Screen
            name="ClassDetail"
            component={ClassDetailScreen}
            options={{
              presentation: 'modal',
              animation: 'slide_from_bottom',
            }}
          />
        </>
      )}
    </Stack.Navigator>
  );
}

export default function App() {
  return (
    <SafeAreaProvider>
      <ThemeProvider>
        <AuthProvider>
          <NavigationContainer>
            <StatusBar style="light" />
            <AppNavigator />
          </NavigationContainer>
        </AuthProvider>
      </ThemeProvider>
    </SafeAreaProvider>
  );
}

// ============================================================
// FILE: apps/mobile/src/screens/LoginScreen.tsx
// Member Login Screen
// ============================================================

import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  KeyboardAvoidingView,
  Platform,
  ActivityIndicator,
  Image,
} from 'react-native';
import { useAuth } from '../contexts/AuthContext';

export default function LoginScreen() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const { login } = useAuth();

  async function handleLogin() {
    if (!email || !password) {
      setError('Please enter email and password');
      return;
    }

    setLoading(true);
    setError('');

    try {
      await login(email, password);
    } catch (err: any) {
      setError(err.message || 'Login failed');
    } finally {
      setLoading(false);
    }
  }

  return (
    <KeyboardAvoidingView
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      style={styles.container}
    >
      <View style={styles.content}>
        {/* Logo */}
        <View style={styles.logoContainer}>
          <Text style={styles.logoEmoji}>🏋️</Text>
          <Text style={styles.title}>FitMind AI</Text>
          <Text style={styles.subtitle}>Your gym, in your pocket</Text>
        </View>

        {/* Form */}
        <View style={styles.form}>
          <View style={styles.inputContainer}>
            <Text style={styles.label}>Email</Text>
            <TextInput
              style={styles.input}
              value={email}
              onChangeText={setEmail}
              placeholder="you@email.com"
              placeholderTextColor="#475569"
              keyboardType="email-address"
              autoCapitalize="none"
              autoCorrect={false}
            />
          </View>

          <View style={styles.inputContainer}>
            <Text style={styles.label}>Password</Text>
            <TextInput
              style={styles.input}
              value={password}
              onChangeText={setPassword}
              placeholder="••••••••"
              placeholderTextColor="#475569"
              secureTextEntry
            />
          </View>

          {error ? (
            <View style={styles.errorContainer}>
              <Text style={styles.errorText}>{error}</Text>
            </View>
          ) : null}

          <TouchableOpacity
            style={[styles.button, loading && styles.buttonDisabled]}
            onPress={handleLogin}
            disabled={loading}
          >
            {loading ? (
              <ActivityIndicator color="#fff" />
            ) : (
              <Text style={styles.buttonText}>Sign In</Text>
            )}
          </TouchableOpacity>

          <TouchableOpacity style={styles.forgotButton}>
            <Text style={styles.forgotText}>Forgot password?</Text>
          </TouchableOpacity>
        </View>

        {/* Footer */}
        <View style={styles.footer}>
          <Text style={styles.footerText}>
            Don't have an account?{' '}
            <Text style={styles.footerLink}>Contact your gym</Text>
          </Text>
        </View>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0a0a14',
  },
  content: {
    flex: 1,
    justifyContent: 'center',
    paddingHorizontal: 32,
  },
  logoContainer: {
    alignItems: 'center',
    marginBottom: 48,
  },
  logoEmoji: {
    fontSize: 64,
    marginBottom: 16,
  },
  title: {
    fontSize: 32,
    fontWeight: '900',
    color: '#fff',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: '#94a3b8',
  },
  form: {
    gap: 20,
  },
  inputContainer: {
    gap: 8,
  },
  label: {
    fontSize: 14,
    fontWeight: '700',
    color: '#94a3b8',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  input: {
    backgroundColor: '#1e1e3f',
    borderWidth: 1,
    borderColor: '#2d2d44',
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 14,
    color: '#fff',
    fontSize: 16,
  },
  errorContainer: {
    backgroundColor: 'rgba(239, 68, 68, 0.1)',
    borderWidth: 1,
    borderColor: 'rgba(239, 68, 68, 0.3)',
    borderRadius: 8,
    padding: 12,
  },
  errorText: {
    color: '#f87171',
    fontSize: 13,
  },
  button: {
    backgroundColor: '#6366f1',
    borderRadius: 12,
    paddingVertical: 16,
    alignItems: 'center',
    marginTop: 8,
  },
  buttonDisabled: {
    opacity: 0.5,
  },
  buttonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '800',
  },
  forgotButton: {
    alignItems: 'center',
    marginTop: 8,
  },
  forgotText: {
    color: '#6366f1',
    fontSize: 14,
    fontWeight: '600',
  },
  footer: {
    marginTop: 32,
    alignItems: 'center',
  },
  footerText: {
    color: '#64748b',
    fontSize: 14,
  },
  footerLink: {
    color: '#6366f1',
    fontWeight: '700',
  },
});

// ============================================================
// FILE: apps/mobile/src/screens/HomeScreen.tsx
// Member Home Dashboard
// ============================================================

import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  RefreshControl,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { api } from '../api/client';
import { useAuth } from '../contexts/AuthContext';

interface MemberProfile {
  id: string;
  first_name: string;
  last_name: string;
  membership_type: string;
  visit_streak: number;
  total_visits: number;
  total_classes: number;
  retention_score: number;
}

interface UpcomingClass {
  id: string;
  class_type: { name: string; color: string; icon: string };
  class_date: string;
  start_time: string;
  room: string;
  coach: { first_name: string; last_name: string };
}

interface AiInsight {
  strength_areas: string[];
  recommended_classes: any[];
  milestone_progress: { current: number; target: number; type: string };
}

export default function HomeScreen() {
  const navigation = useNavigation();
  const { token } = useAuth();
  const [profile, setProfile] = useState<MemberProfile | null>(null);
  const [upcoming, setUpcoming] = useState<UpcomingClass[]>([]);
  const [insights, setInsights] = useState<AiInsight | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  async function loadData() {
    try {
      const [profileRes, upcomingRes, insightsRes] = await Promise.all([
        api.get('/member/me', { headers: { Authorization: `Bearer ${token}` } }),
        api.get('/member/classes/available', { headers: { Authorization: `Bearer ${token}` } }),
        api.get('/member/ai-insights', { headers: { Authorization: `Bearer ${token}` } }),
      ]);

      setProfile(profileRes.data);
      setUpcoming(profileRes.data.upcoming_classes || []);
      setInsights(profileRes.data.ai_insights);
    } catch (err) {
      console.error('Failed to load home data:', err);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  const onRefresh = async () => {
    setRefreshing(true);
    await loadData();
    setRefreshing(false);
  };

  return (
    <ScrollView
      style={styles.container}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="#6366f1" />
      }
    >
      {/* Header */}
      <View style={styles.header}>
        <View>
          <Text style={styles.greeting}>Good morning,</Text>
          <Text style={styles.name}>{profile?.first_name || 'Member'} 👋</Text>
        </View>
        <View style={styles.streakBadge}>
          <Text style={styles.streakEmoji}>🔥</Text>
          <Text style={styles.streakText}>{profile?.visit_streak || 0}</Text>
        </View>
      </View>

      {/* Stats Row */}
      <View style={styles.statsRow}>
        <StatCard label="Classes" value={profile?.total_classes || 0} color="#8b5cf6" />
        <StatCard label="Visits" value={profile?.total_visits || 0} color="#10b981" />
        <StatCard label="Streak" value={profile?.visit_streak || 0} color="#f59e0b" />
      </View>

      {/* AI Coach Insights */}
      {insights && (
        <View style={styles.insightsCard}>
          <View style={styles.insightsHeader}>
            <Text style={styles.insightsIcon}>🧠</Text>
            <Text style={styles.insightsTitle}>AI Coach Insights</Text>
          </View>

          {insights.strength_areas?.length > 0 && (
            <View style={styles.insightItem}>
              <View style={[styles.insightBar, { backgroundColor: '#10b981' }]} />
              <Text style={styles.insightText}>
                <Text style={styles.insightHighlight}>Strength:</Text>{' '}
                {insights.strength_areas[0]}
              </Text>
            </View>
          )}

          {insights.milestone_progress && (
            <View style={styles.insightItem}>
              <View style={[styles.insightBar, { backgroundColor: '#f59e0b' }]} />
              <Text style={styles.insightText}>
                <Text style={styles.insightHighlight}>Milestone:</Text>{' '}
                {insights.milestone_progress.current}/{insights.milestone_progress.target}{' '}
                {insights.milestone_progress.type}
              </Text>
            </View>
          )}

          {insights.recommended_classes?.length > 0 && (
            <View style={styles.insightItem}>
              <View style={[styles.insightBar, { backgroundColor: '#8b5cf6' }]} />
              <Text style={styles.insightText}>
                <Text style={styles.insightHighlight}>Recommended:</Text>{' '}
                {insights.recommended_classes[0].name}
              </Text>
            </View>
          )}
        </View>
      )}

      {/* Upcoming Classes */}
      <View style={styles.section}>
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>📅 Up Next</Text>
          <TouchableOpacity onPress={() => navigation.navigate('Book' as never)}>
            <Text style={styles.seeAll}>See all →</Text>
          </TouchableOpacity>
        </View>

        {upcoming.length === 0 ? (
          <View style={styles.emptyState}>
            <Text style={styles.emptyEmoji}>📭</Text>
            <Text style={styles.emptyText}>No upcoming classes</Text>
            <TouchableOpacity
              style={styles.bookButton}
              onPress={() => navigation.navigate('Book' as never)}
            >
              <Text style={styles.bookButtonText}>Book a Class</Text>
            </TouchableOpacity>
          </View>
        ) : (
          upcoming.slice(0, 3).map((cls) => (
            <TouchableOpacity
              key={cls.id}
              style={styles.classCard}
              onPress={() => navigation.navigate('ClassDetail', { classId: cls.id } as never)}
            >
              <View style={[styles.classIcon, { backgroundColor: cls.class_type?.color || '#6366f1' }]}>
                <Text style={styles.classIconText}>
                  {cls.class_type?.icon === 'fire' ? '🔥' : 
                   cls.class_type?.icon === 'yoga' ? '🧘' : 
                   cls.class_type?.icon === 'bike' ? '🚴' : '🏋️'}
                </Text>
              </View>
              <View style={styles.classInfo}>
                <Text style={styles.className}>{cls.class_type?.name}</Text>
                <Text style={styles.classMeta}>
                  {cls.start_time} • {cls.room} • {cls.coach?.first_name}
                </Text>
              </View>
              <Text style={styles.classArrow}>→</Text>
            </TouchableOpacity>
          ))
        )}
      </View>

      {/* Quick Actions */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>⚡ Quick Actions</Text>
        <View style={styles.quickActions}>
          <QuickActionButton
            icon="📱"
            label="Check In"
            onPress={() => navigation.navigate('CheckIn' as never)}
          />
          <QuickActionButton
            icon="⏸️"
            label="Freeze"
            onPress={() => { /* Open freeze modal */ }}
          />
          <QuickActionButton
            icon="👥"
            label="Refer"
            onPress={() => { /* Open referral modal */ }}
          />
          <QuickActionButton
            icon="💬"
            label="Support"
            onPress={() => { /* Open support chat */ }}
          />
        </View>
      </View>
    </ScrollView>
  );
}

function StatCard({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <View style={styles.statCard}>
      <Text style={[styles.statValue, { color }]}>{value}</Text>
      <Text style={styles.statLabel}>{label}</Text>
    </View>
  );
}

function QuickActionButton({ icon, label, onPress }: { icon: string; label: string; onPress: () => void }) {
  return (
    <TouchableOpacity style={styles.quickAction} onPress={onPress}>
      <Text style={styles.quickActionIcon}>{icon}</Text>
      <Text style={styles.quickActionLabel}>{label}</Text>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0a0a14',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 24,
    paddingTop: 60,
    paddingBottom: 24,
  },
  greeting: {
    fontSize: 14,
    color: '#94a3b8',
  },
  name: {
    fontSize: 28,
    fontWeight: '900',
    color: '#fff',
    marginTop: 4,
  },
  streakBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#1e1e3f',
    borderRadius: 20,
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderWidth: 1,
    borderColor: '#2d2d44',
  },
  streakEmoji: {
    fontSize: 18,
    marginRight: 6,
  },
  streakText: {
    fontSize: 16,
    fontWeight: '800',
    color: '#f59e0b',
  },
  statsRow: {
    flexDirection: 'row',
    paddingHorizontal: 24,
    gap: 12,
    marginBottom: 24,
  },
  statCard: {
    flex: 1,
    backgroundColor: '#1e1e3f',
    borderRadius: 16,
    padding: 16,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#2d2d44',
  },
  statValue: {
    fontSize: 24,
    fontWeight: '900',
  },
  statLabel: {
    fontSize: 12,
    color: '#64748b',
    marginTop: 4,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  insightsCard: {
    marginHorizontal: 24,
    backgroundColor: '#1e1e3f',
    borderRadius: 16,
    padding: 20,
    borderWidth: 1,
    borderColor: '#2d2d44',
    marginBottom: 24,
  },
  insightsHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  insightsIcon: {
    fontSize: 20,
    marginRight: 10,
  },
  insightsTitle: {
    fontSize: 16,
    fontWeight: '800',
    color: '#fff',
  },
  insightItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  insightBar: {
    width: 3,
    height: '100%',
    borderRadius: 2,
    marginRight: 12,
    minHeight: 20,
  },
  insightText: {
    flex: 1,
    fontSize: 13,
    color: '#cbd5e1',
    lineHeight: 20,
  },
  insightHighlight: {
    fontWeight: '700',
    color: '#fff',
  },
  section: {
    paddingHorizontal: 24,
    marginBottom: 24,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '800',
    color: '#fff',
  },
  seeAll: {
    fontSize: 14,
    color: '#6366f1',
    fontWeight: '700',
  },
  classCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#0f0f1a',
    borderRadius: 12,
    padding: 14,
    marginBottom: 10,
    borderWidth: 1,
    borderColor: '#1e1e3f',
  },
  classIcon: {
    width: 48,
    height: 48,
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 14,
  },
  classIconText: {
    fontSize: 22,
  },
  classInfo: {
    flex: 1,
  },
  className: {
    fontSize: 15,
    fontWeight: '800',
    color: '#fff',
    marginBottom: 2,
  },
  classMeta: {
    fontSize: 12,
    color: '#64748b',
  },
  classArrow: {
    fontSize: 18,
    color: '#475569',
  },
  emptyState: {
    backgroundColor: '#0f0f1a',
    borderRadius: 12,
    padding: 32,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#1e1e3f',
  },
  emptyEmoji: {
    fontSize: 40,
    marginBottom: 12,
  },
  emptyText: {
    fontSize: 14,
    color: '#64748b',
    marginBottom: 16,
  },
  bookButton: {
    backgroundColor: '#6366f1',
    borderRadius: 10,
    paddingHorizontal: 24,
    paddingVertical: 12,
  },
  bookButtonText: {
    color: '#fff',
    fontWeight: '800',
    fontSize: 14,
  },
  quickActions: {
    flexDirection: 'row',
    gap: 10,
  },
  quickAction: {
    flex: 1,
    backgroundColor: '#0f0f1a',
    borderRadius: 14,
    padding: 16,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#1e1e3f',
  },
  quickActionIcon: {
    fontSize: 28,
    marginBottom: 8,
  },
  quickActionLabel: {
    fontSize: 12,
    fontWeight: '700',
    color: '#94a3b8',
  },
});

// ============================================================
// FILE: apps/mobile/src/screens/BookingScreen.tsx
// Class Booking Screen
// ============================================================

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  ActivityIndicator,
} from 'react-native';
import { api } from '../api/client';
import { useAuth } from '../contexts/AuthContext';

interface AvailableClass {
  id: string;
  class_type: { name: string; color: string; icon: string };
  class_date: string;
  start_time: string;
  end_time: string;
  room: string;
  coach: { first_name: string };
  spots_remaining: number;
  is_ai_recommended: boolean;
  recommendation_reason?: string;
}

export default function BookingScreen() {
  const { token } = useAuth();
  const [classes, setClasses] = useState<AvailableClass[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedDate, setSelectedDate] = useState(new Date());
  const [bookingInProgress, setBookingInProgress] = useState<string | null>(null);

  const dates = Array.from({ length: 7 }, (_, i) => {
    const d = new Date();
    d.setDate(d.getDate() + i);
    return d;
  });

  async function loadClasses(date: Date) {
    setLoading(true);
    try {
      const response = await api.get('/member/classes/available', {
        headers: { Authorization: `Bearer ${token}` },
        params: { date: date.toISOString().split('T')[0] },
      });
      setClasses(response.data.classes || []);
    } catch (err) {
      console.error('Failed to load classes:', err);
    } finally {
      setLoading(false);
    }
  }

  async function bookClass(classId: string) {
    setBookingInProgress(classId);
    try {
      await api.post('/member/bookings', 
        { class_id: classId },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      // Refresh list
      loadClasses(selectedDate);
    } catch (err: any) {
      alert(err.response?.data?.message || 'Booking failed');
    } finally {
      setBookingInProgress(null);
    }
  }

  useEffect(() => {
    loadClasses(selectedDate);
  }, [selectedDate]);

  const formatDate = (date: Date) => {
    const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
    return {
      day: days[date.getDay()],
      date: date.getDate(),
      isToday: date.toDateString() === new Date().toDateString(),
    };
  };

  return (
    <View style={styles.container}>
      {/* Date Selector */}
      <View style={styles.dateSelector}>
        <FlatList
          horizontal
          showsHorizontalScrollIndicator={false}
          data={dates}
          keyExtractor={(item) => item.toISOString()}
          renderItem={({ item }) => {
            const formatted = formatDate(item);
            const isSelected = item.toDateString() === selectedDate.toDateString();
            return (
              <TouchableOpacity
                style={[
                  styles.dateChip,
                  isSelected && styles.dateChipSelected,
                ]}
                onPress={() => setSelectedDate(item)}
              >
                <Text style={[styles.dateDay, isSelected && styles.dateTextSelected]}>
                  {formatted.day}
                </Text>
                <Text style={[styles.dateNum, isSelected && styles.dateTextSelected]}>
                  {formatted.date}
                </Text>
                {formatted.isToday && (
                  <View style={styles.todayDot} />
                )}
              </TouchableOpacity>
            );
          }}
          contentContainerStyle={styles.dateList}
        />
      </View>

      {/* Classes List */}
      {loading ? (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#6366f1" />
        </View>
      ) : (
        <FlatList
          data={classes}
          keyExtractor={(item) => item.id}
          contentContainerStyle={styles.listContent}
          ListEmptyComponent={
            <View style={styles.emptyContainer}>
              <Text style={styles.emptyEmoji}>📅</Text>
              <Text style={styles.emptyText}>No classes available</Text>
            </View>
          }
          renderItem={({ item }) => (
            <View style={styles.classCard}>
              <View style={styles.classHeader}>
                <View style={[styles.classIcon, { backgroundColor: item.class_type?.color || '#6366f1' }]}>
                  <Text style={styles.classIconText}>
                    {item.class_type?.icon === 'fire' ? '🔥' : 
                     item.class_type?.icon === 'yoga' ? '🧘' : 
                     item.class_type?.icon === 'bike' ? '🚴' : '🏋️'}
                  </Text>
                </View>
                <View style={styles.classInfo}>
                  <Text style={styles.className}>{item.class_type?.name}</Text>
                  <Text style={styles.classMeta}>
                    {item.start_time} • {item.room} • {item.coach?.first_name}
                  </Text>
                  {item.is_ai_recommended && (
                    <View style={styles.aiBadge}>
                      <Text style={styles.aiBadgeText}>✨ AI Recommended</Text>
                    </View>
                  )}
                </View>
              </View>

              <View style={styles.classFooter}>
                <View style={styles.spotsContainer}>
                  <Text style={[
                    styles.spotsText,
                    item.spots_remaining <= 3 && styles.spotsLow,
                  ]}>
                    {item.spots_remaining} spots left
                  </Text>
                </View>
                <TouchableOpacity
                  style={[
                    styles.bookButton,
                    item.spots_remaining === 0 && styles.bookButtonDisabled,
                    bookingInProgress === item.id && styles.bookButtonLoading,
                  ]}
                  onPress={() => bookClass(item.id)}
                  disabled={item.spots_remaining === 0 || bookingInProgress === item.id}
                >
                  {bookingInProgress === item.id ? (
                    <ActivityIndicator size="small" color="#fff" />
                  ) : (
                    <Text style={styles.bookButtonText}>
                      {item.spots_remaining === 0 ? 'Full' : 'Book'}
                    </Text>
                  )}
                </TouchableOpacity>
              </View>
            </View>
          )}
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0a0a14',
  },
  dateSelector: {
    paddingTop: 60,
    paddingBottom: 16,
    backgroundColor: '#0a0a14',
    borderBottomWidth: 1,
    borderBottomColor: '#1e1e3f',
  },
  dateList: {
    paddingHorizontal: 16,
    gap: 8,
  },
  dateChip: {
    width: 56,
    height: 70,
    borderRadius: 14,
    backgroundColor: '#1e1e3f',
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#2d2d44',
    marginRight: 8,
  },
  dateChipSelected: {
    backgroundColor: '#6366f1',
    borderColor: '#6366f1',
  },
  dateDay: {
    fontSize: 12,
    color: '#94a3b8',
    fontWeight: '600',
    textTransform: 'uppercase',
  },
  dateNum: {
    fontSize: 20,
    color: '#fff',
    fontWeight: '900',
    marginTop: 4,
  },
  dateTextSelected: {
    color: '#fff',
  },
  todayDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: '#10b981',
    marginTop: 4,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  listContent: {
    padding: 16,
    paddingBottom: 32,
  },
  classCard: {
    backgroundColor: '#1e1e3f',
    borderRadius: 16,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#2d2d44',
  },
  classHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 14,
  },
  classIcon: {
    width: 50,
    height: 50,
    borderRadius: 14,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 14,
  },
  classIconText: {
    fontSize: 24,
  },
  classInfo: {
    flex: 1,
  },
  className: {
    fontSize: 16,
    fontWeight: '800',
    color: '#fff',
    marginBottom: 4,
  },
  classMeta: {
    fontSize: 13,
    color: '#64748b',
    marginBottom: 6,
  },
  aiBadge: {
    backgroundColor: 'rgba(139, 92, 246, 0.15)',
    borderRadius: 6,
    paddingHorizontal: 8,
    paddingVertical: 3,
    alignSelf: 'flex-start',
  },
  aiBadgeText: {
    fontSize: 10,
    color: '#a78bfa',
    fontWeight: '700',
  },
  classFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    borderTopWidth: 1,
    borderTopColor: '#2d2d44',
    paddingTop: 14,
  },
  spotsContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  spotsText: {
    fontSize: 13,
    color: '#34d399',
    fontWeight: '700',
  },
  spotsLow: {
    color: '#f87171',
  },
  bookButton: {
    backgroundColor: '#10b981',
    borderRadius: 10,
    paddingHorizontal: 24,
    paddingVertical: 10,
  },
  bookButtonDisabled: {
    backgroundColor: '#2d2d44',
  },
  bookButtonLoading: {
    backgroundColor: '#059669',
  },
  bookButtonText: {
    color: '#fff',
    fontWeight: '800',
    fontSize: 14,
  },
  emptyContainer: {
    alignItems: 'center',
    paddingTop: 60,
  },
  emptyEmoji: {
    fontSize: 48,
    marginBottom: 16,
  },
  emptyText: {
    fontSize: 16,
    color: '#64748b',
  },
});

// ============================================================
// FILE: apps/mobile/src/screens/CheckInScreen.tsx
// QR Check-In Screen
// ============================================================

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Vibration,
  Alert,
} from 'react-native';
import { CameraView, useCameraPermissions } from 'expo-camera';
import { api } from '../api/client';
import { useAuth } from '../contexts/AuthContext';

export default function CheckInScreen() {
  const { token } = useAuth();
  const [permission, requestPermission] = useCameraPermissions();
  const [scanned, setScanned] = useState(false);
  const [checkInResult, setCheckInResult] = useState<any>(null);

  async function handleBarCodeScanned({ data }: { data: string }) {
    if (scanned) return;
    setScanned(true);
    Vibration.vibrate(200);

    try {
      const response = await api.post('/member/check-in', 
        { location: data },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setCheckInResult(response.data);

      if (response.data.milestone_reached) {
        Alert.alert(
          '🎉 Milestone Reached!',
          response.data.milestone_message || `You've hit ${response.data.total_visits} visits!`,
          [{ text: 'Awesome!', onPress: () => setScanned(false) }]
        );
      } else {
        setTimeout(() => setScanned(false), 3000);
      }
    } catch (err: any) {
      Alert.alert('Check-In Failed', err.response?.data?.message || 'Please try again');
      setScanned(false);
    }
  }

  if (!permission) {
    return (
      <View style={styles.container}>
        <ActivityIndicator size="large" color="#6366f1" />
      </View>
    );
  }

  if (!permission.granted) {
    return (
      <View style={styles.container}>
        <Text style={styles.permissionText}>Camera access needed for check-in</Text>
        <TouchableOpacity style={styles.permissionButton} onPress={requestPermission}>
          <Text style={styles.permissionButtonText}>Grant Access</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>📱 Check In</Text>
        <Text style={styles.subtitle}>Scan the QR code at the entrance</Text>
      </View>

      {checkInResult ? (
        <View style={styles.resultContainer}>
          <Text style={styles.resultEmoji}>✅</Text>
          <Text style={styles.resultTitle}>Checked In!</Text>
          <Text style={styles.resultDetail}>
            Visit streak: {checkInResult.visit_streak} 🔥
          </Text>
          <Text style={styles.resultDetail}>
            Total visits: {checkInResult.total_visits}
          </Text>
        </View>
      ) : (
        <View style={styles.cameraContainer}>
          <CameraView
            style={styles.camera}
            facing="back"
            barcodeScannerSettings={{
              barcodeTypes: ['qr'],
            }}
            onBarcodeScanned={scanned ? undefined : handleBarCodeScanned}
          >
            <View style={styles.overlay}>
              <View style={styles.scanFrame}>
                <View style={[styles.corner, styles.cornerTL]} />
                <View style={[styles.corner, styles.cornerTR]} />
                <View style={[styles.corner, styles.cornerBL]} />
                <View style={[styles.corner, styles.cornerBR]} />
              </View>
              <Text style={styles.scanText}>Align QR code within frame</Text>
            </View>
          </CameraView>
        </View>
      )}

      <TouchableOpacity
        style={styles.manualButton}
        onPress={() => { /* Manual check-in fallback */ }}
      >
        <Text style={styles.manualButtonText}>Can't scan? Check in manually</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0a0a14',
    paddingTop: 60,
  },
  header: {
    alignItems: 'center',
    marginBottom: 24,
    paddingHorizontal: 24,
  },
  title: {
    fontSize: 24,
    fontWeight: '900',
    color: '#fff',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 14,
    color: '#94a3b8',
  },
  cameraContainer: {
    flex: 1,
    marginHorizontal: 24,
    borderRadius: 24,
    overflow: 'hidden',
    borderWidth: 2,
    borderColor: '#2d2d44',
  },
  camera: {
    flex: 1,
  },
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.3)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  scanFrame: {
    width: 250,
    height: 250,
    position: 'relative',
  },
  corner: {
    position: 'absolute',
    width: 40,
    height: 40,
    borderColor: '#6366f1',
    borderWidth: 4,
  },
  cornerTL: {
    top: 0,
    left: 0,
    borderBottomWidth: 0,
    borderRightWidth: 0,
  },
  cornerTR: {
    top: 0,
    right: 0,
    borderBottomWidth: 0,
    borderLeftWidth: 0,
  },
  cornerBL: {
    bottom: 0,
    left: 0,
    borderTopWidth: 0,
    borderRightWidth: 0,
  },
  cornerBR: {
    bottom: 0,
    right: 0,
    borderTopWidth: 0,
    borderLeftWidth: 0,
  },
  scanText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
    marginTop: 20,
  },
  resultContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    marginHorizontal: 24,
    backgroundColor: '#1e1e3f',
    borderRadius: 24,
    borderWidth: 1,
    borderColor: '#2d2d44',
  },
  resultEmoji: {
    fontSize: 64,
    marginBottom: 16,
  },
  resultTitle: {
    fontSize: 24,
    fontWeight: '900',
    color: '#10b981',
    marginBottom: 12,
  },
  resultDetail: {
    fontSize: 16,
    color: '#94a3b8',
    marginBottom: 8,
  },
  manualButton: {
    marginHorizontal: 24,
    marginVertical: 24,
    padding: 16,
    alignItems: 'center',
  },
  manualButtonText: {
    color: '#6366f1',
    fontSize: 14,
    fontWeight: '700',
  },
  permissionText: {
    color: '#94a3b8',
    fontSize: 16,
    textAlign: 'center',
    marginBottom: 20,
  },
  permissionButton: {
    backgroundColor: '#6366f1',
    borderRadius: 12,
    paddingHorizontal: 32,
    paddingVertical: 14,
  },
  permissionButtonText: {
    color: '#fff',
    fontWeight: '800',
    fontSize: 16,
  },
});

// ============================================================
// FILE: apps/mobile/src/api/client.ts
// API Client with Auth
// ============================================================

import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';

const API_BASE_URL = 'https://api.fitmind.ai/v3';
// const API_BASE_URL = 'http://localhost:8000/v3'; // For local dev

export const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  async (config) => {
    const token = await AsyncStorage.getItem('fitmind_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Token expired, logout
      await AsyncStorage.removeItem('fitmind_token');
      // Trigger logout in auth context
    }
    return Promise.reject(error);
  }
);

// ============================================================
// FILE: apps/mobile/src/contexts/AuthContext.tsx
// Authentication Context
// ============================================================

import React, { createContext, useContext, useState, useEffect } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { api } from '../api/client';

interface AuthContextType {
  isAuthenticated: boolean;
  token: string | null;
  user: any | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType>({
  isAuthenticated: false,
  token: null,
  user: null,
  login: async () => {},
  logout: async () => {},
});

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadToken();
  }, []);

  async function loadToken() {
    try {
      const storedToken = await AsyncStorage.getItem('fitmind_token');
      if (storedToken) {
        setToken(storedToken);
        // Validate token and get user info
        const response = await api.get('/member/me', {
          headers: { Authorization: `Bearer ${storedToken}` },
        });
        setUser(response.data);
      }
    } catch (err) {
      console.error('Failed to load auth state:', err);
    } finally {
      setLoading(false);
    }
  }

  async function login(email: string, password: string) {
    const response = await api.post('/auth/member-login', {
      email,
      password,
    });

    const { token: newToken, member } = response.data;
    await AsyncStorage.setItem('fitmind_token', newToken);
    setToken(newToken);
    setUser(member);
  }

  async function logout() {
    await AsyncStorage.removeItem('fitmind_token');
    setToken(null);
    setUser(null);
  }

  if (loading) {
    return null; // Or loading screen
  }

  return (
    <AuthContext.Provider
      value={{
        isAuthenticated: !!token,
        token,
        user,
        login,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);

// ============================================================
// FILE: apps/mobile/package.json
// ============================================================
"""
{
  "name": "@fitmind/mobile",
  "version": "3.0.0",
  "main": "expo/AppEntry.js",
  "scripts": {
    "start": "expo start",
    "android": "expo start --android",
    "ios": "expo start --ios",
    "web": "expo start --web",
    "build:android": "eas build --platform android",
    "build:ios": "eas build --platform ios"
  },
  "dependencies": {
    "expo": "~51.0.0",
    "expo-status-bar": "~1.12.0",
    "expo-camera": "~15.0.0",
    "expo-secure-store": "~13.0.0",
    "react": "18.2.0",
    "react-native": "0.74.0",
    "@react-navigation/native": "^6.1.0",
    "@react-navigation/native-stack": "^6.9.0",
    "@react-navigation/bottom-tabs": "^6.5.0",
    "react-native-screens": "~3.31.0",
    "react-native-safe-area-context": "~4.10.0",
    "react-native-gesture-handler": "~2.16.0",
    "axios": "^1.7.0",
    "@react-native-async-storage/async-storage": "~1.23.0"
  },
  "devDependencies": {
    "@babel/core": "^7.24.0",
    "@types/react": "~18.2.0",
    "typescript": "^5.4.0"
  }
}
"""
