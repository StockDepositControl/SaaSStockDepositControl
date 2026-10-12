import React, { useEffect, useState, useCallback } from 'react';
import {
  View,
  Text,
  Pressable,
  ScrollView,
  StyleSheet,
  RefreshControl,
} from 'react-native';
import { useAuth } from '../context/AuthContext';
import { useMobileDataClient } from '../context/DataContext';
import { ProgressBar } from '../components/ui/ProgressBar';
import { Icon } from '../components/ui/Icon';
import { formatSpanishFullDate } from '../utils/formatters';
import { extractFirstName } from '../utils/jwtDecoder';
import { colors } from '../utils/designTokens';
import { AuditDailyProgress } from '../types/audit';

interface DashboardScreenProps {
  onNavigateToAudit: () => void;
  onNavigateToCatalog: () => void;
}

export const DashboardScreen: React.FC<DashboardScreenProps> = ({
  onNavigateToAudit,
  onNavigateToCatalog,
}) => {
  const { session } = useAuth();
  const client = useMobileDataClient();
  const [progress, setProgress] = useState<AuditDailyProgress>({
    auditedCount: 0,
    totalCount: 0,
    pendingCount: 0,
    percentage: 0,
  });
  const [isRefreshing, setIsRefreshing] = useState(false);

  const loadProgress = useCallback(async () => {
    try {
      const data = await client.getDailyProgress();
      setProgress(data);
    } catch {
      // Ignore load error
    }
  }, [client]);

  useEffect(() => {
    loadProgress();
  }, [loadProgress]);

  const onRefresh = async () => {
    setIsRefreshing(true);
    await loadProgress();
    setIsRefreshing(false);
  };

  const firstName = extractFirstName(session?.displayName || 'Luis');
  const currentDateStr = formatSpanishFullDate();

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.scrollContent}
      refreshControl={
        <RefreshControl refreshing={isRefreshing} onRefresh={onRefresh} />
      }
    >
      {/* Greeting Header */}
      <View style={styles.header}>
        <Text style={styles.greetingTitle}>¡Hola, {firstName}! 👋</Text>
        <Text style={styles.greetingDate}>{currentDateStr}</Text>
      </View>

      {/* Progress Section */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>PROGRESO DE AUDITORÍA</Text>
        <View style={styles.progressCard}>
          {/* Top Counter Row */}
          <View style={styles.progressTopRow}>
            <View style={styles.counterBox}>
              <Text style={styles.auditedNumber}>{progress.auditedCount}</Text>
              <Text style={styles.totalNumber}> / {progress.totalCount}</Text>
            </View>
            <Text
              style={[
                styles.percentageText,
                progress.percentage >= 100
                  ? styles.percentageCompleted
                  : styles.percentagePending,
              ]}
            >
              {progress.percentage}%
            </Text>
          </View>

          <Text style={styles.progressSubtitle}>artículos auditados hoy</Text>

          {/* Progress Bar */}
          <ProgressBar
            progress={progress.percentage}
            color={colors.primary[500]}
            height={8}
          />

          {/* Pending Counter Footer */}
          <Text style={styles.pendingText}>
            {progress.pendingCount} artículos pendientes
          </Text>
        </View>
      </View>

      {/* Quick Access Section */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>ACCESO RÁPIDO</Text>

        {/* Card 1: Auditar artículo */}
        <Pressable
          onPress={onNavigateToAudit}
          style={({ pressed }) => [
            styles.actionCard,
            pressed && styles.actionCardPressed,
          ]}
        >
          <View style={[styles.actionIconBox, { backgroundColor: '#FFFBEB' }]}>
            <Icon name="clipboard-check" size={24} color="#D97706" />
          </View>
          <View style={styles.actionTextBox}>
            <Text style={styles.actionTitle}>Auditar artículo</Text>
            <Text style={styles.actionSubtitle}>
              Buscá un artículo por código o nombre y registrá su auditoría.
            </Text>
          </View>
          <Icon name="arrow-right" size={18} color="#CBD5E1" />
        </Pressable>

        {/* Card 2: Ver catálogo */}
        <Pressable
          onPress={onNavigateToCatalog}
          style={({ pressed }) => [
            styles.actionCard,
            pressed && styles.actionCardPressed,
          ]}
        >
          <View style={[styles.actionIconBox, { backgroundColor: '#FEF3C7' }]}>
            <Icon name="package" size={24} color="#B45309" />
          </View>
          <View style={styles.actionTextBox}>
            <Text style={styles.actionTitle}>Ver catálogo</Text>
            <Text style={styles.actionSubtitle}>
              Consultá el catálogo completo con stock y estado de cada ítem.
            </Text>
          </View>
          <Icon name="arrow-right" size={18} color="#CBD5E1" />
        </Pressable>
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background.base,
  },
  scrollContent: {
    padding: 16,
    paddingBottom: 32,
  },
  header: {
    marginBottom: 20,
    marginTop: 8,
  },
  greetingTitle: {
    fontSize: 24,
    fontWeight: '800',
    color: colors.text.primary,
    letterSpacing: -0.5,
  },
  greetingDate: {
    fontSize: 14,
    fontWeight: '500',
    color: colors.text.muted,
    marginTop: 2,
  },
  section: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 11,
    fontWeight: '700',
    color: colors.text.muted,
    letterSpacing: 0.8,
    textTransform: 'uppercase',
    marginBottom: 10,
  },
  progressCard: {
    backgroundColor: colors.background.surface,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: colors.background.surfaceMuted,
    padding: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.04,
    shadowRadius: 4,
    elevation: 1,
  },
  progressTopRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'baseline',
  },
  counterBox: {
    flexDirection: 'row',
    alignItems: 'baseline',
  },
  auditedNumber: {
    fontSize: 32,
    fontWeight: '800',
    color: colors.text.primary,
  },
  totalNumber: {
    fontSize: 16,
    fontWeight: '500',
    color: colors.text.muted,
  },
  percentageText: {
    fontSize: 22,
    fontWeight: '800',
  },
  percentagePending: {
    color: '#D97706',
  },
  percentageCompleted: {
    color: '#059669',
  },
  progressSubtitle: {
    fontSize: 12,
    color: colors.text.muted,
    marginTop: 2,
    marginBottom: 14,
  },
  pendingText: {
    fontSize: 12,
    fontWeight: '500',
    color: colors.text.muted,
    marginTop: 12,
  },
  actionCard: {
    backgroundColor: colors.background.surface,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: colors.background.surfaceMuted,
    padding: 16,
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
    minHeight: 48,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.04,
    shadowRadius: 4,
    elevation: 1,
  },
  actionCardPressed: {
    backgroundColor: '#F1F5F9',
  },
  actionIconBox: {
    width: 44,
    height: 44,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 14,
  },
  actionTextBox: {
    flex: 1,
    paddingRight: 8,
  },
  actionTitle: {
    fontSize: 15,
    fontWeight: '700',
    color: colors.text.primary,
  },
  actionSubtitle: {
    fontSize: 12,
    color: colors.text.muted,
    marginTop: 2,
    lineHeight: 16,
  },
});
