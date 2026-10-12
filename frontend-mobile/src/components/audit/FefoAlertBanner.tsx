import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Icon } from '../ui/Icon';
import { FefoEvaluator } from '../../services/domain/FefoEvaluator';

interface FefoAlertBannerProps {
  expirationDate?: string | null;
}

export const FefoAlertBanner: React.FC<FefoAlertBannerProps> = ({ expirationDate }) => {
  const evalResult = FefoEvaluator.evaluate(expirationDate);

  if (evalResult.severity === 'NONE' || evalResult.severity === 'SAFE') {
    return null;
  }

  const isExpired = evalResult.severity === 'EXPIRED';
  const tagLabel = isExpired ? 'VENCIDO' : 'PRÓXIMO';

  return (
    <View style={styles.container}>
      <View style={styles.iconBox}>
        <Icon name="calendar" size={16} color="#DC2626" />
      </View>
      <View style={styles.textBox}>
        <Text style={styles.alertTitle}>Vencimiento más próximo</Text>
        <Text style={styles.alertSubtitle}>
          (FEFO): {evalResult.formattedDate}
        </Text>
      </View>
      <View style={styles.tagBox}>
        <Text style={styles.tagText}>{tagLabel}</Text>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#FEF2F2',
    borderWidth: 1,
    borderColor: '#DC2626',
    borderRadius: 12,
    paddingHorizontal: 12,
    paddingVertical: 10,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginTop: 12,
  },
  iconBox: {
    marginRight: 8,
  },
  textBox: {
    flex: 1,
  },
  alertTitle: {
    fontSize: 11,
    fontWeight: '700',
    color: '#B91C1C',
  },
  alertSubtitle: {
    fontSize: 11,
    fontWeight: '700',
    color: '#B91C1C',
  },
  tagBox: {
    backgroundColor: 'rgba(220, 38, 38, 0.1)',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
  },
  tagText: {
    fontSize: 10,
    fontWeight: '800',
    color: '#B91C1C',
    letterSpacing: 0.5,
  },
});
